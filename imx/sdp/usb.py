# Copyright (c) 2017-2018 Martin Olejar
#
# SPDX-License-Identifier: BSD-3-Clause
# The BSD-3-Clause license for this file can be found in the LICENSE file included with this distribution
# or at https://spdx.org/licenses/BSD-3-Clause.html#licenseText

import os
import logging
import threading
import collections
from time import time

from .misc import atos

#os.environ['PYUSB_DEBUG'] = 'debug'
#os.environ['PYUSB_LOG_FILENAME'] = 'usb.log'


########################################################################################################################
# USB Interface Base Class
########################################################################################################################

class RawHidBase(object):

    @property
    def info(self):
        return "{0:s} (0x{1:04X}, 0x{2:04X})".format(self.product_name, self.vid, self.pid)

    def __init__(self):
        self.vid = 0
        self.pid = 0
        self.vendor_name = ""
        self.product_name = ""

    @staticmethod
    def _encode_packet(report_id, data, pkglen):
        buf = bytes([report_id])                   # Set Report ID (byte 0)
        buf += data                                # Set data
        buf += bytes([0x00]*(pkglen - len(data)))  # Align packet to pkglen
        return buf

    @staticmethod
    def _decode_packet(data):
        report_id = data[0]                        # Get USB-HID Report ID
        return report_id, data[1:]

    def open(self):
        raise NotImplementedError()

    def close(self):
        raise NotImplementedError()

    def write(self, id, data, size):
        raise NotImplementedError()

    def read(self, timeout):
        raise NotImplementedError()


########################################################################################################################
# USB Interface Classes
########################################################################################################################

if os.name == "nt":
    try:
        import pywinusb.hid as hid
    except:
        raise Exception("PyWinUSB is required on a Windows Machine")


    class RawHid(RawHidBase):
        """
        This class provides basic functions to access
        a USB HID device using pywinusb:
            - write/read an endpoint
        """
        def __init__(self):
            super().__init__()
            # Vendor page and usage_id = 2
            self.report = []
            # deque used here instead of synchronized Queue
            # since read speeds are ~10-30% faster and are
            # comparable to a based list implementation.
            self.rcv_data = collections.deque()
            self.device = None
            return

        # handler called when a report is received
        def __rx_handler(self, data):
            # logging.debug("rcv: %s", data[1:])
            self.rcv_data.append(data)

        def open(self):
            """ open the interface """
            logging.debug("Opening USB interface")
            self.device.set_raw_data_handler(self.__rx_handler)
            self.device.open(shared=False)

        def close(self):
            """ close the interface """
            logging.debug("Closing USB interface")
            self.device.close()

        def write(self, id, data, size):
            """
            write data on the OUT endpoint associated to the HID interface
            """
            rawdata = self._encode_packet(id, data, size)
            logging.debug('USB-OUT[0x]: %s', atos(rawdata))
            self.report[id - 1].send(rawdata)

        def read(self, timeout=2000):
            """
            Read data on the IN endpoint associated to the HID interface
            :param timeout:
            """
            start = time()
            while len(self.rcv_data) == 0:
                if ((time() - start) * 1000) > timeout:
                    raise Exception("Read timed out")
            rawdata = self.rcv_data.popleft()
            logging.debug('USB-IN [0x]: %s', atos(rawdata))
            return self._decode_packet(bytes(rawdata))

        @staticmethod
        def enumerate(vid=None, pid=None):
            """
            returns all the connected devices which matches PyWinUSB.vid/PyWinUSB.pid.
            returns an array of PyWinUSB (Interface) objects
            :param vid:
            :param pid:
            """
            all_hid_devices = hid.find_all_hid_devices()

            # find devices with good vid/pid
            all_imx_devices = []
            for hid_dev in all_hid_devices:
                if hid_dev.vendor_id == vid or \
                   hid_dev.product_id == pid or \
                   'Freescale' in hid_dev.vendor_name or \
                   'NXP' in hid_dev.vendor_name.upper():
                    all_imx_devices.append(hid_dev)

            targets = []
            for dev in all_imx_devices:
                try:
                    dev.open(shared=False)
                    report = dev.find_output_reports()
                    dev.close()

                    if report:
                        new_target = RawHid()
                        new_target.report = report
                        new_target.vendor_name = dev.vendor_name.strip()
                        new_target.product_name = dev.product_name.strip()
                        new_target.vid = dev.vendor_id
                        new_target.pid = dev.product_id
                        new_target.device = dev
                        new_target.device.set_raw_data_handler(new_target.__rx_handler)
                        targets.append(new_target)
                except Exception as e:
                    logging.error("Receiving Exception: %s", e)
                    dev.close()

            return targets


elif os.name == "posix":
    try:
        import usb.core
        import usb.util
    except:
        raise Exception("PyUSB is required on a Linux Machine")

    class RawHid(RawHidBase):
        """
        This class provides basic functions to access
        a USB HID device using pyusb:
            - write/read an endpoint
        """

        vid = 0
        pid = 0
        interface_number = 0

        def __init__(self):
            super().__init__()
            self.dev = None
            self.closed = False

        def open(self):
            """ open the interface """
            logging.debug("Opening USB interface")

        def close(self):
            """ close the interface """
            logging.debug("Close USB Interface")
            self.closed = True
            try:
                if self.dev: usb.util.dispose_resources(self.dev)
            except:
                pass

        def write(self, id, data, size):
            """ write data on the OUT endpoint associated to the HID interface
            :param id: report ID
            :param data: report data in bytes
            :param size: report size
            """
            rawdata = self._encode_packet(id, data, size)
            logging.debug('USB-OUT[0x]: %s', atos(rawdata))

            bmRequestType = 0x21       # Host to device request of type Class of Recipient Interface
            bmRequest = 0x09           # Set_REPORT (HID class-specific request for transferring data over EP0)
            wValue = 0x200             # Issuing an OUT report
            wIndex = self.interface_number  # Interface number for HID
            self.dev.ctrl_transfer(bmRequestType, bmRequest, wValue + id, wIndex, rawdata)

        def read(self, timeout=1000):
            """ read data on the IN endpoint associated to the HID interface
            :param timeout: wait time in ms
            :return Tuple [report_id, data]
            """
            rawdata = self.dev.read(1 | 0x80, 1024, timeout)
            logging.debug('USB-IN [0x]: %s', atos(rawdata))
            return self._decode_packet(rawdata)

        @staticmethod
        def enumerate(vid=None, pid=None):

            def is_hid_device(device):
                if device.bDeviceClass != 0:
                    return False
                for cfg in device:
                    if cfg.bNumInterfaces == 1 and usb.util.find_descriptor(cfg, bInterfaceClass=3) is not None:
                        return True

            devices = []

            if vid is None or pid is None:
                all_hid_devices = usb.core.find(find_all=True, custom_match=is_hid_device)
            else:
                all_hid_devices = usb.core.find(find_all=True, idVendor=vid, idProduct=pid)

            # iterate on all devices found
            for dev in all_hid_devices:

                try:
                    if dev.is_kernel_driver_active(0):
                        dev.detach_kernel_driver(0)
                except Exception as e:
                    logging.warning(str(e))
                    continue

                try:
                    dev.set_configuration()
                    dev.reset()
                except usb.core.USBError as e:
                    logging.warning("Cannot set configuration the device: %s" % str(e))
                    continue

                new_device = RawHid()
                new_device.dev = dev
                new_device.vid = dev.idVendor
                new_device.pid = dev.idProduct
                new_device.vendor_name = usb.util.get_string(dev, 1).strip('\0')
                new_device.product_name = usb.util.get_string(dev, 2).strip('\0')
                new_device.interface_number = 0
                devices.append(new_device)

            return devices

else:
    raise Exception("No USB backend found")
