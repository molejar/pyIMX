# Copyright (c) 2017-2018 Martin Olejar
#
# SPDX-License-Identifier: BSD-3-Clause
# The BSD-3-Clause license for this file can be found in the LICENSE file included with this distribution
# or at https://spdx.org/licenses/BSD-3-Clause.html#licenseText

from enum import Enum, unique
from struct import pack, unpack_from

from .header import CmdTag, Header


########################################################################################################################
## Custom Types
########################################################################################################################


class IntEnum(int, Enum):
    @classmethod
    def check_value(cls, value):
        for n, v in cls.__members__.items():
            if int(value) == int(v):
                return True
        return False

    @classmethod
    def str_to_value(cls, name):
        for n, v in cls.__members__.items():
            if name.upper() == n:
                return int(v)
        raise ValueError("Unsupported name: %s" % name)

    @classmethod
    def value_to_str(cls, value):
        for n, v in cls.__members__.items():
            if int(value) == int(v):
                return n
        return "0x{0:08X}".format(value)

    @classmethod
    def get_names(cls, lower=False):
        if lower:
            return [x.lower() for x in cls.__members__.keys()]
        else:
            return cls.__members__.keys()

    @classmethod
    def get_items(cls):
        items = {}
        for n, v in cls.__members__.items():
            items[n] = int(v)
        return items


########################################################################################################################
## Enums
########################################################################################################################

@unique
class EnumWriteOps(IntEnum):
    ''' help '''
    WRITE_VALUE = 0
    WRITE_VALUE1 = 1
    CLEAR_BITMASK = 2
    SET_BITMASK = 3


@unique
class EnumCheckOps(IntEnum):
    ''' help '''
    ALL_CLEAR = 0
    ALL_SET = 1
    ANY_CLEAR = 2
    ANY_SET = 3


@unique
class EnumAlgorithm(IntEnum):
    ''' Algorithm types '''
    ANY    = 0x00  # Algorithm type ANY
    HASH   = 0x01  # Hash algorithm type
    SIG    = 0x02  # Signature algorithm type
    F      = 0x03  # Finite field arithmetic
    EC     = 0x04  # Elliptic curve arithmetic
    CIPHER = 0x05  # Cipher algorithm type
    MODE   = 0x06  # Cipher/hash modes
    WRAP   = 0x07  # Key wrap algorithm type
    # Hash algorithms
    SHA1   = 0x11  # SHA-1 algorithm ID
    SHA256 = 0x17  # SHA-256 algorithm ID
    SHA512 = 0x1b  # SHA-512 algorithm ID
    # Signature algorithms
    PKCS1  = 0x21  # PKCS#1 RSA signature algorithm
    # Cipher algorithms
    AES    = 0x55  # AES algorithm ID
    # Cipher or hash modes
    CCM    = 0x66  # Counter with CBC-MAC
    # Key wrap algorithms
    BLOB   = 0x71  # SHW-specific key wrap


@unique
class EnumProtocol(IntEnum):
    ''' Protocol tags '''
    SRK  = 0x03  # SRK certificate format
    X509 = 0x09  # X.509v3 certificate format
    CMS  = 0xC5  # CMS/PKCS#7 signature format
    BLOB = 0xBB  # SHW-specific wrapped key format
    AEAD = 0xA3  # Proprietary AEAD MAC format


@unique
class EnumInsKey(IntEnum):
    ''' Command tags '''
    CLR = 0    #
    ABS = 1    #
    CSF = 2    #
    DAT = 4    #
    CFG = 8    #
    FID = 16   #
    MID = 32   #
    CID = 64   #
    HSH = 128  #


@unique
class EnumAuthDat(IntEnum):
    ''' help '''
    CLR = 0
    ABS = 1


@unique
class EnumEngine(IntEnum):
    ''' Engine plugin tags '''
    ANY    = 0x00  # First compatible engine will be selected (no engine configuration parameters are allowed)
    SCC    = 0x03  # Security controller
    RTIC   = 0x05  # Run-time integrity checker
    SAHARA = 0x06  #
    CSU    = 0x0A
    SRTC   = 0x0C
    DCP    = 0x1B
    CAAM   = 0x1D
    SNVS   = 0x1E
    OCOTP  = 0x21
    DTCP   = 0x22
    ROM    = 0x36
    HDCP   = 0x24
    SW     = 0xFF


@unique
class EnumItm(IntEnum):
    ''' help '''
    MID = 0x01
    ENG = 0x03


########################################################################################################################
## HAB Commands
########################################################################################################################

class CmdBase(object):

    def __str__(self):
        return self.info()

    def __repr__(self):
        return self.info()

    def info(self):
        pass


class CmdWriteData(object):
    ''' Write data command '''

    @property
    def bytes(self):
        return self._header.param & 0x7

    @bytes.setter
    def bytes(self, value):
        assert value in (1, 2, 4), "Unsupported Value !"
        self._header.param &= ~0x7
        self._header.param |= value

    @property
    def ops(self):
        return (self._header.param >> 3) & 0x3

    @ops.setter
    def ops(self, value):
        assert EnumWriteOps.check_value(value), "Unsupported Value !"
        self._header.param &= ~(0x3 << 3)
        self._header.param |= int(value) << 3

    @property
    def size(self):
        return self._header.length

    def __init__(self, bytes=4, ops=EnumWriteOps.WRITE_VALUE):
        assert bytes in (1, 2, 4), "Unsupported Value !"
        assert EnumWriteOps.check_value(ops), "Unsupported Value !"
        self._header = Header(tag=CmdTag.WRT_DAT, param=((int(ops) & 0x3) << 3) | (bytes & 0x7))
        self._data = []

    def __str__(self):
        return self.info()

    def __repr__(self):
        return self.info()

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
        msg += "Write Data Command (Ops: {0:s}, Bytes: {1:d})\n".format(EnumWriteOps.value_to_str(self.ops), self.bytes)
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


class CmdCheckData(object):
    ''' Check data command '''

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
        assert EnumCheckOps.check_value(value), "Unsupported value !"
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
        assert EnumCheckOps.check_value(ops), "Unsupported value !"
        self._header = Header(tag=CmdTag.CHK_DAT, param=((int(ops) & 0x3) << 3) | (bytes & 0x7))
        self._address = address
        self._mask = mask
        self._count = count

    def __str__(self):
        return self.info()

    def __repr__(self):
        return self.info()

    def info(self):
        msg  = "-" * 60 + "\n"
        msg += "Check Data Command (Ops: {0:s}, Bytes: {1:d})\n".format(EnumCheckOps.value_to_str(self.ops), self.bytes)
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
            raw_data += pack(">L",self._count)
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


class CmdNop(object):
    ''' Nop command '''

    @property
    def size(self):
        return self._header.length

    def __init__(self, param=0):
        self._header = Header(tag=CmdTag.NOP, param=param)

    def __str__(self):
        return self.info()

    def __repr__(self):
        return self.info()

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


class CmdSet(object):
    ''' Set command '''

    @property
    def itm(self):
        return self._header.param

    @itm.setter
    def itm(self, value):
        assert EnumItm.check_value(value), "uncorrected value !"
        self._header.param = int(value)

    @property
    def size(self):
        return self._header.length

    def __init__(self, itm=EnumItm.ENG, data=None):
        assert EnumItm.check_value(itm), "uncorrected value !"
        self._header = Header(tag=CmdTag.SET, param=itm)
        self._data = data if data else []

    def __str__(self):
        return self.info()

    def __repr__(self):
        return self.info()

    def info(self):
        msg  = "-" * 60 + "\n"
        msg += "Set Command (ITM: {0:s})\n".format(EnumItm.value_to_str(self.itm))
        msg += "-" * 60 + "\n"
        for cmd in self._data:
            msg += "- ALG: {0:s}, ENG: {1:s}, CFG: {2:d}\n".format(EnumAlgorithm.value_to_str(cmd[0]),
                                                                   EnumEngine.value_to_str(cmd[1]), cmd[2])
        return msg

    def append(self, alg, eng, cfg):
        assert EnumAlgorithm.check_value(alg), "uncorrected value !"
        assert EnumEngine.check_value(eng), "uncorrected value !"
        assert type(cfg) is int, "cfg value must be INT type"
        assert 0 <= cfg < 256, "cfg value out of range"
        self._data.append([alg, eng, cfg])
        self._header.length += 4

    def pop(self, index):
        assert 0 <= index < len(self._data)
        cmd = self._data.pop(index)
        self._header.length -= 4
        return cmd

    def clear(self):
        self._data.clear()
        self._header.length = self._header.size

    def export(self):
        raw_data = self._header.export()
        for cmd in self._data:
            raw_data += pack("4B", 0x00, cmd[0], cmd[1], cmd[2])
        return raw_data

    @classmethod
    def parse(cls, data, offset=0):
        header = Header.parse(data, offset, CmdTag.SET)
        obj = cls(header.param)
        index = header.size
        while index < header.length:
            (_, alg, eng, cfg) = unpack_from("4B", data, offset + index)
            obj.append(alg, eng, cfg)
            index += 4
        return obj


class CmdInitialize(object):
    ''' Initialize command '''

    @property
    def engine(self):
        return self._header.param

    @engine.setter
    def engine(self, value):
        assert EnumEngine.check_value(value), "uncorrected value !"
        self._header.param = int(value)

    @property
    def size(self):
        return self._header.length

    def __init__(self, engine=EnumEngine.ANY, data=None):
        assert EnumEngine.check_value(engine), "uncorrected value !"
        self._header = Header(tag=CmdTag.INIT, param=engine)
        self._data = data if data else []

    def __str__(self):
        return self.info()

    def __repr__(self):
        return self.info()

    def info(self):
        msg  = "-" * 60 + "\n"
        msg += "Initialize Command (Engine: {0:s})\n".format(EnumEngine.value_to_str(self.engine))
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


class CmdUnlock(object):
    ''' Unlock engine command '''

    @property
    def engine(self):
        return self._header.param

    @engine.setter
    def engine(self, value):
        assert EnumEngine.check_value(value), "uncorrected value !"
        self._header.param = int(value)

    @property
    def size(self):
        return self._header.size + len(self._data) * 4

    def __init__(self, engine = EnumEngine.ANY, data=None):
        assert EnumEngine.check_value(engine), "uncorrected value !"
        self._header = Header(tag=CmdTag.UNLK, param=engine)
        self._data = data if data else []

    def __str__(self):
        return self.info()

    def __repr__(self):
        return self.info()

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
        msg += "Unlock Command (Engine: {0:s})\n".format(EnumEngine.value_to_str(self.engine))
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

    def pop(self, index):
        assert 0 <= index < len(self._data)
        val = self._data.pop(index)
        return val

    def clear(self):
        self._data.clear()

    def export(self):
        self._header.length = self.size
        raw_data = self._header.export()
        for val in self._data:
            raw_data += pack(">L", val)
        return raw_data

    @classmethod
    def parse(cls, data, offset=0):
        header = Header.parse(data, offset, CmdTag.UNLK)
        obj = cls(header.param)
        index = header.size
        while index < header.length:
            assert (offset + index) < len(data)
            val = unpack_from(">L", data, offset + index)
            obj.append(val[0])
            index += 4
        return obj


class CmdInstallKey(object):
    ''' Install key command '''
    @property
    def param(self):
        return self._header.param

    @param.setter
    def param(self, value):
        assert EnumInsKey.check_value(value), "uncorrected value !"
        self._header.param = int(value)

    @property
    def pcl(self):
        return self._pcl

    @pcl.setter
    def pcl(self, value):
        assert EnumProtocol.check_value(value), "uncorrected value !"
        self._pcl = int(value)

    @property
    def alg(self):
        return self._alg

    @alg.setter
    def alg(self, value):
        assert EnumAlgorithm.check_value(value), "uncorrected value !"
        self._alg = int(value)

    @property
    def src(self):
        return self._src

    @src.setter
    def src(self, value):
        self._src = value

    @property
    def tgt(self):
        return self._tgt

    @tgt.setter
    def tgt(self, value):
        self._tgt = value

    @property
    def keydat(self):
        return self._keydat

    @keydat.setter
    def keydat(self, value):
        self._keydat = value

    @property
    def size(self):
        return self._header.size + 8 + len(self._crthsh)

    def __init__(self, param=EnumInsKey.CLR,
                 pcl=EnumProtocol.SRK,
                 alg=EnumAlgorithm.ANY,
                 src=0,
                 tgt=0,
                 keydat=0,
                 crthsh=None):
        self._header = Header(tag=CmdTag.INS_KEY, param=param)
        self.pcl = pcl
        self.alg = alg
        self.src = src
        self.tgt = tgt
        self._keydat = keydat
        self._crthsh = [] if crthsh is None else crthsh

    def __str__(self):
        return self.info()

    def __repr__(self):
        return self.info()

    def info(self):
        msg = "-" * 60 + "\n"
        msg += "Install Key Command\n"
        msg += " Flag:   {0:s}\n".format(EnumInsKey.value_to_str(self.param))
        msg += " Prot:   {0:s}\n".format(EnumProtocol.value_to_str(self.pcl))
        msg += " Algo:   {0:s}\n".format(EnumAlgorithm.value_to_str(self.alg))
        msg += " SrcKey: {0:d} (Source key index) \n".format(self.src)
        msg += " TgtKey: {0:d} (Target key index) \n".format(self.tgt)
        msg += " Addr:   0x{0:08X} (Start address of key data to install) \n".format(self.keydat)
        msg += "-" * 60 + "\n"
        return msg

    def export(self):
        self._header.length = self.size
        raw_data = self._header.export()
        raw_data += pack(">BBBBL", self.pcl, self.alg, self.src, self.tgt, self.keydat)
        raw_data += self._crthsh
        return raw_data

    @classmethod
    def parse(cls, data, offset=0):
        header = Header.parse(data, offset, CmdTag.INS_KEY)
        pcl, alg, src, tgt, keydat = unpack_from(">BBBBL", data, offset + header.size)
        crthsh = data[offset + header.size + 8 : offset + header.size + 8 + header.length]
        return cls(header.param, pcl, alg, src, tgt, keydat, crthsh)


class CmdAuthData(object):
    ''' write here Doc '''
    @property
    def flag(self):
        return self._header.param

    @flag.setter
    def flag(self, value):
        assert EnumAuthDat.check_value(value), "uncorrected value !"
        self._header.param = int(value)

    @property
    def key(self):
        return self._key

    @key.setter
    def key(self, value):
        self._key = value

    @property
    def pcl(self):
        return self._pcl

    @pcl.setter
    def pcl(self, value):
        assert EnumProtocol.check_value(value), "uncorrected value !"
        self._pcl = int(value)

    @property
    def eng(self):
        return self._eng

    @eng.setter
    def eng(self, value):
        assert EnumEngine.check_value(value), "uncorrected value !"
        self._eng = int(value)

    @property
    def cfg(self):
        return self._cfg

    @cfg.setter
    def cfg(self, value):
        self._cfg = value

    @property
    def auth_start(self):
        return self._auth_start

    @auth_start.setter
    def auth_start(self, value):
        self._auth_start = value

    @property
    def auth_data(self):
        return self._auth_data

    @auth_data.setter
    def auth_data(self, value):
        self._auth_data = value

    @property
    def size(self):
        return self._header.size + 8 + 8 * len(self._blocks)

    def __init__(self, flag=EnumAuthDat.CLR, key=0, pcl=EnumProtocol.SRK, eng=EnumEngine.ANY, cfg=0, auth_start=0,
                 auth_data=None):
        self._header = Header(CmdTag.AUT_DAT, flag)
        self.key = key
        self.pcl = pcl
        self.eng = eng
        self.cfg = cfg
        self.auth_start = auth_start
        self.auth_data = auth_data
        self._blocks = []

    def __str__(self):
        return self.info()

    def __repr__(self):
        return self.info()

    def info(self):
        msg = "-" * 60 + "\n"
        msg += "Auth Data Command\n"
        msg += " Flag:   {0:s}\n".format(EnumAuthDat.value_to_str(self._header.param))
        msg += " Prot:   {0:s}\n".format(EnumProtocol.value_to_str(self.pcl))
        msg += " Engine: {0:s}\n".format(EnumEngine.value_to_str(self.eng))
        msg += " Key:    {0:d} (Key index)\n".format(self.key)
        msg += " Conf:   {0:d} (Configuration)\n".format(self.cfg)
        msg += " Addr:   0x{0:08X} (Start address of authentication data) \n".format(self.auth_start)
        msg += "-" * 60 + "\n"
        for blk in self._blocks:
            msg += "- Start: 0x{0:08X}, Length: {1:d} Bytes\n".format(blk[0], blk[1])
        return msg

    def append(self, start_address, size):
        self._blocks.append([start_address, size])

    def pop(self, index):
        assert 0 <= index < len(self._blocks)
        return self._blocks.pop(index)

    def clear(self):
        self._blocks.clear()

    def export(self):
        self._header.length = self.size
        raw_data  = self._header.export()
        raw_data += pack(">BBBBL", self.key, self.pcl, self.eng, self.cfg, self.auth_start)
        for blk in self._blocks:
            raw_data += pack(">2L", blk[0], blk[1])
        return raw_data

    @classmethod
    def parse(cls, data, offset=0):
        header = Header.parse(data, offset, CmdTag.AUT_DAT)
        key, pcl, eng, cfg, auth_start = unpack_from(">BBBBL", data, offset + header.size)
        obj = cls(header.param, key, pcl, eng, cfg, auth_start)
        index = header.size + 8
        while offset < header.length:
            start_address, size = unpack_from(">2L", data, offset + index)
            obj.append(start_address, size)
            index += 8
        return obj
