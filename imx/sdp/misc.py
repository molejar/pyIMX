# Copyright (c) 2017-2018 Martin Olejar
#
# SPDX-License-Identifier: BSD-3-Clause
# The BSD-3-Clause license for this file can be found in the LICENSE file included with this distribution
# or at https://spdx.org/licenses/BSD-3-Clause.html#licenseText


def atos(data, sep=' ', fmt='02X'):
    """
    Convert array of bytes into HEX String
    :rtype: String
    """
    ret = ''
    for x in data:
        if fmt == 'c':
            if 0x00 < x < 0x7F:
                ret += ('{:'+fmt+'}').format(x)
            else:
                ret += '.'
        else:
            ret += ('{:'+fmt+'}').format(x)
        ret += sep
    return ret


def crc16(data, crc_init=0):
    """
    Calculate CRC from input data
    :rtype: int value
    """
    crc = crc_init
    for c in data:
        crc ^= c << 8
        for _ in range(8):
            temp = crc << 1
            if crc & 0x8000:
                temp ^= 0x1021
            crc = temp
    return crc
