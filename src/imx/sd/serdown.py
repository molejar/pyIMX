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

import sys
import struct
import logging

from .usbif import USBIF
from .uartif import UARTIF
from .misc import atos


########################################################################################################################
## Serial Downloader Exceptions
########################################################################################################################


class SD_GenericError(Exception):
    """ Base Exception class for Loader
    """
    _fmt = 'IMX Serial Downloader Error'   #: format string

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
            return self._fmt % self.__dict__
        except (NameError, ValueError, KeyError):
            e = sys.exc_info()[1]     # current exception
            return 'Unprintable exception %s: %s' % (repr(e), str(e))

    def GetErrorVal(self):
        if self.errval:
            return self.errval
        else:
            return -1


class SD_CommandError(SD_GenericError):
    _fmt = 'Command operation break, error: 0x%(errval)08X'


class SD_DataError(SD_GenericError):
    _fmt = 'Data %(mode)s break: %(errname)s'


class SD_ConnectionError(SD_GenericError):
    _fmt = 'USB/RS232 connection error'


class SD_TimeoutError(SD_GenericError):
    _fmt = 'USB/RS232 timeout error'


class SD_SecureError(SD_GenericError):
    _fmt = 'Target is Locked !'


########################################################################################################################
## Serial Downloader Class
########################################################################################################################

class SerialDownloader(object):

    # Supported i.MX Targets
    HID_VID = 0x15A2
    HID_PID = {
        # NAME   | PID
        'MX6DQP': 0x0054,
        'MX6SDL': 0x0061,
        'MX6SL':  0x0063,
        'MX6SX':  0x0071,
        'MX6UL':  0x007D,
        'MX6ULL': 0x0080,
        'MX6SLL': 0x0128,
        'MX7SD':  0x0076,
        'VYBRID': 0x006A
    }

    # iMX Serial Downloader USB HID Reports.
    HID_REPORT = {
        'CMD': {'ID': 0x01, 'LEN': 1024},
        'DAT': {'ID': 0x02, 'LEN': 1024},
        'SEC': {'ID': 0x03, 'LEN': 4},
        'RET': {'ID': 0x04, 'LEN': 64}
    }

    # Supported commands
    CMD = {
        'READ':   {'ID': 0x0101},                     # Read memory or regs
        'WRITE':  {'ID': 0x0202, 'ACK': 0x128A8A12},  # Write one word (max 4 bytes) into memory or reg
        'WFILE':  {'ID': 0x0404, 'ACK': 0x88888888},  # Write file (image) into target memory
        'ERROR':  {'ID': 0x0505},                     # Read error state
        'WCSF':   {'ID': 0x0606, 'ACK': 0x128A8A12},  # Write CSF data into target
        'WDCD':   {'ID': 0x0A0A, 'ACK': 0x128A8A12},  # Write DCD data into target
        'JUMP':   {'ID': 0x0B0B, 'ACK': None},        # Jump to specified address and run
        'SKIPDCD':{'ID': 0x0C0C, 'ACK': 0x900DD009}   # Skip DCD content from loaded image (uboot.imx)
    }

    # Secure info flags
    SECNFO = {
        'OPEN': 0x56787856,
        'LOCK': 0x12343412
    }

    def __init__(self):
        self._usb_dev  = None
        self._uart_dev = None

    @staticmethod
    def scanUSB(pid=None):
        """ IMX SD: Scan commected USB devices
        :param: pid The PID value of USB device
        :rtype : object
        """
        usb_devs = []
        if pid:
            usb_devs += USBIF.enumerate(SerialDownloader.HID_VID, pid)
        else:
            for key, value in SerialDownloader.HID_PID.items():
                usb_devs += USBIF.enumerate(SerialDownloader.HID_VID, value)

        if usb_devs is None:
            logging.info('No Target Connected')

        return usb_devs

    @staticmethod
    def scanUART():
        return UARTIF.available_ports()

    def is_connected(self):
        """ IMX SD: Check if device connected
        """
        if self._usb_dev is not None:
            return True
        else:
            return False

    def getTargetName(self):
        if self._usb_dev:
            for name, val in self.HID_PID.items():
                if self._usb_dev.pid == val:
                    return name

    def connectUSB(self, dev):
        """ IMX SD: Connect by USB
        """
        if dev is not None:
            logging.info('Connect: %s', dev.getInfo())
            self._usb_dev = dev
            self._usb_dev.open()

            return True
        else:
            logging.info('USB Disconnected !')
            return False

    def connectUART(self, port, baudrate):
        """ IMX SD: Connect by UART """
        if port is not None:
            self._uart_dev = UARTIF()
            self._uart_dev.open(port, baudrate)
            if self._uart_dev.ping():
                return True
            else:
                self.disconnect()
                return False
        else:
            logging.info('UART Disconnected !')
            return False

    def disconnect(self):
        """ IMX SD: Disconnect USB/RS232 device """
        if self._usb_dev:
            self._usb_dev.close()
            self._usb_dev = None

        if self._uart_dev:
            self._uart_dev.close()
            self._uart_dev = None

    def _send_cmd(self, name, addr=0, format=0, count=0, value=0):
        """IMX SD: Send Command
        :param name: Command name
        :param addr:
        :param format:
        :param count:
        :param value:
        """
        if self._usb_dev is None and self._uart_dev is None:
            logging.info('RX-CMD: USB Disconnected')
            raise SD_ConnectionError('USB Disconnected !')

        buf = bytearray(struct.pack('>HIBII', self.CMD[name]['ID'], addr, format, count, value))

        # log TX raw command data
        logging.debug('TX-CMD [0x]: %s', atos(buf))

        if self._usb_dev:
            # Send USB-HID CMD OUT Report
            self._usb_dev.write(self.HID_REPORT['CMD']['ID'], buf, self.HID_REPORT['CMD']['LEN'])

    def _check_secinfo(self, timeout=1000, wait=True):
        """ IMX SD: Check secure info of connected device
        :param timeout: waiting time in ms for rx data
        :param wait:
        """
        try:
            report_id, rx_data = self._usb_dev.read(timeout)
        except:
            if wait:
                logging.info('RX-CMD: Timeout Error >> USB Disconnected')
                raise SD_TimeoutError('Timeout >> USB Disconnected !')
            else:
                return None

        if report_id != self.HID_REPORT['SEC']['ID']:
            logging.info('RX-CMD: Wrong Report ID %d', report_id)
            raise SD_DataError('Wrong Report ID')

        tmp = struct.unpack_from("I", rx_data)
        if tmp[0] == self.SECNFO['LOCK']:
            logging.info('SECURE: Target is Locked !')
            raise SD_SecureError()

        logging.debug('SECURE: Not Enabled')

    def _get_status(self, timeout=1000, wait=True):
        """ IMX SD: Read status value
        :param timeout: waiting time in ms for rx data
        :param wait:
        """
        try:
            report_id, rx_data = self._usb_dev.read(timeout)
        except:
            if wait:
                logging.info('RX-CMD: Timeout Error >> USB Disconnected')
                raise SD_TimeoutError('Timeout >> USB Disconnected !')
            else:
                return None

        if report_id != self.HID_REPORT['RET']['ID']:
            logging.info('RX-CMD: Wrong Report ID %d', report_id)
            raise SD_DataError('Wrong Report ID')

        return struct.unpack_from("I", rx_data)[0]

    def _check_status(self, cmd, timeout=1000):
        """ IMX SD: Check command status
        :param cmd: command name
        :param timeout: waiting time in ms for rx data
        """
        if 'ACK' in self.CMD[cmd]:
            status = self._get_status(timeout=timeout, wait=True if self.CMD[cmd]['ACK'] else False)
            if status is not None and status != self.CMD[cmd]['ACK']:
                logging.info('RX-CMD: ERROR: 0x%08X', status)
                raise SD_CommandError(errval=status)
        logging.info('RX-CMD: OK')

    def _read_data(self, length, timeout=1000):
        """ IMX SD: Read data from target
        :param length: count of bytes
        :param timeout: waiting time in ms for rx data
        """
        n = 0
        data = bytearray()
        while n < length:
            try:
                report_id, rx_data = self._usb_dev.read(timeout)
            except Exception as e:
                print(e)
                logging.info('RX-CMD: Timeout Error >> USB Disconnected')
                raise SD_TimeoutError('Timeout >> USB Disconnected !')
            # test for correct report
            if report_id != self.HID_REPORT['RET']['ID']:
                raise SD_DataError('Wrong Report ID')
            # add next packet
            data.extend(rx_data)
            n += len(rx_data)
        # Align RX data to required length
        if n > length:
            data = data[0:length]
        return data

    def _send_data(self, data):
        """ IMX SD: Send data to target
        :param data: array with data to send
        """
        report = self.HID_REPORT['DAT']
        length = len(data)
        offset = 0
        pkglen = report['LEN']
        while length > 0:
            if length < report['LEN']:
                pkglen = length
            try:
                self._usb_dev.write(report['ID'], data[offset:offset + pkglen], report['LEN'])
            except:
                logging.info('TX-CMD: Data Error >> USB Disconnected')
                raise SD_DataError('USB Disconnected')
            offset += pkglen
            length -= pkglen

    def read(self, address, length, format=32):
        """ IMX SD: Read value from reg/mem at specified address
        :param address: Start address of first register
        :param length: Count of bytes
        :param format: Register access format 8, 16, 32 bytes
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
        """ IMX SD: Write value into reg/mem at specified address
        :param address: Start address of first register
        :param value: Register value
        :param count: Count of bytes (max 4)
        :param format: Register access format 8, 16, 32 bytes
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

    def writeCSF(self, address, data):
        """ IMX SD: Write CSF Data at specified address
        :param address: Start Address
        :param data: The CSF data in bytearray type
        """
        logging.info('TX-CMD: WriteCSF [ Addr=0x%08X | Len=%d ] ', address, len(data))
        self._send_cmd('WCSF', address, 0, len(data))
        self._send_data(data)
        self._check_secinfo()
        self._check_status('WCSF')

    def writeDCD(self, address, data):
        """ IMX SD: Write DCD values at specified address
        :param address: Start Address
        :param data: The DCD data in bytearray type
        """
        logging.info('TX-CMD: WriteDCD [ Addr=0x%08X | Len=%d ] ', address, len(data))
        self._send_cmd('WDCD', address, 0, len(data))
        self._send_data(data)
        self._check_secinfo()
        self._check_status('WDCD')

    def writeFile(self, address, data):
        """ IMX SD: Write File/Data at specified address
        :param address: Start Address
        :param data: The image data in bytearray type
        """
        logging.info('TX-CMD: WriteFile [ Addr=0x%08X | Len=%d ] ', address, len(data))
        self._send_cmd('WFILE', address, 0, len(data))
        self._send_data(data)
        self._check_secinfo()
        self._check_status('WFILE')

    def skipDCD(self):
        """ IMX SD: Skip DCD Header from loaded file """
        logging.info('TX-CMD: SkipDCD')
        self._send_cmd('SKIPDCD')
        self._check_secinfo()
        self._check_status('SKIPDCD')

    def readStatus(self):
        """ IMX SD: Read Status
        :return status value
        """
        logging.info('TX-CMD: ReadStatus')
        self._send_cmd('ERROR')
        self._check_secinfo()
        status = self._get_status()
        logging.info('RX-CMD: 0x%08X', status)
        return status

    def jumpAndRun(self, address):
        """ IMX SD: Jump to specified address and run
        :param address: Destination address
        """
        logging.info('TX-CMD: Jump To Address: 0x%08X', address)
        self._send_cmd('JUMP', address)
        self._check_secinfo()
        self._check_status('JUMP', timeout=100)
