# Copyright (c) 2017-2018 Martin Olejar
#
# SPDX-License-Identifier: BSD-3-Clause
# The BSD-3-Clause license for this file can be found in the LICENSE file included with this distribution
# or at https://spdx.org/licenses/BSD-3-Clause.html#licenseText

from easy_enum import EEnum as Enum
from struct import pack, unpack_from, calcsize


########################################################################################################################
# Enums
########################################################################################################################

class SegTag(Enum):
    """ Segments Tag """
    DCD = (0xD2, 'Device Configuration Data')
    CSF = (0xD4, 'Command Sequence File Data')
    # i.MX6, i.MX7, i.MX8M
    IVT2 = (0xD1, 'Image Vector Table (Version 2)')
    CRT = (0xD7, 'Certificate')
    SIG = (0xD8, 'Signature')
    EVT = (0xDB, 'Event')
    RVT = (0xDD, 'ROM Vector Table')
    WRP = (0x81, 'Wrapped Key')
    MAC = (0xAC, 'Message Authentication Code')
    # i.MX8QXP_A0, i.MX8QM_A0
    IVT3 = (0xDE, 'Image Vector Table (Version 3)')
    # i.MX8QXP_B0, i.MX8QM_B0
    BIC1 = (0x87, 'Boot Images Container')
    SIGB = (0x90, 'Signature block')


class CmdTag(Enum):
    """ Commands Tag """
    SET = (0xB1, 'Set')
    INS_KEY = (0xBE, 'Install Key')
    AUT_DAT = (0xCA, 'Authenticate Data')
    WRT_DAT = (0xCC, 'Write Data')
    CHK_DAT = (0xCF, 'Check Data')
    NOP = (0xC0, 'No Operation')
    INIT = (0xB4, 'Initialize')
    UNLK = (0xB2, 'Unlock')


########################################################################################################################
# Exceptions
########################################################################################################################

class UnparsedException(Exception):
    pass


class CorruptedException(Exception):
    pass


########################################################################################################################
# Classes
########################################################################################################################

class Header(object):
    """ header element type """
    FORMAT = ">BHB"
    SIZE = calcsize(FORMAT)

    @property
    def size(self):
        """ Header Size """
        return self.SIZE

    def __init__(self, tag, param=0, length=None):
        self.tag = tag
        self.param = param
        self.length = self.SIZE if length is None else length

    def __str__(self):
        return self.info()

    def __repr__(self):
        return self.info()

    def info(self):
        return "HEADER < TAG: 0x{:02X}, PARAM: 0x{:02X}, DLEN: {:d} Bytes >\n".format(self.tag, self.param, self.length)

    def export(self):
        return pack(self.FORMAT, self.tag, self.length, self.param)

    @classmethod
    def parse(cls, data, offset=0, required_tag=None):
        """ Parse header
        :param data: Raw data as bytes or bytearray
        :param offset: Offset of input data
        :param required_tag:
        :return:
        """
        tag, length, param = unpack_from(cls.FORMAT, data, offset)
        if required_tag is not None and tag != required_tag:
            raise UnparsedException(" Invalid header tag: '0x{:02X}' expected '0x{:02X}' ".format(tag, required_tag))

        return cls(tag, param, length)


class Header2(Header):
    """ header element type """
    FORMAT = "<BHB"

    def export(self):
        return pack(self.FORMAT, self.param, self.length, self.tag)

    @classmethod
    def parse(cls, data, offset=0, required_tag=None):
        """ Parse header
        :param data: Raw data as bytes or bytearray
        :param offset: Offset of input data
        :param required_tag:
        :return: Header2 object
        """
        param, length, tag = unpack_from(cls.FORMAT, data, offset)
        if required_tag is not None and tag != required_tag:
            raise UnparsedException(" Invalid header tag: '0x{:02X}' expected '0x{:02X}' ".format(tag, required_tag))

        return cls(tag, param, length)
