# Copyright (c) 2017-2018 Martin Olejar
#
# SPDX-License-Identifier: BSD-3-Clause
# The BSD-3-Clause license for this file can be found in the LICENSE file included with this distribution
# or at https://spdx.org/licenses/BSD-3-Clause.html#licenseText

from struct import pack, unpack_from

from .header import SegTag, Header


class SecretKeyBlob(object):
    """ Secret Key Blob """

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, value):
        self._mode = value

    @property
    def alg(self):
        return self._alg

    @alg.setter
    def alg(self, value):
        self._alg = value

    @property
    def flg(self):
        return self._flg

    @flg.setter
    def flg(self, value):
        self._flg = value

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, value):
        self._data = value

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, value):
        self._size = value

    def __init__(self, mode=None, alg=None, flg=None, data=None):
        self._mode = mode
        self._alg = alg
        self._flg = flg
        self._data = data
        self._size = 0

    def parse(self, data, offset=0):
        (self.mode, self.alg, self.size, self.flg) = unpack_from("BBBB", data, offset)
        self.data = data[offset + 4: offset + 4 + self.size]

    def export(self):
        raw_data = pack("BBBB", self.mode, self.alg, self.size, self.flg)
        if self.data:
            raw_data += self.data
        return raw_data


class Certificate(object):

    @property
    def param(self):
        return self._header.param

    @property
    def size(self):
        return self._header.length

    def __init__(self, param=0, data=None):
        self._header = Header(tag=SegTag.CRT, param=param)
        self._data = data

    def __str__(self):
        return self.info()

    def __repr__(self):
        return self.info()

    def info(self):
        msg = "-" * 60 + "\n"
        msg += "Certificate:\n"
        msg += "-" * 60 + "\n"
        return msg

    def parse(self, data, offset=0):
        self._header.parse(data, offset)
        self._data = data[offset + self._header.size : offset + self._header.length]

    def export(self):
        raw_data = self._header.export()
        raw_data += self._data
        return raw_data


class Signature(object):

    @property
    def param(self):
        return self._header.param

    @property
    def size(self):
        return self._header.length

    def __init__(self, param=0, data=None):
        self._header = Header(tag=SegTag.SIG, param=param)
        self._data = data

    def __str__(self):
        return self.info()

    def __repr__(self):
        return self.info()

    def info(self):
        msg = "-" * 60 + "\n"
        msg += "Signature:\n"
        msg += "-" * 60 + "\n"
        return msg

    def parse(self, data, offset=0):
        self._header.parse(data, offset)
        self._data = data[offset + self._header.size : offset + self._header.length]

    def export(self):
        raw_data = self._header.export()
        raw_data += self._data
        return raw_data
