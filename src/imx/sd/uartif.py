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
import glob
import logging
import threading
import serial
from time import time

from .misc import atos, crc16


class UARTIF(object):

    def __init__(self):
        self.ser = serial.Serial()

    @staticmethod
    def available_ports():
        if sys.platform.startswith('win'):
            ports = ['COM%s' % (i + 1) for i in range(256)]
        elif sys.platform.startswith('linux') or \
             sys.platform.startswith('cygwin'):
            # this excludes your current terminal "/dev/tty"
            ports = glob.glob('/dev/tty[A-Za-z]*')
        elif sys.platform.startswith('darwin'):
            ports = glob.glob('/dev/tty.*')
        else:
            raise EnvironmentError('Unsupported platform')

        result = []
        for port in ports:
            try:
                s = serial.Serial(port)
                s.close()
                result.append(port)
            except (OSError, serial.SerialException):
                pass

        return result

    def open(self, port, baudrate=115200):
        self.ser.port = port
        self.ser.baudrate = baudrate
        self.ser.bytesize = serial.EIGHTBITS     # number of bits per bytes
        self.ser.parity = serial.PARITY_NONE     # set parity check: no parity
        self.ser.stopbits = serial.STOPBITS_ONE  # number of stop bits
        self.ser.timeout = 1                     # non-block read
        self.ser.xonxoff = False                 # disable software flow control
        self.ser.rtscts = False                  # disable hardware (RTS/CTS) flow control
        self.ser.dsrdtr = False                  # disable hardware (DSR/DTR) flow control
        self.ser.writeTimeout = 2                # timeout for write
        #self.ser.timeout = None                  # block read
        try:
            self.ser.open()
        except Exception as e:
            print("error open serial port: " + str(e))

    def close(self):
        if self.ser.isOpen():
            self.ser.close()

    def get_supported_baudrates(self):
        if self.ser.isOpen():
            self.ser.getSupportedBaudrates()

    def read(self, timeout=5000):
        if not self.ser.isOpen():
            raise Exception("UART Disconnected")

        # TODO: add implementation

    def write(self, type, data, timeout=5000):
        if not self.ser.isOpen():
            raise Exception("UART Disconnected")

        # TODO: add implementation


