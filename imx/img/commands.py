# Copyright (c) 2017-2018 Martin Olejar
#
# SPDX-License-Identifier: BSD-3-Clause
# The BSD-3-Clause license for this file can be found in the LICENSE file included with this distribution
# or at https://spdx.org/licenses/BSD-3-Clause.html#licenseText

from easy_enum import EEnum as Enum
from struct import pack, unpack_from
from .header import CmdTag, Header


########################################################################################################################
# Enums
########################################################################################################################

class EnumWriteOps(Enum):
    """ Enum definition for 'flags' control flags in 'par' parameter of Write Data command """
    WRITE_VALUE = (0, 'Write value')
    WRITE_VALUE1 = (1, 'Write value')
    CLEAR_BITMASK = (2, 'Clear bitmask')
    SET_BITMASK = (3, 'Set bitmask')


class EnumCheckOps(Enum):
    """ Enum definition for 'par' parameter of Check Data command """
    ALL_CLEAR = (0, 'All bits clear')
    ALL_SET = (1, 'All bits set')
    ANY_CLEAR = (2, 'Any bit clear')
    ANY_SET = (3, 'Any bit set')


class EnumAlgorithm(Enum):
    """ Algorithm types """
    ANY = (0x00, 'Algorithm type ANY')
    HASH = (0x01, 'Hash algorithm type')
    SIG = (0x02, 'Signature algorithm type')
    F = (0x03, 'Finite field arithmetic')
    EC = (0x04, 'Elliptic curve arithmetic')
    CIPHER = (0x05, 'Cipher algorithm type')
    MODE = (0x06, 'Cipher/hash modes')
    WRAP = (0x07, 'Key wrap algorithm type')
    # Hash algorithms
    SHA1 = (0x11, 'SHA-1 algorithm ID')
    SHA256 = (0x17, 'SHA-256 algorithm ID')
    SHA512 = (0x1b, 'SHA-512 algorithm ID')
    # Signature algorithms
    PKCS1 = (0x21, 'PKCS#1 RSA signature algorithm')
    # Cipher algorithms
    AES = (0x55, 'AES algorithm ID')
    # Cipher or hash modes
    CCM = (0x66, 'Counter with CBC-MAC')
    # Key wrap algorithms
    BLOB = (0x71, 'SHW-specific key wrap')


class EnumCertFormat(Enum):
    """ Certificate format tags """
    SRK = (0x03, 'SRK certificate format')
    X509 = (0x09, 'X.509v3 certificate format')
    CMS = (0xC5, 'CMS/PKCS#7 signature format')
    BLOB = (0xBB, 'SHW-specific wrapped key format')
    AEAD = (0xA3, 'Proprietary AEAD MAC format')


class EnumInsKey(Enum):
    """ Flags for Install Key commands """
    CLR = (0, 'No flags set')
    ABS = (1, 'Absolute certificate address')
    CSF = (2, 'Install CSF key')
    DAT = (4, 'Key binds to Data Type')
    CFG = (8, 'Key binds to Configuration')
    FID = (16, 'Key binds to Fabrication UID')
    MID = (32, 'Key binds to Manufacturing ID')
    CID = (64, 'Key binds to Caller ID')
    HSH = (128, 'Certificate hash present')


class EnumAuthDat(Enum):
    """ Flags for Authenticate Data commands """
    CLR = (0, 'No flags set')
    ABS = (1, 'Absolute signature address')


class EnumEngine(Enum):
    """ Engine plugin tags """
    ANY = (0x00, 'First compatible engine will be selected (no engine configuration parameters are allowed)')
    SCC = (0x03, 'Security controller')
    RTIC = (0x05, 'Run-time integrity checker')
    SAHARA = (0x06, 'Crypto accelerator')
    CSU = (0x0A, 'Central Security Unit')
    SRTC = (0x0C, 'Secure clock')
    DCP = (0x1B, 'Data Co-Processor')
    CAAM = (0x1D, 'Cryptographic Acceleration and Assurance Module')
    SNVS = (0x1E, 'Secure Non-Volatile Storage')
    OCOTP = (0x21, 'Fuse controller')
    DTCP = (0x22, 'DTCP co-processor')
    ROM = (0x36, 'Protected ROM area')
    HDCP = (0x24, 'HDCP co-processor')
    SW = (0xFF, 'Software engine')


class EnumCAAM(Enum):
    """ CAAM Engine Configuration """
    DEFAULT = 0x00
    IN_SWAP8 = 0x01
    IN_SWAP16 = 0x02
    OUT_SWAP8 = 0x08
    OUT_SWAP16 = 0x10
    DSC_SWAP8 = 0x40
    DSC_SWAP16 = 0x80


class EnumItm(Enum):
    """ Engine configuration flags of Set command """
    MID = (0x01, 'Manufacturing ID (MID) fuse locations')
    ENG = (0x03, 'Preferred engine for a given algorithm')


########################################################################################################################
# Abstract Class
########################################################################################################################

class CmdBase(object):

    @property
    def size(self):
        return self._header.length

    def __init__(self, tag, param, length=None):
        self._header = Header(tag, param, length)

    def __ne__(self, cmd):
        return not self.__eq__(cmd)

    def info(self):
        raise NotImplementedError()

    def export(self):
        raise NotImplementedError()

    @classmethod
    def parse(cls, data, offset=0):
        raise NotImplementedError()


########################################################################################################################
# HAB Commands
########################################################################################################################

class CmdWriteData(CmdBase):
    """ Write data command """

    @property
    def bytes(self):
        return self._header.param & 0x7

    @bytes.setter
    def bytes(self, value):
        assert value in (1, 2, 4)
        self._header.param &= ~0x7
        self._header.param |= value

    @property
    def ops(self):
        return (self._header.param >> 3) & 0x3

    @ops.setter
    def ops(self, value):
        assert EnumWriteOps.is_valid(value)
        self._header.param &= ~(0x3 << 3)
        self._header.param |= int(value) << 3

    def __init__(self, bytes=4, ops=EnumWriteOps.WRITE_VALUE, data=None):
        assert bytes in (1, 2, 4)
        assert EnumWriteOps.is_valid(ops)
        super().__init__(CmdTag.WRT_DAT, ((int(ops) & 0x3) << 3) | (bytes & 0x7))
        self._data = []
        if data is not None:
            assert isinstance(data, (list, tuple))
            for address, value in data:
                self.append(address, value)

    def __repr__(self):
        return "CmdWriteData <{}/{}, {}>".format(EnumWriteOps[self.ops], self.bytes, len(self._data))

    def __eq__(self, cmd):
        if not isinstance(cmd, CmdWriteData):
            return False
        if self.size != cmd.size or self.bytes != cmd.bytes or self.ops != cmd.ops:
            return False
        for val in cmd:
            if val not in self._data:
                return False
        return True

    def __len__(self):
        return len(self._data)

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value

    def __iter__(self):
        return self._data.__iter__()

    def info(self):
        msg  = "-" * 60 + "\n"
        msg += "Write Data Command (Ops: {0:s}, Bytes: {1:d})\n".format(EnumWriteOps[self.ops], self.bytes)
        msg += "-" * 60 + "\n"
        for cmd in self._data:
            msg += "- Address: 0x{0:08X}, Value: 0x{1:08X}\n".format(cmd[0], cmd[1])
        return msg

    def append(self, address, value):
        assert 0 <= address <= 0xFFFFFFFF, "address out of range"
        assert 0 <= value <= 0xFFFFFFFF, "value out of range"
        self._data.append([address, value])
        self._header.length += 8

    def pop(self, index):
        assert 0 <= index < len(self._data)
        cmd = self._data.pop(index)
        self._header.length -= 8
        return cmd

    def clear(self):
        self._data.clear()
        self._header.length = self._header.size

    def export(self):
        raw_data = self._header.export()
        for cmd in self._data:
            raw_data += pack(">LL", cmd[0], cmd[1])
        return raw_data

    @classmethod
    def parse(cls, data, offset=0):
        header = Header.parse(data, offset, CmdTag.WRT_DAT)
        obj = cls(header.param & 0x7, (header.param >> 3) & 0x3)
        index = header.size
        while index < header.length:
            (address, value) = unpack_from(">LL", data, offset + index)
            obj.append(address, value)
            index += 8
        return obj


class CmdCheckData(CmdBase):
    """ Check data command """

    @property
    def bytes(self):
        return self._header.param & 0x7

    @bytes.setter
    def bytes(self, value):
        assert value in (1, 2, 4), "Unsupported Value !"
        self._header.param &= ~0x7
        self._header.param |= int(value)

    @property
    def ops(self):
        return (self._header.param >> 3) & 0x3

    @ops.setter
    def ops(self, value):
        assert EnumCheckOps.is_valid(value), "Unsupported value !"
        self._header.param &= ~(0x3 << 3)
        self._header.param |= int(value) << 3

    @property
    def address(self):
        return self._address

    @address.setter
    def address(self, value):
        self._address = value

    @property
    def mask(self):
        return self._mask

    @mask.setter
    def mask(self, value):
        self._mask = value

    @property
    def count(self):
        return self._count

    @count.setter
    def count(self, value):
        self._count = value

    @property
    def size(self):
        return self._header.size + (8 if self._count is None else 12)

    def __init__(self, bytes=4, ops=EnumCheckOps.ALL_SET, address=0, mask=0, count=None):
        assert bytes in (1, 2, 4), "Unsupported Value !"
        assert EnumCheckOps.is_valid(ops), "Unsupported value !"
        super().__init__(CmdTag.CHK_DAT, ((int(ops) & 0x3) << 3) | (bytes & 0x7))
        self._address = address
        self._mask = mask
        self._count = count

    def __repr__(self):
        return "CmdCheckData <{}/{}, ADDR=0x{:X}, MASK=0x{:X}>".format(
            EnumCheckOps[self.ops], self.bytes, self.address, self.mask
        )

    def __eq__(self, cmd):
        if not isinstance(cmd, CmdCheckData):
            return False
        if self.bytes != cmd.bytes or \
           self.ops != cmd.ops or \
           self.address != cmd.address or \
           self.mask != cmd.mask or \
           self.count != cmd.count:
            return False
        return True

    def info(self):
        msg  = "-" * 60 + "\n"
        msg += "Check Data Command (Ops: {0:s}, Bytes: {1:d})\n".format(EnumCheckOps[self.ops], self.bytes)
        msg += "-" * 60 + "\n"
        msg += "- Address: 0x{0:08X}, Mask: 0x{1:08X}".format(self._address, self._mask)
        if self.count:
            msg += ", Count: {0:d}".format(self._count)
        msg += "\n"
        return msg

    def export(self):
        self._header.length = self.size
        raw_data = self._header.export()
        raw_data += pack(">LL", self._address, self._mask)
        if self._count is not None:
            raw_data += pack(">L", self._count)
        return raw_data

    @classmethod
    def parse(cls, data, offset=0):
        header = Header.parse(data, offset, CmdTag.CHK_DAT)
        bytes = header.param & 0x7
        ops = (header.param >> 3) & 0x3
        address, mask = unpack_from(">LL", data, offset + header.size)
        count = None
        if (header.length - header.size) > 8:
            count = unpack_from(">L", data, offset + header.size + 8)[0]
        return cls(bytes, ops, address, mask, count)


class CmdNop(CmdBase):
    """ Nop command """

    def __init__(self, param=0):
        super().__init__(CmdTag.NOP, param)

    def __repr__(self):
        return "CmdNop"

    def __eq__(self, cmd):
        if not isinstance(cmd, CmdNop):
            return False
        return True

    def info(self):
        msg = "-" * 60 + "\n"
        msg += "NOP Command\n"
        msg += "-" * 60 + "\n"
        return msg

    def export(self):
        return self._header.export()

    @classmethod
    def parse(cls, data, offset=0):
        header = Header.parse(data, offset, CmdTag.NOP)
        if header.length != header.size:
            pass
        return cls(header.param)


class CmdSet(CmdBase):
    """ Set command """

    @property
    def itm(self):
        return self._header.param

    @itm.setter
    def itm(self, value):
        assert EnumItm.is_valid(value)
        self._header.param = int(value)

    @property
    def hash_algorithm(self):
        return self._hash_alg

    @hash_algorithm.setter
    def hash_algorithm(self, value):
        assert EnumAlgorithm.is_valid(value)
        self._hash_alg = int(value)

    @property
    def engine(self):
        return self._engine

    @engine.setter
    def engine(self, value):
        assert EnumEngine.is_valid(value)
        self._engine = int(value)

    @property
    def engine_cfg(self):
        return self._engine_cfg

    @engine_cfg.setter
    def engine_cfg(self, value):
        self._engine_cfg = value

    def __init__(self, itm=EnumItm.ENG, hash_alg=0, engine=0, engine_cfg=0):
        assert EnumItm.is_valid(itm)
        super().__init__(CmdTag.SET, itm)
        self.hash_algorithm = hash_alg
        self.engine = engine
        self.engine_cfg = engine_cfg
        self._header.length = Header.SIZE + 4

    def __repr__(self):
        return "CmdSet <{}, {}, {}, 0x{:X}>".format(
            EnumItm[self.itm], EnumAlgorithm[self.hash_algorithm], EnumEngine[self.engine], self.engine_cfg
        )

    def __eq__(self, cmd):
        if not isinstance(cmd, CmdSet):
            return False
        if self.size != cmd.size or self.itm != cmd.itm or self.hash_algorithm != cmd.hash_algorithm or \
           self.engine != cmd.engine or self.engine_cfg != cmd.engine_cfg:
            return False
        return True

    def info(self):
        msg  = "-" * 60 + "\n"
        msg += "Set Command (ITM: {0:s})\n".format(EnumItm[self.itm])
        msg += "HASH Algo:  {})\n".format(self.hash_algorithm)
        msg += "Engine:     {})\n".format(self.engine)
        msg += "Engine Conf:{})\n".format(self.engine_cfg)
        msg += "-" * 60 + "\n"
        return msg

    def export(self):
        raw_data = self._header.export()
        raw_data += pack("4B", 0x00, self.hash_algorithm, self.engine, self.engine_cfg)
        return raw_data

    @classmethod
    def parse(cls, data, offset=0):
        header = Header.parse(data, offset, CmdTag.SET)
        (_, alg, eng, cfg) = unpack_from("4B", data, offset + Header.SIZE)
        return cls(header.param, alg, eng, cfg)


class CmdInitialize(CmdBase):
    """ Initialize command """

    @property
    def engine(self):
        return self._header.param

    @engine.setter
    def engine(self, value):
        assert EnumEngine.is_valid(value)
        self._header.param = int(value)

    def __init__(self, engine=EnumEngine.ANY, data=None):
        assert EnumEngine.is_valid(engine)
        super().__init__(CmdTag.INIT, engine)
        self._data = data if data else []

    def __repr__(self):
        return "CmdInitialize <{}, {}>".format(
            EnumEngine[self.engine], len(self._data)
        )

    def __eq__(self, cmd):
        if not isinstance(cmd, CmdInitialize):
            return False
        if self.size != cmd.size or self.engine != cmd.engine:
            return False
        # TODO: Compare data
        return True

    def __len__(self):
        len(self._data)

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value

    def __iter__(self):
        return self._data.__iter__()

    def info(self):
        msg  = "-" * 60 + "\n"
        msg += "Initialize Command (Engine: {0:s})\n".format(EnumEngine[self.engine])
        msg += "-" * 60 + "\n"
        cnt = 0
        for val in self._data:
            msg += " {0:02d}) Value: 0x{1:08X}\n".format(cnt, val)
            cnt += 1
        return msg

    def append(self, value):
        assert type(value) is int, "value must be INT type"
        assert 0 <= value < 0xFFFFFFFF, "value out of range"
        self._data.append(value)
        self._header.length += 4

    def pop(self, index):
        assert 0 <= index < len(self._data)
        val = self._data.pop(index)
        self._header.length -= 4
        return val

    def clear(self):
        self._data.clear()
        self._header.length = self._header.size

    def export(self):
        raw_data = self._header.export()
        for val in self._data:
            raw_data += pack(">L", val)
        return raw_data

    @classmethod
    def parse(cls, data, offset=0):
        header = Header.parse(data, offset, CmdTag.INIT)
        obj = cls(header.param)
        index = header.size
        while index < header.length:
            assert (offset + index) < len(data)
            val = unpack_from(">L", data, offset + index)
            obj.append(val[0])
            index += 4
        return obj


class CmdUnlock(CmdBase):
    """ Unlock engine command """

    @property
    def engine(self):
        return self._header.param

    @engine.setter
    def engine(self, value):
        assert EnumEngine.is_valid(value)
        self._header.param = int(value)

    def __init__(self, engine=EnumEngine.ANY, features=0, uid=0):
        assert EnumEngine.is_valid(engine)
        super().__init__(CmdTag.UNLK, engine)
        self.features = features
        self.uid = uid
        self._header.length = Header.SIZE + 12

    def __repr__(self):
        return "CmdUnlock <{}, {}, {}>".format(
            EnumEngine[self.engine], self.features, self.uid
        )

    def __eq__(self, cmd):
        if not isinstance(cmd, CmdUnlock):
            return False
        if self.size != cmd.size or self.engine != cmd.engine or self.features != cmd.features or self.uid != cmd.uid:
            return False
        return True

    def info(self):
        msg  = "-" * 60 + "\n"
        msg += "Unlock Command (Engine: {:s})\n".format(EnumEngine[self.engine])
        msg += "Features: {})\n".format(self.features)
        msg += "UID:      {})\n".format(self.uid)
        msg += "-" * 60 + "\n"
        return msg

    def export(self):
        self._header.length = self.size
        raw_data = self._header.export()
        raw_data += pack(">LQ", self.features, self.uid)
        return raw_data

    @classmethod
    def parse(cls, data, offset=0):
        header = Header.parse(data, offset, CmdTag.UNLK)
        features, uid = unpack_from(">LQ", data, offset + header.size)
        obj = cls(header.param, features, uid)
        return obj


class CmdInstallKey(CmdBase):
    """ Install key command """

    @property
    def flags(self):
        return self._header.param

    @flags.setter
    def flags(self, value):
        assert EnumInsKey.is_valid(value)
        self._header.param = int(value)

    @property
    def certificate_format(self):
        return self._cert_fmt

    @certificate_format.setter
    def certificate_format(self, value):
        assert EnumCertFormat.is_valid(value)
        self._cert_fmt = int(value)

    @property
    def hash_algorithm(self):
        return self._hash_alg

    @hash_algorithm.setter
    def hash_algorithm(self, value):
        assert EnumAlgorithm.is_valid(value)
        self._hash_alg = int(value)

    @property
    def source_index(self):
        return self._src_index

    @source_index.setter
    def source_index(self, value):
        assert value in (0, 2, 3, 4, 5)
        self._src_index = int(value)

    @property
    def target_index(self):
        return self._tgt_index

    @target_index.setter
    def target_index(self, value):
        assert value in (0, 1, 2, 3, 4, 5)
        self._tgt_index = int(value)

    def __init__(self, flags=EnumInsKey.CLR, cert_fmt=EnumCertFormat.SRK, hash_alg=EnumAlgorithm.ANY,
                 src_index=0, tgt_index=0, location=0):
        super().__init__(CmdTag.INS_KEY, flags)
        self.certificate_format = cert_fmt
        self.hash_algorithm = hash_alg
        self.source_index = src_index
        self.target_index = tgt_index
        self.key_location = location
        self._header.length = Header.SIZE + 8

    def __repr__(self):
        return "CmdInstallKey <{}, {}, {}, {}, {}, 0x{:X}>".format(
            EnumInsKey[self.flags], EnumCertFormat[self.certificate_format], EnumAlgorithm[self.hash_algorithm],
            self.source_index, self.target_index, self.key_location
        )

    def __eq__(self, cmd):
        if not isinstance(cmd, CmdInstallKey):
            return False
        if self.size != cmd.size or \
           self.flags != cmd.flags or \
           self.certificate_format != cmd.certificate_format or \
           self.hash_algorithm != cmd.hash_algorithm or \
           self.source_index != cmd.source_index or \
           self.target_index != cmd.target_index or \
           self.key_location != cmd.key_location:
            return False
        return True

    def info(self):
        msg = "-" * 60 + "\n"
        msg += "Install Key Command\n"
        msg += " Flag:    {:d} ({})\n".format(self.flags, EnumInsKey.desc(self.flags))
        msg += " Prot:    {:d} ({})\n".format(self.certificate_format, EnumCertFormat.desc(self.certificate_format))
        msg += " Algo:    {:d} ({})\n".format(self.hash_algorithm, EnumAlgorithm.desc(self.hash_algorithm))
        msg += " SrcKey:  {:d} (Source key index) \n".format(self.source_index)
        msg += " TgtKey:  {:d} (Target key index) \n".format(self.target_index)
        msg += " Location:0x{:08X} (Start address of key data to install) \n".format(self.key_location)
        msg += "-" * 60 + "\n"
        return msg

    def export(self):
        raw_data = self._header.export()
        raw_data += pack(">4BL", self.certificate_format, self.hash_algorithm, self.source_index, self.target_index,
                         self.key_location)
        return raw_data

    @classmethod
    def parse(cls, data, offset=0):
        header = Header.parse(data, offset, CmdTag.INS_KEY)
        protocol, algorithm, src_index, tgt_index, location = unpack_from(">4BL", data, offset + header.size)
        return cls(header.param, protocol, algorithm, src_index, tgt_index, location)


class CmdAuthData(CmdBase):
    """ Authenticate data command """

    @property
    def flags(self):
        return self._header.param

    @flags.setter
    def flags(self, value):
        assert EnumAuthDat.is_valid(value)
        self._header.param = int(value)

    @property
    def key_index(self):
        return self._key_index

    @key_index.setter
    def key_index(self, value):
        assert value in (1, 2, 3, 4, 5)
        self._key_index = value

    @property
    def engine(self):
        return self._engine

    @engine.setter
    def engine(self, value):
        assert EnumEngine.is_valid(value)
        self._engine = int(value)

    @property
    def engine_cfg(self):
        return self._engine_cfg

    @engine_cfg.setter
    def engine_cfg(self, value):
        self._engine_cfg = value

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, value):
        self._location = value

    def __init__(self, flags=EnumAuthDat.CLR, key_index=1, engine=EnumEngine.ANY, engine_cfg=0, location=0):
        super().__init__(CmdTag.AUT_DAT, flags)
        self.key_index = key_index
        self.sig_format = 0xC5
        self.engine = engine
        self.engine_cfg = engine_cfg
        self.location = location
        self._header.length = Header.SIZE + 8
        self._blocks = []

    def __repr__(self):
        return "CmdAuthData <{}, {}, {}, key:{}, 0x{:X}>".format(
            EnumAuthDat[self.flags], EnumEngine[self.engine], self.engine_cfg, self.key_index, self.location
        )

    def __eq__(self, cmd):
        if not isinstance(cmd, CmdAuthData):
            return False
        if self.size != cmd.size or self.flags != cmd.flags or self.key_index != cmd.key_index or \
           self.engine != cmd.engine or self.engine_cfg != cmd.engine_cfg or self.location != cmd.location:
            return False
        for item in cmd:
            if item not in self._blocks:
                return False
        return True

    def __len__(self):
        len(self._blocks)

    def __getitem__(self, key):
        return self._blocks[key]

    def __setitem__(self, key, value):
        assert isinstance(value, (list, tuple))
        assert len(value) == 2
        self._blocks[key] = value

    def __iter__(self):
        return self._blocks.__iter__()

    def info(self):
        msg = "-" * 60 + "\n"
        msg += "Auth Data Command\n"
        msg += " Flag:        {:d} ({})\n".format(self.flags, EnumAuthDat.desc(self.flags))
        msg += " Key index:   {:d}\n".format(self.key_index)
        msg += " Engine:      {:d} ({})\n".format(self.engine, EnumEngine.desc(self.engine))
        msg += " Engine Conf: {:d}\n".format(self.engine_cfg)
        msg += " Location:    0x{:08X} (Start address of authentication data) \n".format(self.location)
        msg += "-" * 60 + "\n"
        for blk in self._blocks:
            msg += "- Start: 0x{0:08X}, Length: {1:d} Bytes\n".format(blk[0], blk[1])
        return msg

    def append(self, start_address, size):
        self._blocks.append([start_address, size])
        self._header.length += 8

    def pop(self, index):
        assert 0 <= index < len(self._blocks)
        value = self._blocks.pop(index)
        self._header.length -= 8
        return value

    def clear(self):
        self._blocks.clear()
        self._header.length = self._header.size + 8

    def export(self):
        self._header.length = self.size
        raw_data = self._header.export()
        raw_data += pack(">4BL", self.key_index, self.sig_format, self.engine, self.engine_cfg, self.location)
        for blk in self._blocks:
            raw_data += pack(">2L", blk[0], blk[1])
        return raw_data

    @classmethod
    def parse(cls, data, offset=0):
        header = Header.parse(data, offset, CmdTag.AUT_DAT)
        key, sf, eng, cfg, location = unpack_from(">4BL", data, offset + header.size)
        obj = cls(header.param, key, eng, cfg, location)
        obj.sig_format = sf
        index = header.size + 8
        while index < header.length:
            start_address, size = unpack_from(">2L", data, offset + index)
            obj.append(start_address, size)
            index += 8
        return obj
