# Copyright (c) 2017 Martin Olejar, martin.olejar@gmail.com
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
# Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import os
import logging
import threading
import collections
from time import time

from .misc import atos

#os.environ['PYUSB_DEBUG'] = 'debug'
#os.environ['PYUSB_LOG_FILENAME'] = 'usb.log'


########################################################################################################################
## USB Interface Base Class
########################################################################################################################


class USBIF_BASE(object):

    def __init__(self):
        self.vid = 0
        self.pid = 0
        self.vendor_name = ""
        self.product_name = ""

    def _encode_packet(self, report_id, data, pkglen):
        buf = bytearray([report_id])                   # Set Report ID (byte 0)
        buf.extend(data)                               # Set data
        buf.extend([0x00]*(pkglen - len(data)))        # Align packet to pkglen
        return buf

    def _decode_packet(self, data):
        report_id = data[0]                            # Get USB-HID Report ID
        return (report_id, bytearray(data[1:]))

    def open(self):
        raise NotImplementedError()

    def close(self):
        raise NotImplementedError()

    def getInfo(self):
        return "{0:s} (0x{1:04X}, 0x{2:04X})".format(self.product_name, self.vid, self.pid)

    def write(self, id, data, size):
        raise NotImplementedError()

    def read(self, timeout):
        raise NotImplementedError()


########################################################################################################################
## USB Interface Classes
########################################################################################################################

if os.name == "nt":
    try:
        import pywinusb.hid as hid
    except:
        raise Exception("PyWinUSB is required on a Windows Machine")


    class USBIF(USBIF_BASE):
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
            # comprable to a based list implmentation.
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
            return self._decode_packet(rawdata)

        @staticmethod
        def enumerate(vid, pid):
            """
            returns all the connected devices which matches PyWinUSB.vid/PyWinUSB.pid.
            returns an array of PyWinUSB (Interface) objects
            :param vid:
            :param pid:
            """
            all_devices = hid.find_all_hid_devices()

            # find devices with good vid/pid
            all_kboot_devices = []
            for d in all_devices:
                if (d.vendor_id == vid) and (d.product_id == pid):
                    all_kboot_devices.append(d)

            targets = []
            for dev in all_kboot_devices:
                try:
                    dev.open(shared=False)
                    report = dev.find_output_reports()
                    dev.close()

                    if report:
                        new_target = USBIF()
                        new_target.report = report
                        new_target.vendor_name = dev.vendor_name
                        new_target.product_name = dev.product_name
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

    class USBIF(USBIF_BASE):
        """
        This class provides basic functions to access
        a USB HID device using pyusb:
            - write/read an endpoint
        """

        vid = 0
        pid = 0
        intf_number = 0

        def __init__(self):
            super().__init__()
            self.ep_out = None
            self.ep_in = None
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
            """
            write data on the OUT endpoint associated to the HID interface
            """
            rawdata = self._encode_packet(id, data, size)
            logging.debug('USB-OUT[0x]: %s', atos(rawdata))

            if self.ep_out:
                self.ep_out.write(rawdata)
            else:
                bmRequestType = 0x21       #Host to device request of type Class of Recipient Interface
                bmRequest = 0x09           #Set_REPORT (HID class-specific request for transferring data over EP0)
                wValue = 0x201             #Issuing an OUT report
                wIndex = self.intf_number  #Interface number for HID
                self.dev.ctrl_transfer(bmRequestType, bmRequest, wValue, wIndex, rawdata)

        def read(self, timeout=1000):
            """
            read data on the IN endpoint associated to the HID interface
            """
            #rawdata = self.ep_in.read(self.ep_in.wMaxPacketSize, timeout)
            rawdata = self.ep_in.read(1024, timeout)
            logging.debug('USB-IN [0x]: %s', atos(rawdata))
            return self._decode_packet(rawdata)


        @staticmethod
        def enumerate(vid, pid):
            """
            returns all the connected devices which matches PyUSB.vid/PyUSB.pid.
            returns an array of PyUSB (Interface) objects
            :param vid:
            :param pid:
            """
            # find all devices matching the vid/pid specified
            all_devices = usb.core.find(find_all=True, idVendor=vid, idProduct=pid)

            if not all_devices:
                logging.debug("No device connected")
                return None

            targets = []

            # iterate on all devices found
            for dev in all_devices:
                interface_number = -1

                # get active config
                config = dev.get_active_configuration()

                # iterate on all interfaces:
                for interface in config:
                    if interface.bInterfaceClass == 0x03: # HID Interface
                        interface_number = interface.bInterfaceNumber
                        break

                if interface_number == -1:
                    continue

                try:
                    if dev.is_kernel_driver_active(interface_number):
                        dev.detach_kernel_driver(interface_number)
                except Exception as e:
                    print(str(e))

                try:
                    dev.set_configuration()
                    dev.reset()
                except usb.core.USBError as e:
                    print("Cannot set configuration the device: %s" % str(e))

                ep_in, ep_out = None, None
                for ep in interface:
                    if ep.bEndpointAddress & 0x80:
                        ep_in = ep
                    else:
                        ep_out = ep

                if usb.__version__ == '1.0.0b1':
                    product_name = usb.util.get_string(dev, 64, 2)
                    vendor_name = usb.util.get_string(dev, 64, 1)
                else:
                    vendor_name = usb.util.get_string(dev, 1)
                    product_name = usb.util.get_string(dev, 2)

                if not ep_in:
                    logging.error('Endpoints not found')
                    return None

                new_target = USBIF()
                new_target.ep_in = ep_in
                new_target.ep_out = ep_out
                new_target.dev = dev
                new_target.vid = vid
                new_target.pid = pid
                new_target.intf_number = interface_number
                new_target.vendor_name = vendor_name
                new_target.product_name = product_name
                targets.append(new_target)

            return targets

else:
    raise Exception("No USB backend found")


