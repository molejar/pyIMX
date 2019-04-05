# Copyright (c) 2017-2018 Martin Olejar
#
# SPDX-License-Identifier: BSD-3-Clause
# The BSD-3-Clause license for this file can be found in the LICENSE file included with this distribution
# or at https://spdx.org/licenses/BSD-3-Clause.html#licenseText

import sys
import struct
import logging

from .usb import RawHid
from .misc import atos
from ..hab import status_info


########################################################################################################################
# Serial Downloader Protocol (SDP) Exceptions
########################################################################################################################

class SdpGenericError(Exception):
    """ Base Exception class for Loader
    """
    fmt = 'i.MX Serial Downloader Error'   #: format string

    @property
    def error_value(self):
        return getattr(self, "errval")

    def __init__(self, msg=None, **kw):
        """ Initialize the Exception with the given message. """
        self.msg = msg
        for key, value in kw.items():
            setattr(self, key, value)

    def __str__(self):
        """ Return the message in this Exception. """
        if self.msg:
            return self.msg
        try:
            return self.fmt % self.__dict__
        except (NameError, ValueError, KeyError):
            e = sys.exc_info()[1]     # current exception
            return 'Unprintable exception %s: %s' % (repr(e), str(e))


class SdpCommandError(SdpGenericError):
    fmt = 'Command operation break, error: 0x%(errval)08X'


class SdpDataError(SdpGenericError):
    fmt = 'Data %(mode)s break: %(errname)s'


class SdpConnectionError(SdpGenericError):
    fmt = 'USB connection error'


class SdpTimeoutError(SdpGenericError):
    fmt = 'USB timeout error'


class SdpSecureError(SdpGenericError):
    fmt = 'Target is locked !'


class SdpAbortError(SdpGenericError):
    fmt = 'Operation aborted !'


########################################################################################################################
# Serial Downloader Protocol (SDP) base Class
########################################################################################################################

class SdpBase(object):

    # iMX Serial Downloader USB HID Reports.
    HID_REPORT = {
        'CMD': {'ID': 0x01, 'LEN': 1024},
        'DAT': {'ID': 0x02, 'LEN': 1024},
        'SEC': {'ID': 0x03, 'LEN': 4},
        'RET': {'ID': 0x04, 'LEN': 64}
    }

    # Supported commands
    CMDS = {
        'READ':   {'ID': 0x0101},                     # Read memory or regs
        'WRITE':  {'ID': 0x0202, 'ACK': 0x128A8A12},  # Write one word (max 4 bytes) into memory or reg
        'WFILE':  {'ID': 0x0404, 'ACK': 0x88888888},  # Write file (img) into target memory
        'ERROR':  {'ID': 0x0505},                     # Read error state
        'WCSF':   {'ID': 0x0606, 'ACK': 0x128A8A12},  # Write CSF data into target
        'WDCD':   {'ID': 0x0A0A, 'ACK': 0x128A8A12},  # Write DCD data into target
        'JUMP':   {'ID': 0x0B0B, 'ACK': None},        # Jump to specified address and run
        'SKIPDCD':{'ID': 0x0C0C, 'ACK': 0x900DD009}   # Skip DCD content from loaded img (uboot.imx)
    }

    # Secure info flags
    SECNFO = {
        'OPEN': 0x56787856,
        'LOCK': 0x12343412
    }

    # Supported i.MX USB Devices
    DEVICES = {}

    def __init__(self, device):
        """ Constructor """
        assert isinstance(device, RawHid), "Not a \"RawHid\" instance !"

        self.usbd = device
        self.opened = False
        self.pg_handler = None
        self.pg_range = 100
        self.pg_resolution = 5

    @property
    def device_name(self):
        dev_name = None
        for name, val in self.DEVICES.items():
            if self.usbd.vid == val[0] and self.usbd.pid == val[1]:
                dev_name = name
                break

        return dev_name

    def open(self, handler=None):
        """ Connect i.MX device """
        if not self.opened:
            logging.info('Connect: %s', self.usbd.info)
            self.usbd.open()
            self.opened = True
            self.pg_handler = handler

    def close(self):
        """ Disconnect i.MX device """
        self.opened = False
        self.usbd.close()

    def _send_cmd(self, name, addr=0, format=0, count=0, value=0):
        """IMX SD: Send Command
        :param name: Command name
        :param addr: Address
        :param format:
        :param count:
        :param value:
        """
        if not self.opened or self.usbd is None:
            logging.info('RX-CMD: USB Disconnected')
            raise SdpConnectionError('USB Disconnected !')
        # Assembly Command
        buf = struct.pack('>HIBII', self.CMDS[name]['ID'], addr, format, count, value)
        # Send it to USB
        self.usbd.write(self.HID_REPORT['CMD']['ID'], buf, self.HID_REPORT['CMD']['LEN'])
        # Write into log
        logging.debug('TX-CMD [0x]: %s', atos(buf))

    def _check_secinfo(self, timeout=1000, wait=True):
        """ Check secure info of connected i.MX device
        :param timeout: waiting time in ms for rx data
        :param wait:
        """
        try:
            report_id, rx_data = self.usbd.read(timeout)
        except:
            if wait:
                logging.info('RX-CMD: Timeout Error >> USB Disconnected')
                raise SdpTimeoutError('Timeout >> USB Disconnected !')
            else:
                return None

        if report_id != self.HID_REPORT['SEC']['ID']:
            logging.info('RX-CMD: Wrong Report ID %d', report_id)
            raise SdpDataError('Wrong Report ID')

        tmp = struct.unpack_from("I", rx_data)
        if tmp[0] == self.SECNFO['LOCK']:
            logging.info('SECURE: Target is Locked !')
            raise SdpSecureError()

        logging.debug('SECURE: Not Enabled')

    def _get_status(self, timeout=1000, wait=True):
        """ Read status value
        :param timeout: waiting time in ms for rx data
        :param wait: If False, ignore timeout error
        """
        try:
            report_id, rx_data = self.usbd.read(timeout)
        except:
            if wait:
                logging.info('RX-CMD: Timeout Error >> USB Disconnected')
                raise SdpTimeoutError('Timeout >> USB Disconnected !')
            else:
                return None

        if report_id != self.HID_REPORT['RET']['ID']:
            logging.info('RX-CMD: Wrong Report ID %d', report_id)
            raise SdpDataError('Wrong Report ID')

        return struct.unpack_from("I", rx_data)[0]

    def _check_status(self, cmd, timeout=1000):
        """ Check command status
        :param cmd: command name
        :param timeout: waiting time in ms for rx data
        """
        if 'ACK' in self.CMDS[cmd]:
            status = self._get_status(timeout=timeout, wait=True if self.CMDS[cmd]['ACK'] else False)
            if status is not None and status != self.CMDS[cmd]['ACK']:
                logging.info('RX-CMD: ERROR: 0x%08X', status)
                raise SdpCommandError(status_info(status))
        logging.info('RX-CMD: OK')

    def _read_data(self, length, timeout=1000):
        """ Read data from target
        :param length: count of bytes
        :param timeout: waiting time in ms for rx data
        """
        n = 0
        data = bytearray()
        update = True
        while n < length:
            try:
                report_id, rx_data = self.usbd.read(timeout)
            except Exception as e:
                print(e)
                logging.info('RX-CMD: Timeout Error >> USB Disconnected')
                raise SdpTimeoutError('Timeout >> USB Disconnected !')
            # test for correct report
            if report_id != self.HID_REPORT['RET']['ID']:
                raise SdpDataError('Wrong Report ID')
            # add next packet
            data.extend(rx_data)
            n += len(rx_data)
            # ...
            if self.pg_handler is not None and (n % (self.HID_REPORT['DAT']['LEN'] * self.pg_resolution)) == 0:
                running = self.pg_handler(min(int((self.pg_range / length) * n), self.pg_range))
                update = False
                if not running:
                    raise SdpAbortError()

        # Align RX data to required length
        if n > length:
            data = data[:length]

        if self.pg_handler is not None and update:
            self.pg_handler(self.pg_range)

        return data

    def _send_data(self, data):
        """ Send data to target
        :param data: array with data to send
        """
        update = True
        report = self.HID_REPORT['DAT']
        length = len(data)
        offset = 0
        pkglen = report['LEN']
        while length > 0:
            if length < report['LEN']:
                pkglen = length
            try:
                self.usbd.write(report['ID'], data[offset:offset + pkglen], report['LEN'])
            except:
                logging.info('TX-CMD: Data Error >> USB Disconnected')
                raise SdpDataError('USB Disconnected')
            if self.pg_handler is not None and (offset % (report['LEN'] * self.pg_resolution)) == 0:
                running = self.pg_handler(min(int((self.pg_range / len(data)) * offset), self.pg_range))
                update = False
                if not running:
                    raise SdpAbortError()

            offset += pkglen
            length -= pkglen

        if self.pg_handler is not None and update:
            self.pg_handler(self.pg_range)

    def read(self, address, length, format=32):
        """ Read value from reg/mem at specified address
        :param address: Start address of first register
        :param length: Count of bytes
        :param format: Register access format 8, 16, 32 bites
        :return {list} read data
        """
        if (address % (format // 8)) > 0:
            raise Exception('Address <0x%08X> not aligned to %s bites' % (address, format))

        align = length % (format // 8)
        if align > 0:
            length += (format // 8) - align

        logging.info('TX-CMD: Read [ Addr=0x%08X | Len=%d | Format=%d ] ', address, length, format)
        self._send_cmd('READ', address, format, length)
        self._check_secinfo()
        ret_val = self._read_data(length, timeout=1000)
        logging.info('RX-CMD: %s', atos(ret_val))
        return ret_val

    def write(self, address, value, count=4, format=32):
        """ Write value into reg/mem at specified address
        :param address: Start address of first register
        :param value: Register value
        :param count: Count of bytes (max 4)
        :param format: Register access format 8, 16, 32 bites
        """
        # Check if start address value is aligned
        if (address % (format // 8)) > 0:
            raise Exception('Address <0x%08X> not aligned to %s bites' % (address, format))
        # Align count value if doesnt
        align = count % (format // 8)
        if align > 0:
            count += (format // 8) - align
        if count > 4:
            count = 4

        logging.info('TX-CMD: Write [ Addr=0x%08X | Val=0x%08X | Count=%d | Format=%d ] ', address, value, count, format)
        self._send_cmd('WRITE', address, format, count, value)
        self._check_secinfo()
        self._check_status('WRITE')

    def write_csf(self, address, data):
        """ Write CSF Data at specified address
        :param address: Start Address
        :param data: The CSF data in bytearray type
        """
        logging.info('TX-CMD: WriteCSF [ Addr=0x%08X | Len=%d ] ', address, len(data))
        self._send_cmd('WCSF', address, 0, len(data))
        self._send_data(data)
        self._check_secinfo()
        self._check_status('WCSF')

    def write_dcd(self, address, data):
        """ Write DCD values at specified address
        :param address: Start Address
        :param data: The DCD data in bytearray type
        """
        logging.info('TX-CMD: WriteDCD [ Addr=0x%08X | Len=%d ] ', address, len(data))
        self._send_cmd('WDCD', address, 0, len(data))
        self._send_data(data)
        self._check_secinfo()
        self._check_status('WDCD')

    def write_file(self, address, data):
        """ Write File/Data at specified address
        :param address: Start Address
        :param data: The img data in bytearray type
        """
        logging.info('TX-CMD: WriteFile [ Addr=0x%08X | Len=%d ] ', address, len(data))
        self._send_cmd('WFILE', address, 0, len(data))
        self._send_data(data)
        self._check_secinfo()
        self._check_status('WFILE')

    def skip_dcd(self):
        """ Skip DCD blob from loaded file """
        logging.info('TX-CMD: SkipDCD')
        self._send_cmd('SKIPDCD')
        self._check_secinfo()
        self._check_status('SKIPDCD')
        if self.pg_handler is not None:
            self.pg_handler(self.pg_range)

    def jump_and_run(self, address):
        """ Jump to specified address and run code
        :param address: Destination address
        """
        logging.info('TX-CMD: Jump To Address: 0x%08X', address)
        self._send_cmd('JUMP', address)
        self._check_secinfo()
        self._check_status('JUMP', timeout=100)
        if self.pg_handler is not None:
            self.pg_handler(self.pg_range)

    def read_status(self):
        """ Read Error Status
        :return status value
        """
        logging.info('TX-CMD: ReadStatus')
        self._send_cmd('ERROR')
        self._check_secinfo()
        status = self._get_status()
        if self.pg_handler is not None:
            self.pg_handler(self.pg_range)
        logging.info('RX-CMD: 0x%08X', status)
        return status

    def parse_status(self, status):
        raise NotImplementedError()

    def read_uid(self):
        raise NotImplementedError()


########################################################################################################################
# Serial Downloader Protocol Class: i.MX6, i.MX7 and Vybrid
########################################################################################################################

class SdpMX67(SdpBase):

    # Supported i.MX6, i.MX7 and Vybrid Devices
    DEVICES = {
        # NAME    | VID   | PID
        'MX6DQP': (0x15A2, 0x0054),
        'MX6SDL': (0x15A2, 0x0061),
        'MX6SL':  (0x15A2, 0x0063),
        'MX6SX':  (0x15A2, 0x0071),
        'MX6UL':  (0x15A2, 0x007D),
        'MX6ULL': (0x15A2, 0x0080),
        'MX6SLL': (0x15A2, 0x0128),
        'MX7SD':  (0x15A2, 0x0076),
        'MX7ULP': (0x1FC9, 0x0126),
        'VYBRID': (0x15A2, 0x006A),
    }

    def read_uid(self):
        pass


########################################################################################################################
# Serial Downloader Protocol Class: i.MX-RT
########################################################################################################################

class SdpMXRT(SdpBase):

    # Supported i.MXRT Devices
    DEVICES = {
        # NAME   | VID   | PID
        'MXRT':  (0x1FC9, 0x0130),
    }

    def write_csf(self, address, data):
        raise NotImplementedError()

    def skip_dcd(self):
        raise NotImplementedError()


########################################################################################################################
# Serial Downloader Protocol Class: i.MX8M
########################################################################################################################

class SdpMX8M(SdpBase):

    # Supported i.MX8 Devices
    DEVICES = {
        # NAME   | VID   | PID
        'MX8MQ':  (0x1FC9, 0x012B),
    }

    def write_csf(self, address, data):
        raise NotImplementedError()


########################################################################################################################
# Serial Downloader Protocol Class: i.MX8 rev. A0
########################################################################################################################

class SdpMX8A0(SdpBase):

    # Supported i.MX8 Devices
    DEVICES = {
        # NAME   | VID   | PID
        'MX8QXP-A0': (0x1FC9, 0x007D),
        'MX8QM-A0':  (0x1FC9, 0x0129)
    }

    def write_csf(self, address, data):
        raise NotImplementedError()


########################################################################################################################
# Serial Downloader Protocol Class: i.MX8 rev. B0 and upper
########################################################################################################################

class SdpMX8(SdpBase):

    # Supported i.MX8 Devices
    DEVICES = {
        # NAME   | VID   | PID
        'MX8QXP': (0x1FC9, 0x012F),
        'MX8QM':  (0x1FC9, 0x0129)
    }

    def read(self, address, length, format=32):
        raise NotImplementedError()

    def write(self, address, value, count=4, format=32):
        raise NotImplementedError()

    def write_csf(self, address, data):
        raise NotImplementedError()

    def skip_dcd(self):
        raise NotImplementedError()


########################################################################################################################
# General Variables
########################################################################################################################
SDP_CLS = (SdpMXRT, SdpMX67, SdpMX8M, SdpMX8A0, SdpMX8)


########################################################################################################################
# Helper functions
########################################################################################################################

def supported_devices():
    """
    :return list of supported devices names
    """
    names = []

    for sdc in SDP_CLS:
        names += sdc.DEVICES.keys()

    return names


def scan_usb(device_name=None):
    """ Scan for available USB devices
    :param device_name: The device name (MX6DQP, MX6SDL, ...) or USB device VID:PID value
    :rtype list
    """

    if device_name is None:
        objs = []
        devs = RawHid.enumerate()
        for cls in SDP_CLS:
            for dev in devs:
                for value in cls.DEVICES.values():
                    if dev.vid == value[0] and dev.pid == value[1]:
                        objs += [cls(dev)]
        return objs
    else:
        if ':' in device_name:
            vid, pid = device_name.split(':')
            devs = RawHid.enumerate(int(vid, 0), int(pid, 0))
            return [SdpBase(dev) for dev in devs]
        else:
            for cls in SDP_CLS:
                if device_name in cls.DEVICES:
                    vid = cls.DEVICES[device_name][0]
                    pid = cls.DEVICES[device_name][1]
                    devs = RawHid.enumerate(vid, pid)
                    return [cls(dev) for dev in devs]
    return []
