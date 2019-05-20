# Copyright (c) 2017-2018 Martin Olejar
#
# SPDX-License-Identifier: BSD-3-Clause
# The BSD-3-Clause license for this file can be found in the LICENSE file included with this distribution
# or at https://spdx.org/licenses/BSD-3-Clause.html#licenseText

from struct import pack, unpack_from
from hashlib import sha256

from .misc import modulus_fmt
from .header import SegTag, Header
from .commands import EnumAlgorithm


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

    def info(self):
        pass

    def export(self):
        raw_data = pack("BBBB", self.mode, self.alg, self.size, self.flg)
        if self.data:
            raw_data += self.data
        return raw_data

    def parse(self, data, offset=0):
        (self.mode, self.alg, self.size, self.flg) = unpack_from("BBBB", data, offset)
        self.data = data[offset + 4: offset + 4 + self.size]


class Certificate(object):

    @property
    def version(self):
        return self._header.param

    @property
    def size(self):
        return Header.SIZE + len(self._data)

    def __init__(self, version=0x40, data=None):
        self._header = Header(tag=SegTag.CRT, param=version)
        self._data = data

    def info(self):
        msg = "-" * 60 + "\n"
        msg += "Certificate (version 0x{:02X})\n".format(self.version)
        msg += "-" * 60 + "\n"
        return msg

    def export(self):
        self._header.length = self.size
        raw_data = self._header.export()
        raw_data += self._data
        return raw_data

    @classmethod
    def parse(cls, data, offset=0):
        header = Header.parse(data, offset, SegTag.CRT)
        offset += Header.SIZE
        return cls(header.param, data[offset: offset + (header.length - Header.SIZE)])


class Signature(object):

    @property
    def version(self):
        return self._header.param

    @property
    def size(self):
        return Header.SIZE + len(self._data)

    def __init__(self, version=0x40, data=None):
        self._header = Header(tag=SegTag.SIG, param=version)
        self._data = data

    def info(self):
        msg = "-" * 60 + "\n"
        msg += "Signature (version 0x{:02X})\n".format(self.version)
        msg += "-" * 60 + "\n"
        return msg

    def export(self):
        self._header.length = self.size
        raw_data = self._header.export()
        raw_data += self._data
        return raw_data

    @classmethod
    def parse(cls, data, offset=0):
        header = Header.parse(data, offset, SegTag.SIG)
        offset += Header.SIZE
        return cls(header.param, data[offset: offset + (header.length - Header.SIZE)])


class MAC(object):

    @property
    def version(self):
        return self._header.param

    @property
    def size(self):
        return Header.SIZE + 4 + len(self._data)

    def __init__(self, version=0x40, nonce_bytes=0, mac_bytes=0, data=None):
        self._header = Header(tag=SegTag.MAC, param=version)
        self.nonce_bytes = nonce_bytes
        self.mac_bytes = mac_bytes
        self._data = data

    def __repr__(self):
        return "MAC <Version: {:02X}, Keys: {}>".format(self.version, self.nonce_bytes, self.mac_bytes)

    def info(self):
        msg = "-" * 60 + "\n"
        msg += "MAC (version 0x{:02X})\n".format(self.version)
        msg += "-" * 60 + "\n"
        return msg

    def export(self):
        self._header.length = self.size
        raw_data = self._header.export()
        raw_data += self._data
        return raw_data

    @classmethod
    def parse(cls, data, offset=0):
        header = Header.parse(data, offset, SegTag.MAC)
        # TODO:
        return cls(header.param)


class SrkItem(object):

    SRK_TAG = 0xE1

    @property
    def algorithm(self):
        return self._header.param

    @property
    def flag(self):
        return self._flag

    @flag.setter
    def flag(self, value):
        assert value in (0, 0x80)
        self._flag = value

    @property
    def size(self):
        return Header.SIZE + 8 + len(self.modulus) + len(self.exponent)

    def __init__(self, modulus=b'', exponent=b'', flag=0, algorithm=EnumAlgorithm.PKCS1):
        self._header = Header(tag=self.SRK_TAG, param=algorithm)
        self.flag = flag
        self.modulus = modulus
        self.exponent = exponent

    def __repr__(self):
        return "SRK <Algorithm: {}, CA: {}>".format(EnumAlgorithm[self.algorithm], 'YES' if self.flag == 0x80 else 'NO')

    def info(self):
        msg = str()
        msg += "Algorithm: {}\n".format(EnumAlgorithm[self.algorithm])
        msg += "Flag:      0x{:02X}\n".format(self.flag)
        msg += "Length:    {} bit\n".format(len(self.modulus) * 8)
        msg += "Modulus:\n"
        msg += modulus_fmt(self.modulus)
        msg += "\n"
        msg += "Exponent: {0} (0x{0:X})\n".format(int.from_bytes(self.exponent, 'big'))
        return msg

    def export(self):
        self._header.length = self.size
        data = self._header.export()
        data += pack(">4B2H", 0, 0, 0, self.flag, len(self.modulus), len(self.exponent))
        data += bytes(self.modulus)
        data += bytes(self.exponent)
        return data

    @classmethod
    def parse(cls, data, offset=0):
        header = Header.parse(data, offset, cls.SRK_TAG)
        offset += Header.SIZE + 3
        (flag, modulus_len, exponent_len) = unpack_from(">B2H", data, offset)
        offset += 5
        modulus = data[offset: offset + modulus_len]
        offset += modulus_len
        exponent = data[offset: offset + exponent_len]
        return cls(modulus, exponent, flag, header.param)


class SrkTable(object):

    @property
    def version(self):
        return self._header.param

    @property
    def size(self):
        size = Header.SIZE
        for key in self._keys:
            size += key.size
        return size

    def __init__(self, version=0x40):
        self._header = Header(tag=SegTag.CRT, param=version)
        self._keys = []

    def __repr__(self):
        return "SRK_Table <Version: {:02X}, Keys: {}>".format(self.version, len(self._keys))

    def __len__(self):
        return len(self._keys)

    def __getitem__(self, key):
        return self._keys[key]

    def __setitem__(self, key, value):
        assert isinstance(value, SrkItem)
        self._keys[key] = value

    def __iter__(self):
        return self._keys.__iter__()

    def info(self):
        msg = "-" * 60 + "\n"
        msg += "SRK Table (Version 0x{:02X}, Keys: {})\n".format(self.version, len(self._keys))
        msg += "-" * 60 + "\n"
        for i, srk in enumerate(self._keys):
            msg += "Key Index: {} \n".format(i)
            msg += srk.info()
            msg += "\n"
        return msg

    def append(self, srk):
        self._keys.append(srk)

    def export_fuses(self):
        data = b''
        for srk in self._keys:
            srk_data = srk.export()
            data += sha256(srk_data).digest()
        return sha256(data).digest()

    def export(self):
        self._header.length = self.size
        raw_data = self._header.export()
        for srk in self._keys:
            raw_data += srk.export()
        return raw_data

    @classmethod
    def parse(cls, data, offset=0):
        header = Header.parse(data, offset, SegTag.CRT)
        offset += Header.SIZE
        obj = cls(header.param)
        length = header.length - Header.SIZE
        while length > 0:
            srk = SrkItem.parse(data, offset)
            offset += srk.size
            length -= srk.size
            obj.append(srk)
        return obj
