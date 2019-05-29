# Copyright (c) 2017-2019 Martin Olejar
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
        # assert value
        self._mode = value

    @property
    def algorithm(self):
        return self._alg

    @algorithm.setter
    def algorithm(self, value):
        # assert value
        self._alg = value

    @property
    def flag(self):
        return self._flg

    @flag.setter
    def flag(self, value):
        # assert value
        self._flg = value

    @property
    def blob(self):
        return self._data

    @blob.setter
    def blob(self, value):
        assert isinstance(value, (bytes, bytearray))
        self._data = value

    @property
    def size(self):
        return len(self._data) + 4

    def __init__(self, mode, algorithm, flag):
        self._mode = mode
        self._alg = algorithm
        self._flg = flag
        self._data = bytearray()

    def __repr__(self):
        return "SecKeyBlob <Mode: {}, Algo: {}, Flag: 0x{:02X}, Size: {}>".format(self.mode, self.algorithm,
                                                                                  self.flag, len(self._data))

    def __eq__(self, obj):
        if not isinstance(obj, SecretKeyBlob):
            return False
        if self.mode != obj.mode or \
           self.algorithm != obj.algorithm or \
           self.flag != obj.flag:
            return False
        if self.blob != obj.blob:
            return False
        return True

    def __ne__(self, obj):
        return not self.__eq__(obj)

    def info(self):
        msg = "-" * 60 + "\n"
        msg += "SecKeyBlob\n"
        msg += "-" * 60 + "\n"
        msg += "Mode:      {}\n".format(self.mode)
        msg += "Algorithm: {}\n".format(self.algorithm)
        msg += "Flag:      0x{:02X}\n".format(self.flag)
        msg += "Size:      {} Bytes\n".format(len(self._data))
        return msg

    def export(self):
        raw_data = pack("4B", self.mode, self.algorithm, self.size, self.flag)
        raw_data += bytes(self._data)
        return raw_data

    @classmethod
    def parse(cls, data, offset=0):
        (mode, alg, size, flg) = unpack_from("4B", data, offset)
        offset += 4
        obj = cls(mode, alg, flg)
        obj.blob = data[offset: offset + size]
        return obj


class Certificate(object):

    @property
    def version(self):
        return self._header.param

    @property
    def size(self):
        return Header.SIZE + len(self._data)

    def __init__(self, version=0x40, data=None):
        self._header = Header(tag=SegTag.CRT, param=version)
        self._data = bytearray() if data is None else bytearray(data)

    def __repr__(self):
        return "Certificate <Ver: {:X}.{:X}, Size: {}>".format(self.version >> 4, self.version & 0xF, len(self._data))

    def __eq__(self, obj):
        if not isinstance(obj, Certificate):
            return False
        if self.version != obj.version:
            return False
        for i, value in enumerate(self._data):
            if obj[i] != value:
                return False
        return True

    def __ne__(self, obj):
        return not self.__eq__(obj)

    def __len__(self):
        return len(self._data)

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value

    def __iter__(self):
        return self._data.__iter__()

    def info(self):
        msg = "-" * 60 + "\n"
        msg += "Certificate (Ver: {:X}.{:X}, Size: {})\n".format(self.version >> 4, self.version & 0xF, len(self._data))
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
        return cls(header.param, data[offset: offset + header.length - Header.SIZE])


class Signature(object):

    @property
    def version(self):
        return self._header.param

    @property
    def size(self):
        return Header.SIZE + len(self._data)

    def __init__(self, version=0x40, data=None):
        self._header = Header(tag=SegTag.SIG, param=version)
        self._data = bytearray() if data is None else bytearray(data)

    def __repr__(self):
        return "Signature <Ver: {:X}.{:X}, Size: {}>".format(self.version >> 4, self.version & 0xF, len(self._data))

    def __eq__(self, obj):
        if not isinstance(obj, Signature):
            return False
        if self.version != obj.version:
            return False
        for i, value in enumerate(self._data):
            if obj[i] != value:
                return False
        return True

    def __ne__(self, obj):
        return not self.__eq__(obj)

    def __len__(self):
        return len(self._data)

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value

    def __iter__(self):
        return self._data.__iter__()

    def info(self):
        msg = "-" * 60 + "\n"
        msg += "Signature (Ver: {:X}.{:X}, Size: {})\n".format(self.version >> 4, self.version & 0xF, len(self._data))
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
        return cls(header.param, data[offset: offset + header.length - Header.SIZE])


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
        self._data = bytearray() if data is None else bytearray(data)

    def __repr__(self):
        return "MAC <Ver: {:X}.{:X}, Nonce: {}, MAC: {}>".format(self.version >> 4, self.version & 0xF,
                                                                 self.nonce_bytes, self.mac_bytes)

    def __eq__(self, obj):
        if not isinstance(obj, MAC):
            return False
        if self.version != obj.version or \
           self.nonce_bytes != obj.nonce_bytes or \
           self.mac_bytes != obj.mac_bytes:
            return False
        for i, value in enumerate(self._data):
            if obj[i] != value:
                return False
        return True

    def __ne__(self, obj):
        return not self.__eq__(obj)

    def __len__(self):
        return len(self._data)

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value

    def __iter__(self):
        return self._data.__iter__()

    def info(self):
        msg = "-" * 60 + "\n"
        msg += "MAC (Version: {:X}.{:X})\n".format(self.version >> 4, self.version & 0xF)
        msg += "-" * 60 + "\n"
        msg += "Nonce Len: {} Bytes\n".format(self.nonce_bytes)
        msg += "MAC Len:   {} Bytes\n".format(self.mac_bytes)
        msg += "[{}]\n".format(self._data)
        return msg

    def export(self):
        self._header.length = self.size
        raw_data = self._header.export()
        raw_data += pack(">4B", 0, self.nonce_bytes, 0, self.mac_bytes)
        raw_data += bytes(self._data)
        return raw_data

    @classmethod
    def parse(cls, data, offset=0):
        header = Header.parse(data, offset, SegTag.MAC)
        (_, nonce_bytes, _, mac_bytes) = unpack_from(">4B", data, offset)
        offset += Header.SIZE + 4
        return cls(header.param, nonce_bytes, mac_bytes, data[offset: offset + header.length - (Header.SIZE + 4)])


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
    def key_length(self):
        return len(self.modulus) * 8

    @property
    def size(self):
        return Header.SIZE + 8 + len(self.modulus) + len(self.exponent)

    def __init__(self, modulus, exponent, flag=0, algorithm=EnumAlgorithm.PKCS1):
        assert isinstance(modulus, bytes)
        assert isinstance(exponent, bytes)
        self._header = Header(tag=self.SRK_TAG, param=algorithm)
        self.flag = flag
        self.modulus = modulus
        self.exponent = exponent

    def __repr__(self):
        return "SRK <Algorithm: {}, CA: {}>".format(EnumAlgorithm[self.algorithm], 'YES' if self.flag == 0x80 else 'NO')

    def __eq__(self, obj):
        if not isinstance(obj, SrkItem):
            return False
        if self.algorithm != obj.algorithm or \
           self.flag != obj.flag or \
           self.key_length != obj.key_length or \
           self.modulus != obj.modulus or \
           self.exponent != obj.exponent:
            return False
        return True

    def __ne__(self, obj):
        return not self.__eq__(obj)

    def info(self):
        msg = str()
        msg += "Algorithm: {}\n".format(EnumAlgorithm[self.algorithm])
        msg += "Flag:      0x{:02X} {}\n".format(self.flag, '(CA)' if self.flag == 0x80 else '')
        msg += "Length:    {} bit\n".format(self.key_length)
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
        """ Parse segment from bytes array
        :param data: The bytes array of SRK segment
        :param offset: The offset of input data
        :return SrkItem object
        """
        header = Header.parse(data, offset, cls.SRK_TAG)
        offset += Header.SIZE + 3
        (flag, modulus_len, exponent_len) = unpack_from(">B2H", data, offset)
        offset += 5
        modulus = data[offset: offset + modulus_len]
        offset += modulus_len
        exponent = data[offset: offset + exponent_len]
        return cls(modulus, exponent, flag, header.param)

    @classmethod
    def from_certificate(cls, cert):

        from cryptography import x509
        assert isinstance(cert, x509.Certificate)

        flag = 0

        for extension in cert.extensions:
            if extension.oid._name == 'keyUsage':
                if extension.value.key_cert_sign:
                    flag = 0x80

        # get modulus and exponent of public key
        pub_key_numbers = cert.public_key().public_numbers()
        modulus_len = pub_key_numbers.n.bit_length() // 8
        if pub_key_numbers.n.bit_length() % 8:
            modulus_len += 1
        exponent_len = pub_key_numbers.e.bit_length() // 8
        if pub_key_numbers.e.bit_length() % 8:
            exponent_len += 1
        modulus = pub_key_numbers.n.to_bytes(modulus_len, "big")
        exponent = pub_key_numbers.e.to_bytes(exponent_len, "big")

        return cls(modulus, exponent, flag)


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
        return "SRK_Table <Version: {:X}.{:X}, Keys: {}>".format(self.version >> 4, self.version & 0xF, len(self._keys))

    def __eq__(self, obj):
        if not isinstance(obj, SrkTable):
            return False
        if self.version != obj.version:
            return False
        for key in obj:
            if key not in self._keys:
                return False
        return True

    def __ne__(self, obj):
        return not self.__eq__(obj)

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
        msg += "SRK Table (Version: {:X}.{:X}, Keys: {})\n".format(self.version>>4, self.version&0xF, len(self._keys))
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
