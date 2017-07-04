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