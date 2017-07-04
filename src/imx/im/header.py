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

from enum import IntEnum, unique
from struct import pack, unpack_from, calcsize


########################################################################################################################
## Enums
########################################################################################################################

@unique
class CmdTag(IntEnum):
    HAB_CMD_SET     = 0xB1  # Set
    HAB_CMD_INS_KEY = 0xBE  # Install Key
    HAB_CMD_AUT_DAT = 0xCA  # Authenticate Data
    HAB_CMD_WRT_DAT = 0xCC  # Write Data
    HAB_CMD_CHK_DAT = 0xCF  # Check Data
    HAB_CMD_NOP     = 0xC0  # No Operation
    HAB_CMD_INIT    = 0xB4  # Initialize
    HAB_CMD_UNLK    = 0xB2  # Unlock


@unique
class SegTag(IntEnum):
    HAB_TAG_IVT = 0xD1  # Image Vector Table
    HAB_TAG_DCD = 0xD2  # Device Configuration Data
    HAB_TAG_CSF = 0xD4  # Command Sequence File
    HAB_TAG_CRT = 0xD7  # Certificate
    HAB_TAG_SIG = 0xD8  # Signature
    HAB_TAG_EVT = 0xDB  # Event
    HAB_TAG_RVT = 0xDD  # ROM Vector Table
    HAB_TAG_WRP = 0x81  # Wrapped Key
    HAB_TAG_MAC = 0xAC  # Message Authentication Code


########################################################################################################################
## Exceptions
########################################################################################################################


class UnparsedException(Exception):
    pass


class CorruptedException(Exception):
    pass


########################################################################################################################
## Classes
########################################################################################################################

class Header(object):
    ''' header element type '''
    FORMAT = ">BHB"

    @property
    def tag(self):
        return self._tag

    @property
    def length(self):
        return self._length

    @length.setter
    def length(self, value):
        self._length = value

    @property
    def param(self):
        return self._param

    @param.setter
    def param(self, value):
        self._param = value

    @property
    def size(self):
        ''' data size '''
        return self._size

    def __init__(self, tag, param=0):
        self._size = calcsize(self.FORMAT)
        self._tag = tag
        self._length = self._size
        self._param = param

    def __str__(self):
        return self.info()

    def __repr__(self):
        return self.info()

    def info(self):
        msg = "HEADER < TAG: 0x{0:X}, PARAM: 0x{1:X}, DLEN: {2:d} Bytes >\n".format(self.tag, self.param, self.length)
        return msg

    def parse(self, data, offset=0):
        (tag, length, param) = unpack_from(self.FORMAT, data, offset)
        if tag != self.tag:
            raise UnparsedException("Invalid header '0x#{0:X}' expected '0x#{1:X}' ".format(tag, self.tag))
        self.length = length
        self.param = param

    def export(self):
        return pack(self.FORMAT, self.tag, self.length, self.param)
