# Copyright (c) 2017-2018 Martin Olejar
#
# SPDX-License-Identifier: BSD-3-Clause
# The BSD-3-Clause license for this file can be found in the LICENSE file included with this distribution
# or at https://spdx.org/licenses/BSD-3-Clause.html#licenseText

from io import BytesIO, BufferedReader, SEEK_CUR
from .header import Header


def size_fmt(num, use_kibibyte=True):
    base, suffix = [(1000., 'B'), (1024., 'iB')][use_kibibyte]
    for x in ['B'] + [x + suffix for x in list('kMGTP')]:
        if -base < num < base:
            break
        num /= base
    return "{0:3.1f} {1:s}".format(num, x)


def modulus_fmt(modulus, tab=4, length=15, sep=':'):
    text = ' ' * tab
    data = b'\0' + modulus
    for i, b in enumerate(data):
        text += "{:02x}{}".format(b, sep)
        if ((i + 1) % length) == 0:
            text += '\n' + ' ' * tab
    return text


def read_raw_data(stream, length, index=None, no_seek=False):
    if index is not None:
        if index < 0:
            raise ValueError(" Index must be non-negative, found {}".format(index))
        if index != stream.tell():
            stream.seek(index)

    if length < 0:
        raise ValueError(" Length must be non-negative, found {}".format(length))

    try:
        data = stream.read(length)
    except Exception:
        raise Exception(" stream.read() failed, requested {} bytes".format(length))

    if len(data) != length:
        raise Exception(" Could not read enough bytes, expected {}, found {}".format(length, len(data)))

    if no_seek:
        stream.seek(-length, SEEK_CUR)

    return data


def read_raw_segment(buffer, segment_tag, index=None):
    hrdata = read_raw_data(buffer, Header.SIZE, index)
    length = Header.parse(hrdata, 0, segment_tag).length - Header.SIZE
    return hrdata + read_raw_data(buffer, length)
