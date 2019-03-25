# Copyright (c) 2017-2018 Martin Olejar
#
# SPDX-License-Identifier: BSD-3-Clause
# The BSD-3-Clause license for this file can be found in the LICENSE file included with this distribution
# or at https://spdx.org/licenses/BSD-3-Clause.html#licenseText

from struct import pack, unpack_from, calcsize

from .header import Header, Header2, SegTag, UnparsedException, CorruptedException
from .commands import CmdWriteData, CmdCheckData, CmdNop, CmdSet, CmdInitialize, CmdUnlock, CmdInstallKey, CmdAuthData,\
                      EnumWriteOps, EnumCheckOps, EnumEngine
from .secret import SecretKeyBlob, Certificate, Signature
from .misc import sizeof_fmt


########################################################################################################################
# Base Segment Class
########################################################################################################################


class BaseSegment(object):
    """ base segment """

    # padding fill value
    PADDING_VALUE = 0x00

    @property
    def padding(self):
        return self._padding

    @padding.setter
    def padding(self, value):
        self._padding = value

    @property
    def space(self):
        return self.size + self.padding

    @property
    def size(self):
        return 0

    def _padding_export(self):
        return bytes([self.PADDING_VALUE] * self._padding) if self._padding > 0 else b''

    def __init__(self):
        self._padding = 0

    def __ne__(self, obj):
        return not self.__eq__(obj)

    def __str__(self):
        return self.info()

    def __repr__(self):
        return self.info()

    def info(self):
        """ object info """
        raise NotImplementedError()

    def export(self, padding=False):
        """ export interface """
        raise NotImplementedError()

    @classmethod
    def parse(cls, buffer):
        """ parse interface """
        raise NotImplementedError()

########################################################################################################################
# Boot Image V1 Segments (i.MX5)
########################################################################################################################

# Obsolete, will not be implemented


########################################################################################################################
# Boot Image V2 Segments (i.MX6, i.MX7, i.MX8M)
########################################################################################################################

class SegIVT2(BaseSegment):
    """ IVT2 segment """

    FORMAT = '<7L'
    SIZE = Header.SIZE + calcsize(FORMAT)

    @property
    def version(self):
        return self._header.param

    @version.setter
    def version(self, value):
        assert 0x40 <= value < 0x4F
        self._header.param = value

    @property
    def size(self):
        return self._header.length

    def __init__(self, version):
        """ Initialize IVT2 segment
        :param version: The version of IVT and Image format
        """
        super().__init__()
        self._header = Header(SegTag.IVT2, version)
        self._header.length = self.SIZE
        self.app_address = 0
        self.rs1 = 0
        self.dcd_address = 0
        self.bdt_address = 0
        self.ivt_address = 0
        self.csf_address = 0
        self.rs2 = 0

    def __eq__(self, obj):
        if not isinstance(obj, SegIVT2):
            return False
        if self.size != obj.size or \
           self.version != obj.version or \
           self.app_address != obj.app_address or \
           self.dcd_address != obj.dcd_address or \
           self.bdt_address != obj.bdt_address or \
           self.ivt_address != obj.ivt_address or \
           self.csf_address != obj.csf_address:
            return False
        return True

    def info(self):
        msg = ""
        msg += " IVT: 0x{:08X}\n".format(self.ivt_address)
        msg += " BDT: 0x{:08X}\n".format(self.bdt_address)
        msg += " DCD: 0x{:08X}\n".format(self.dcd_address)
        msg += " APP: 0x{:08X}\n".format(self.app_address)
        msg += " CSF: 0x{:08X}\n".format(self.csf_address)
        msg += "\n"
        return msg

    def validate(self):
        if self.ivt_address == 0 or self.bdt_address == 0 or self.bdt_address < self.ivt_address:
            raise ValueError("Not valid IVT/BDT address")
        if self.dcd_address and self.dcd_address < self.ivt_address:
            raise ValueError("Not valid DCD address: 0x{:X} < 0x{:X}".format(self.dcd_address, self.ivt_address))
#        if self.app_address and self.app_address < self.ivt_address:
#            raise ValueError("Not valid APP address: 0x{:X} < 0x{:X}".format(self.app_address, self.ivt_address))
        if self.csf_address and self.csf_address < self.ivt_address:
            raise ValueError("Not valid CSF address: 0x{:X} < 0x{:X}".format(self.csf_address, self.ivt_address))
        if self.padding > 0:
            raise ValueError("IVT padding should be zero: {}".format(self.padding))

    def export(self, padding=False):
        """ Export segment as bytes array
        :param padding: True if use padding (default: False)
        :return: bytes
        """
        self.validate()

        data = self._header.export()
        data += pack(self.FORMAT, self.app_address, self.rs1, self.dcd_address, self.bdt_address, self.ivt_address,
                     self.csf_address, self.rs2)
        if padding:
            data += self._padding_export()

        return data

    @classmethod
    def parse(cls, data):
        """ Parse segment from bytes array
        :param data: The bytes array of IVT2 segment
        :return SegIVT2 object
        """
        header = Header.parse(data, 0, SegTag.IVT2)
        obj = cls(header.param)
        # Parse IVT items
        (obj.app_address,
         obj.rs1,
         obj.dcd_address,
         obj.bdt_address,
         obj.ivt_address,
         obj.csf_address,
         obj.rs2) = unpack_from(cls.FORMAT, data, header.size)
        # Calculate IVT padding (should be zero)
        obj.padding = obj.bdt_address - obj.ivt_address - obj.size
        # Validate parsed values
        obj.validate()
        return obj


class SegBDT(BaseSegment):
    """ Boot data segment """
    FORMAT = '<3L'
    SIZE = calcsize(FORMAT)

    @property
    def plugin(self):
        return self._plugin

    @plugin.setter
    def plugin(self, value):
        assert value in (0, 1, 2), "Plugin value must be 0 .. 2"
        self._plugin = value

    @property
    def size(self):
        return self.SIZE

    def __init__(self, start=0, length=0, plugin=0):
        """ Initialize BDT segment
        :param int start:
        :param int length:
        :param int plugin: 0 .. 2
        """
        super().__init__()
        self.start  = start
        self.length = length
        self.plugin = plugin

    def __eq__(self, obj):
        if not isinstance(obj, SegBDT):
            return False
        if self.size != obj.size or self.start != obj.start or self.length != obj.length or self.plugin != obj.plugin:
            return False
        return True

    def info(self):
        """ Get info of BDT segment
        :return: string
        """
        msg  = " Start:  0x{0:08X}\n".format(self.start)
        msg += " Length: {0:s} ({1:d} Bytes)\n".format(sizeof_fmt(self.length), self.length)
        msg += " Plugin: {0:s}\n".format('YES' if self.plugin else 'NO')
        msg += "\n"

        return msg

    def export(self, padding=False):
        """ Export segment as bytes array
        :param padding: True if use padding (default: False)
        :return: bytes
        """
        data = pack(self.FORMAT, self.start, self.length, self.plugin)
        if padding:
            data += self._padding_export()

        return data

    @classmethod
    def parse(cls, data):
        """ Parse segment from bytes array
        :param data: The bytes array of BDT segment
        :return SegBDT object
        """
        return cls(*unpack_from(cls.FORMAT, data))


class SegAPP(BaseSegment):
    """ Boot data segment """

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, value):
        assert isinstance(value, (bytes, bytearray))
        self._data = value

    @property
    def size(self):
        return 0 if self._data is None else len(self._data)

    def __init__(self, data=None):
        """ Initialize APP segment
        :param data: bytes
        """
        super().__init__()
        self._data = data

    def __eq__(self, obj):
        if not isinstance(obj, SegAPP):
            return False
        if self._data != obj.data:
            return False
        return True

    def info(self):
        """ Get info of APP segment
        :return: string
        """
        msg  = " Size: {0:d} Bytes\n".format(len(self._data))
        msg += "\n"
        return msg

    def export(self, padding=False):
        """ Export segment as bytes array
        :param padding: True if use padding (default: False)
        :return: bytes
        """
        data = b''
        if self._data:
            data += bytes(self._data)
        if padding:
            data += self._padding_export()
        return data


class SegDCD(BaseSegment):
    """ DCD segment """
    CMD_TYPES = (CmdWriteData, CmdCheckData, CmdNop, CmdUnlock)

    @property
    def header(self):
        return self._header

    @property
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, value):
        self._enabled = value

    @property
    def commands(self):
        return self._commands

    @property
    def size(self):
        return self._header.length if self.enabled else 0

    @property
    def space(self):
        return self.size + self.padding if self.enabled else 0

    def __init__(self, param=0x41, enabled=False):
        super().__init__()
        self._enabled = enabled
        self._header = Header(SegTag.DCD, param)
        self._header.length = self._header.size
        self._commands = []

    def __eq__(self, obj):
        if not isinstance(obj, SegDCD):
            return False
        if len(self._commands) != len(obj):
            return False
        for cmd in obj:
            if cmd not in self._commands:
                return False
        return True

    def __len__(self):
        return len(self._commands)

    def __getitem__(self, key):
        return self._commands[key]

    def __setitem__(self, key, value):
        assert type(value) in self.CMD_TYPES
        self._commands[key] = value

    def __iter__(self):
        return self._commands.__iter__()

    def info(self):
        msg = ""
        for cmd in self._commands:
            msg += str(cmd)
            msg += "\n"
        return msg

    def append(self, cmd):
        assert type(cmd) in self.CMD_TYPES
        self._commands.append(cmd)
        self._header.length += cmd.size

    def pop(self, index):
        assert 0 <= index < len(self._commands)
        cmd = self._commands.pop(index)
        self._header.length -= cmd.size
        return cmd

    def clear(self):
        self._commands.clear()
        self._header.length = self._header.size

    def export_txt(self, txt_data=None):
        write_ops = ('WriteValue', 'WriteValue1', 'ClearBitMask', 'SetBitMask')
        check_ops = ('CheckAllClear', 'CheckAllSet', 'CheckAnyClear', 'CheckAnySet')
        if txt_data is None:
            txt_data = ""

        for cmd in self._commands:
            if type(cmd) is CmdWriteData:
                for (address, value) in cmd:
                    txt_data += "{0:s} {1:d} 0x{2:08X} 0x{3:08X}\n".format(write_ops[cmd.ops],cmd.bytes,address,value)

            elif type(cmd) is CmdCheckData:
                txt_data += "{0:s} {1:d} 0x{2:08X} 0x{3:08X}".format(check_ops[cmd.ops],cmd.bytes,cmd.address,cmd.mask)
                txt_data += "{0:d}\n".format(cmd.count) if cmd.count else "\n"

            elif type(cmd) is CmdUnlock:
                txt_data += "Unlock {0:s}".format(EnumEngine[cmd.engine])
                cnt = 1
                for value in cmd:
                    if cnt > 6:
                        txt_data += " \\\n"
                        cnt = 0
                    txt_data += " 0x{0:08X}".format(value)
                    cnt += 1

                txt_data += '\n'

            else:
                txt_data += "Nop\n"

            # Split with new line every group of commands
            txt_data += '\n'

        return txt_data

    def export(self, padding=False):
        """ Export segment as bytes array
        :param padding: True if use padding (default: False)
        :return: bytes
        """
        data = b''
        if self.enabled:
            data = self._header.export()
            for command in self._commands:
                data += command.export()
            if padding:
                data += self._padding_export()

        return data

    @classmethod
    def parse_txt(cls, text):
        """ Parse segment from text file
        :param text: The string with DCD commands
        :return SegDCD object
        """
        cmds = {
            'WriteValue': ('write', int(EnumWriteOps.WRITE_VALUE)),
            'WriteValue1': ('write', int(EnumWriteOps.WRITE_VALUE1)),
            'ClearBitMask': ('write', int(EnumWriteOps.CLEAR_BITMASK)),
            'SetBitMask': ('write', int(EnumWriteOps.SET_BITMASK)),
            'CheckAllClear': ('check', int(EnumCheckOps.ALL_CLEAR)),
            'CheckAllSet': ('check', int(EnumCheckOps.ALL_SET)),
            'CheckAnyClear': ('check', int(EnumCheckOps.ANY_CLEAR)),
            'CheckAnySet': ('check', int(EnumCheckOps.ANY_SET)),
            'Unlock': None,
            'Nop': None
        }

        line_cnt = 0
        cmd_write = None
        cmd_mline = False
        dcd_obj = cls(enabled=True)

        for line in text.split('\n'):
            line = line.rstrip('\0')
            # increment line counter
            line_cnt += 1
            # ignore comments
            if not line or line.startswith('#'):
                continue
            # check if multi-line command
            if cmd_mline:
                cmd += line.split()
                cmd_mline = False
            else:
                cmd = line.split()
                if cmd[0] not in cmds:
                    continue
            #
            if cmd[-1] == '\\':
                cmd = cmd[:-1]
                cmd_mline = True
                continue
            # ----------------------------
            # Parse command
            # ----------------------------
            if cmd[0] == 'Nop':
                if cmd_write is not None:
                    dcd_obj.append(cmd_write)
                    cmd_write = None

                dcd_obj.append(CmdNop())

            elif cmd[0] == 'Unlock':
                if cmd_write is not None:
                    dcd_obj.append(cmd_write)
                    cmd_write = None

                if not EnumEngine.is_valid(cmd[1]):
                    raise SyntaxError("Unlock CMD: wrong engine parameter at line %d" % (line_cnt - 1))

                engine = EnumEngine[cmd[1]]
                data = [int(value, 0) for value in cmd[2:]]
                dcd_obj.append(CmdUnlock(engine, data))

            elif cmds[cmd[0]][0] == 'write':
                if len(cmd) < 4:
                    raise SyntaxError("Write CMD: not enough arguments at line %d" % (line_cnt - 1))

                ops = cmds[cmd[0]][1]
                bytes = int(cmd[1])
                addr = int(cmd[2], 0)
                value = int(cmd[3], 0)

                if cmd_write is not None:
                    if cmd_write.ops != ops or cmd_write.bytes != bytes:
                        dcd_obj.append(cmd_write)
                        cmd_write = None

                if cmd_write is None:
                    cmd_write = CmdWriteData(bytes, ops)

                cmd_write.append(addr, value)

            else:
                if len(cmd) < 4:
                    raise SyntaxError("Check CMD: not enough arguments at line %d" % (line_cnt - 1))

                if cmd_write is not None:
                    dcd_obj.append(cmd_write)
                    cmd_write = None

                ops = cmds[cmd[0]][1]
                bytes = int(cmd[1])
                addr = int(cmd[2], 0)
                mask = int(cmd[3], 0)
                count = int(cmd[4], 0) if len(cmd) > 4 else None
                dcd_obj.append(CmdCheckData(bytes, ops, addr, mask, count))

        if cmd_write is not None:
            dcd_obj.append(cmd_write)

        return dcd_obj

    @classmethod
    def parse(cls, data):
        """ Parse segment from bytes array
        :param data: The bytes array of DCD segment
        :return SegDCD object
        """
        header = Header.parse(data, 0, SegTag.DCD)
        index = header.size
        obj = cls(header.param, True)
        while index < header.length:
            passed = False
            for cmd_class in cls.CMD_TYPES:
                try:
                    cmd_obj = cmd_class.parse(data, index)
                except UnparsedException:
                    passed = False
                    continue
                obj.append(cmd_obj)
                index += cmd_obj.size
                passed = True
                break
            if not passed:
                raise CorruptedException("at position: " + hex(index))
        return obj


class SegCSF(BaseSegment):
    """ CSF segment """

    CMD_TYPES = (CmdWriteData, CmdCheckData, CmdNop, CmdSet, CmdInitialize, CmdUnlock, CmdInstallKey, CmdAuthData)

    @property
    def header(self):
        return self._header

    @property
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, value):
        self._enabled = value

    @property
    def commands(self):
        return self._commands

    @property
    def size(self):
        return self.header.length if self.enabled else 0

    @property
    def space(self):
        return self.size + self.padding if self.enabled else 0

    def __init__(self, param=0, enabled=False):
        super().__init__()
        self._header = Header(SegTag.CSF, param)
        self._enabled = enabled
        self._commands = []

    def __eq__(self, obj):
        if not isinstance(obj, SegCSF):
            return False
        if len(self._commands) != len(obj):
            return False
        for cmd in obj:
            if cmd not in self._commands:
                return False
        return True

    def __len__(self):
        len(self._commands)

    def __getitem__(self, key):
        return self._commands[key]

    def __setitem__(self, key, value):
        assert type(value) in self.CMD_TYPES
        self._commands[key] = value

    def __iter__(self):
        return self._commands.__iter__()

    def info(self):
        msg = ""
        for cmd in self._commands:
            msg += str(cmd)
            msg += "\n"
        return msg

    def append(self, cmd):
        assert type(cmd) in self.CMD_TYPES
        self._commands.append(cmd)
        self._header.length += cmd.size

    def pop(self, index):
        assert 0 <= index < len(self._commands)
        cmd = self._commands.pop(index)
        self._header.length -= cmd.size
        return cmd

    def clear(self):
        self._commands.clear()
        self._header.length = self._header.size

    def export(self, padding=False):
        """ Export segment as bytes array
        :param padding: True if use padding (default: False)
        :return: bytes
        """
        data = b''
        if self.enabled:
            data = self.header.export()
            for command in self._commands:
                data += command.export()
            if padding:
                data += self._padding_export()

        return data

    @classmethod
    def parse(cls, data, offset=0):
        """ Parse segment from bytes array
        :param data: The bytes array of CSF segment
        :return SegCSF object
        """
        header = Header.parse(data, offset, SegTag.CSF)
        index = header.size
        obj = cls(header.param, True)
        while index < header.length:
            passed = False
            for cmd_class in cls.CMD_TYPES:
                try:
                    cmd_obj = cmd_class.parse(data, offset + index)
                except UnparsedException:
                    passed = False
                    continue
                obj.append(cmd_obj)
                index += cmd_obj.size
                passed = True
                break
            if not passed:
                raise CorruptedException("at position: " + hex(offset + index))
# TODO: Parse CSF blob
#        for cmd in obj.commands:
#            if isinstance(cmd, CmdInstallKey):
#                header = Header.parse(data, offset, SegTag.CRT)
#                index = offset + cmd.keydat + header.size
#            elif isinstance(cmd, CmdAuthData):
#                header.parse(data, offset + cmd.auth_start, SegTag.SIG)
#                index = offset + cmd.auth_start + header.size
#            else:
#                continue

        return obj


########################################################################################################################
# Boot Image V3 Segments (i.MX8QM-Ax, i.MX8QXP-Ax)
########################################################################################################################

class SegIVT3a(BaseSegment):
    """ IVT3a segment """

    FORMAT = '<1L5Q'
    SIZE = Header.SIZE + calcsize(FORMAT)

    @property
    def header(self):
        return self._header

    @property
    def size(self):
        return self.SIZE

    def __init__(self, param):
        """ Initialize IVT segment
        :param param: The version of IVT and Image format
        """
        super().__init__()
        self._header = Header(SegTag.IVT3, param)
        self._header.length = self.SIZE
        self.version = 0
        self.dcd_address = 0
        self.bdt_address = 0
        self.ivt_address = 0
        self.csf_address = 0
        self.next = 0

    def __eq__(self, obj):
        if not isinstance(obj, SegIVT3a):
            return False
        if self.version != obj.version or \
           self.dcd_address != obj.dcd_address or \
           self.bdt_address != obj.bdt_address or \
           self.ivt_address != obj.ivt_address or \
           self.csf_address != obj.csf_address or \
           self.next != obj.next:
            return False
        return True

    def info(self):
        msg = ""
        msg += " VER:  {}\n".format(self.version)
        msg += " IVT:  0x{:08X}\n".format(self.ivt_address)
        msg += " BDT:  0x{:08X}\n".format(self.bdt_address)
        msg += " DCD:  0x{:08X}\n".format(self.dcd_address)
        msg += " CSF:  0x{:08X}\n".format(self.csf_address)
        msg += " NEXT: 0x{:08X}\n".format(self.next)
        msg += "\n"
        return msg

    def validate(self):
        if self.ivt_address == 0 or self.bdt_address == 0 or self.bdt_address < self.ivt_address:
            raise ValueError("Not valid IVT/BDT address")
        if self.dcd_address and self.dcd_address < self.ivt_address:
            raise ValueError("Not valid DCD address: 0x{:X}".format(self.dcd_address))
        if self.csf_address and self.csf_address < self.ivt_address:
            raise ValueError("Not valid CSF address: 0x{:X}".format(self.csf_address))

    def export(self, padding=False):
        """ Export segment as bytes array
        :param padding: True if use padding (default: False)
        :return: bytes
        """
        self.validate()

        data = self.header.export()
        data += pack(self.FORMAT, self.version, self.dcd_address, self.bdt_address, self.ivt_address,
                     self.csf_address, self.next)
        if padding:
            data += self._padding_export()
        return data

    @classmethod
    def parse(cls, data):
        """ Parse segment from bytes array
        :param data: The bytes array of IVT3a segment
        :return SegIVT3a object
        """
        header = Header.parse(data, 0, SegTag.IVT3)
        obj = cls(header.param)

        (obj.version,
         obj.dcd_address,
         obj.bdt_address,
         obj.ivt_address,
         obj.csf_address,
         obj.next) = unpack_from(cls.FORMAT, data, header.size)

        obj.validate()

        return obj


class SegIVT3b(BaseSegment):
    """ IVT3b segment """

    FORMAT = '<1L7Q'
    SIZE = Header.SIZE + calcsize(FORMAT)

    @property
    def header(self):
        return self._header

    @property
    def size(self):
        return self.SIZE

    def __init__(self, version):
        """ Initialize IVT segment
        :param version: The version of IVT and Image format
        """
        super().__init__()
        self._header = Header(SegTag.IVT2, version)
        self._header.length = self.SIZE
        self.rs1 = 0
        self.dcd_address = 0
        self.bdt_address = 0
        self.ivt_address = 0
        self.csf_address = 0
        self.scd_address = 0
        self.rs2h = 0
        self.rs2l = 0

    def __eq__(self, obj):
        if not isinstance(obj, SegIVT3b):
            return False
        if self.header.param != obj.header.param or \
           self.dcd_address != obj.dcd_address or \
           self.bdt_address != obj.bdt_address or \
           self.ivt_address != obj.ivt_address or \
           self.csf_address != obj.csf_address or \
           self.scd_address != obj.scd_address:
            return False
        return True

    def info(self):
        msg = ""
        msg += " IVT: 0x{:08X}\n".format(self.ivt_address)
        msg += " BDT: 0x{:08X}\n".format(self.bdt_address)
        msg += " DCD: 0x{:08X}\n".format(self.dcd_address)
        msg += " SCD: 0x{:08X}\n".format(self.scd_address)
        msg += " CSF: 0x{:08X}\n".format(self.csf_address)
        msg += "\n"
        return msg

    def validate(self):
        if self.ivt_address == 0 or self.bdt_address == 0 or self.bdt_address < self.ivt_address:
            raise ValueError("Not valid IVT/BDT address")
        if self.dcd_address and self.dcd_address < self.ivt_address:
            raise ValueError("Not valid DCD address: 0x{:X}".format(self.dcd_address))
        if self.csf_address and self.csf_address < self.ivt_address:
            raise ValueError("Not valid CSF address: 0x{:X}".format(self.csf_address))
        if self.scd_address and self.scd_address < self.ivt_address:
            raise ValueError("Not valid SCD address: 0x{:X}".format(self.scd_address))

    def export(self, padding=False):
        """ Export segment as bytes array
        :param padding: True if use padding (default: False)
        :return: bytes
        """
        self.validate()

        data = self.header.export()
        data += pack(self.FORMAT, self.rs1, self.dcd_address, self.bdt_address, self.ivt_address, self.csf_address,
                     self.scd_address, self.rs2h, self.rs2l)
        if padding:
            data += self._padding_export()
        return data

    @classmethod
    def parse(cls, data):
        """ Parse segment from bytes array
        :param data: The bytes array of IVT3b segment
        :return SegIVT3b object
        """
        header = Header.parse(data, 0, SegTag.IVT2)
        obj = cls(header.param)

        (obj.rs1,
         obj.dcd_address,
         obj.bdt_address,
         obj.ivt_address,
         obj.csf_address,
         obj.scd_address,
         obj.rs2h,
         obj.rs2l) = unpack_from(cls.FORMAT, data, header.size)

        obj.validate()

        return obj


class SegIDS3a(BaseSegment):
    """ IDS3a segment """

    FORMAT = '<3Q4L'
    SIZE = calcsize(FORMAT)

    @property
    def size(self):
        return self.SIZE

    def __init__(self):
        """ Initialize IDS3a segment """
        super().__init__()
        self.image_source = 0
        self.image_destination = 0
        self.image_entry = 0
        self.image_size = 0
        self.hab_flags = 0
        self.scfw_flags = 0
        self.rom_flags = 0

    def __eq__(self, obj):
        if not isinstance(obj, SegIDS3a):
            return False
        if self.image_source != obj.image_source or \
           self.image_destination != obj.image_destination or \
           self.image_entry != obj.image_entry or \
           self.image_size != obj.image_size or \
           self.hab_flags != obj.hab_flags or \
           self.scfw_flags != obj.scfw_flags or \
           self.rom_flags != obj.rom_flags:
            return False
        return True

    def info(self):
        """ Get IDS3a segment info """
        msg  = " Source: 0x{:08X}\n".format(self.image_source)
        msg += " Dest:   0x{:08X}\n".format(self.image_destination)
        msg += " Entry:  0x{:08X}\n".format(self.image_entry)
        msg += " Size:   {:s} ({} Bytes)\n".format(sizeof_fmt(self.image_size), self.image_size)
        msg += " <Flags>\n"
        msg += " SCFW:   0x{:08X}\n".format(self.scfw_flags)
        msg += " HAB:    0x{:08X}\n".format(self.hab_flags)
        msg += " ROM:    0x{:08X}\n".format(self.rom_flags)
        msg += "\n"
        return msg

    def export(self, padding=False):
        """ Export segment as bytes array
        :param padding: True if use padding (default: False)
        :return: bytes
        """
        data = pack(self.FORMAT,
                    self.image_source,
                    self.image_destination,
                    self.image_entry,
                    self.image_size,
                    self.hab_flags,
                    self.scfw_flags,
                    self.rom_flags)
        if padding:
            data += self._padding_export()

        return data

    @classmethod
    def parse(cls, data):
        """ Parse segment from bytes array
        :param data: The bytes array of IDS3a segment
        :return SegIDS3a object
        """
        obj = cls()
        (obj.image_source,
         obj.image_destination,
         obj.image_entry,
         obj.image_size,
         obj.hab_flags,
         obj.scfw_flags,
         obj.rom_flags) = unpack_from(obj.FORMAT, data)

        return obj


class SegBDS3a(BaseSegment):
    """ BDS3a segment """

    FORMAT = '<4L'
    HEADER_SIZE = calcsize(FORMAT)
    IMAGES_MAX_COUNT = 6
    SIZE = HEADER_SIZE + SegIDS3a.SIZE * IMAGES_MAX_COUNT

    @property
    def header_size(self):
        return self.HEADER_SIZE

    @property
    def size(self):
        return self.SIZE

    def __init__(self):
        """ Initialize BDS3a segment """
        super().__init__()
        self.images_count = 0
        self.boot_data_size = 0
        self.boot_data_flag = 0
        self.images = [SegIDS3a() for i in range(self.IMAGES_MAX_COUNT)]
        self.rs = 0

    def info(self):
        msg  = " IMAGES: {}\n".format(self.images_count)
        #msg += " Data size: {}\n".format(self.boot_data_size)
        msg += " DFLAGS: 0x{0:08X}\n".format(self.boot_data_flag)
        msg += "\n"
        for i in range(self.images_count):
            msg += " IMAGE[{}] \n".format(i)
            msg += self.images[i].info()
        return msg

    def export(self, padding=False):
        """ Export segment as bytes array
        :param padding: True if use padding (default: False)
        :return: bytes
        """
        data = pack(self.FORMAT,
                    self.images_count,
                    self.boot_data_size,
                    self.boot_data_flag,
                    self.rs)

        for i in range(self.IMAGES_MAX_COUNT):
            data += self.images[i].export()

        if padding:
            data += self._padding_export()
        return data

    @classmethod
    def parse(cls, data):
        """ Parse segment from bytes array
        :param data: The bytes array of BDS3a segment
        :return SegBDS3a object
        """
        obj = cls()
        (obj.images_count,
         obj.boot_data_size,
         obj.boot_data_flag,
         obj.rs) = unpack_from(cls.FORMAT, data)

        for i in range(obj.images_count):
            obj.images[i] = SegIDS3a.parse(data[cls.HEADER_SIZE + i * SegIDS3a.SIZE:])

        return obj


class SegIDS3b(BaseSegment):
    """ IDS3b segment """
    FORMAT = '<3Q2L'
    SIZE = calcsize(FORMAT)

    @property
    def size(self):
        return calcsize(self.FORMAT)

    def __init__(self):
        """ Initialize IDS3b segment """
        super().__init__()
        self.image_source = 0
        self.image_destination = 0
        self.image_entry = 0
        self.image_size = 0
        self.flags = 0

    def info(self):
        msg  = " Source: 0x{:08X}\n".format(self.image_source)
        msg += " Dest:   0x{:08X}\n".format(self.image_destination)
        msg += " Entry:  0x{:08X}\n".format(self.image_entry)
        msg += " Flags:  0x{:08X}\n".format(self.flags)
        msg += " Size:   {:s} ({} Bytes)\n".format(sizeof_fmt(self.image_size), self.image_size)
        msg += "\n"
        return msg

    def export(self, padding=False):
        """ Export segment as bytes array
        :param padding: True if use padding (default: False)
        :return: bytes
        """
        data = pack(self.FORMAT,
                    self.image_source, self.image_destination, self.image_entry, self.image_size, self.flags)
        if padding:
            data += self._padding_export()

        return data

    @classmethod
    def parse(cls, data):
        """ Parse segment from bytes array
        :param data: The bytes array of IDS3b segment
        :return SegIDS3b object
        """
        ids = cls()
        (ids.image_source,
         ids.image_destination,
         ids.image_entry,
         ids.image_size,
         ids.flags) = unpack_from(cls.FORMAT, data)

        return ids


class SegBDS3b(BaseSegment):
    """ BDS3b segment """
    FORMAT = '<4L'
    HEADER_SIZE = calcsize(FORMAT)
    IMAGES_MAX_COUNT = 4
    SIZE = calcsize(FORMAT) + SegIDS3b.SIZE * (IMAGES_MAX_COUNT + 3)

    @property
    def header_size(self):
        return self.HEADER_SIZE

    @property
    def size(self):
        return self.SIZE

    def __init__(self):
        """ Initialize BDS3b segment """
        super().__init__()
        self.images_count = 0
        self.boot_data_size = 0
        self.boot_data_flag = 0
        self.rs = 0

        self.images = [SegIDS3b() for i in range(self.IMAGES_MAX_COUNT)]

        self.scd = SegIDS3b()
        self.csf = SegIDS3b()
        self.rs_img = SegIDS3b()

    def info(self):
        msg  = " IMAGES: {}\n".format(self.images_count)
        #msg += " Data size: {}\n".format(self.boot_data_size)
        msg += " DFLAGS: 0x{0:08X}\n".format(self.boot_data_flag)
        msg += "\n"
        for i in range(self.images_count):
            msg += " IMAGE[{}] \n".format(i)
            msg += self.images[i].info()
        if self.scd.image_source != 0:
            msg += " SCD:\n"
            msg += self.scd.info()
        if self.csf.image_source != 0:
            msg += " CSF:\n"
            msg += self.csf.info()

        return msg

    def export(self, padding=False):
        """ Export segment as bytes array
        :param padding: True if use padding (default: False)
        :return: bytes
        """
        data = pack(self.FORMAT,
                    self.images_count,
                    self.boot_data_size,
                    self.boot_data_flag,
                    self.rs)

        for i in range(self.IMAGES_MAX_COUNT):
            data += self.images[i].export()

        data += self.scd.export()
        data += self.csf.export()
        data += self.rs_img.export()

        if padding:
            data += self._padding_export()

        return data

    @classmethod
    def parse(cls, data):
        """ Parse segment from bytes array
        :param data: The bytes array of BDS3b segment
        :return SegBDS3b object
        """
        obj = cls()
        (obj.images_count,
         obj.boot_data_size,
         obj.boot_data_flag,
         obj.rs) = unpack_from(obj.FORMAT, data)

        offset = cls.HEADER_SIZE
        for i in range(obj.images_count):
            obj.images[i] = SegIDS3b.parse(data[offset:])
            offset += SegIDS3b.SIZE

        obj.scd = SegIDS3b.parse(data[offset:])
        offset += SegIDS3b.SIZE
        obj.csf = SegIDS3b.parse(data[offset:])
        offset += SegIDS3b.SIZE
        obj.rs_img = SegIDS3b.parse(data[offset:])

        return obj


########################################################################################################################
# Boot Image V4 Segments (i.MX8DM, i.MX8QM-Bx, i.MX8QXP-Bx)
########################################################################################################################

class SegBIM(BaseSegment):
    """ BootImage segment """
    FORMAT = '<2L2Q2L'
    SIZE = calcsize(FORMAT) + 64 + 32

    @property
    def size(self):
        return self.SIZE

    def __init__(self):
        """ Initialize BootImage segment """
        super().__init__()
        self.image_offset = 0
        self.image_size = 0
        self.load_address = 0
        self.entry_address = 0
        self.hab_flags = 0
        self.meta_data = 0
        self.image_hash = None
        self.image_iv = None

    def __eq__(self, obj):
        if not isinstance(obj, SegBIM):
            return False
        if self.image_offset != obj.image_offset or \
           self.image_size != obj.image_size or \
           self.load_address != obj.load_address or \
           self.entry_address != obj.entry_address or \
           self.hab_flags != obj.hab_flags or \
           self.meta_data != obj.meta_data or \
           self.image_hash != obj.image_hash or \
           self.image_iv != obj.image_iv:
            return False
        return True

    def info(self):
        """ Get BootImage segment info """
        msg  = " Offset:     0x{:X}\n".format(self.image_offset)
        msg += " Size:       {} ({} Bytes)\n".format(sizeof_fmt(self.image_size), self.image_size)
        msg += " Load:       0x{:X}\n".format(self.load_address)
        msg += " Entry:      0x{:X}\n".format(self.entry_address)
        msg += " HASH:       {}\n".format(''.join(['{:02X}'.format(i) for i in self.image_hash]))
        msg += " IV:         {}\n".format(''.join(['{:02X}'.format(i) for i in self.image_iv]))
        msg += " Hash Flags: 0x{:08X}\n".format(self.hab_flags)
        msg += " Meta Data:  0x{:08X}\n".format(self.meta_data)
        msg += "\n"
        return msg

    def export(self, padding=False):
        """ Export segment as bytes array
        :param padding: True if use padding (default: False)
        :return: bytes
        """
        data = pack(self.FORMAT,
                    self.image_offset,
                    self.image_size,
                    self.load_address,
                    self.entry_address,
                    self.hab_flags,
                    self.meta_data)

        if padding:
            data += self._padding_export()

        return data

    @classmethod
    def parse(cls, data):
        """ Parse segment from bytes array
        :param data: The bytes array of BootImage segment
        :return SegBootImage object
        """
        obj = cls()
        (obj.image_offset,
         obj.image_size,
         obj.load_address,
         obj.entry_address,
         obj.hab_flags,
         obj.meta_data) = unpack_from(obj.FORMAT, data)

        offset = calcsize(cls.FORMAT)
        obj.image_hash = data[offset:offset+64]
        offset += 64
        obj.image_iv = data[offset:offset + 32]

        return obj


class SegSIGB(BaseSegment):
    """ SignatureBlock segment """

    FORMAT = '<4HL'
    SIZE = Header2.SIZE + calcsize(FORMAT)

    @property
    def version(self):
        return self._header.param

    @version.setter
    def version(self, value):
        self._header.param = value

    @property
    def size(self):
        return self.SIZE

    def __init__(self, version=0):
        """ Initialize SignatureBlock segment """
        super().__init__()
        self._header = Header2(SegTag.SIGB, version)
        self._header.length = self.SIZE
        self.srk_table_offset = 0
        self.cert_offset = 0
        self.blob_offset = 0
        self.signature_offset = 0
        self.reserved = 0

    def __eq__(self, obj):
        if not isinstance(obj, SegSIGB):
            return False
        if self.version != obj.version or \
           self.srk_table_offset != obj.srk_table_offset or \
           self.cert_offset != obj.cert_offset or \
           self.blob_offset != obj.blob_offset or \
           self.signature_offset != obj.signature_offset:
            return False
        return True

    def info(self):
        """ Get SignatureBlock segment info """
        msg  = " SRK Table Offset:   0x{:X}\n".format(self.srk_table_offset)
        msg += " Certificate Offset: 0x{:X}\n".format(self.cert_offset)
        msg += " Signature Offset:   0x{:X}\n".format(self.signature_offset)
        msg += " Blob Offset:        0x{:X}\n".format(self.blob_offset)
        msg += "\n"
        return msg

    def export(self, padding=False):
        """ Export segment as bytes array
        :param padding: True if use padding (default: False)
        :return: bytes
        """
        data = self._header.export()
        data += pack(self.FORMAT,
                     self.srk_table_offset, self.cert_offset, self.blob_offset, self.signature_offset, self.reserved)
        if padding:
            data += self._padding_export()

        return data

    @classmethod
    def parse(cls, data):
        """ Parse segment from bytes array
        :param data: The bytes array of SignatureBlock segment
        :return SegSigBlk object
        """
        header = Header2.parse(data, 0, SegTag.SIGB)
        obj = cls(header.param)

        (obj.srk_table_offset,
         obj.cert_offset,
         obj.blob_offset,
         obj.signature_offset,
         obj.reserved) = unpack_from(obj.FORMAT, data)

        return obj


class SegBIC1(BaseSegment):
    """ Boot Images Container segment """

    MAX_NUM_IMGS = 6

    FORMAT = '<LH2B2H'
    SIZE = Header.SIZE + calcsize(FORMAT) + MAX_NUM_IMGS * SegBIM.SIZE + SegSIGB.SIZE + 8

    @property
    def version(self):
        return self._header.param

    @version.setter
    def version(self, value):
        self._header.param = value

    @property
    def size(self):
        return self.SIZE

    def __init__(self, version=0):
        """ Initialize Boot Images Container segment
        :param version: The version of Header for Boot Images Container
        """
        super().__init__()
        self._header = Header2(SegTag.BIC1, version)
        self._header.length = self.SIZE
        self.flags = 0
        self.sw_version = 0
        self.fuse_version = 0
        self.images_count = 0
        self.sig_blk_offset = 0
        self.reserved = 0
        self.images = [SegBIM() for _ in range(self.MAX_NUM_IMGS)]
        self.sig_blk_hdr = SegSIGB()
        self.sig_blk_size = 0
        self.padding = 8

    def __eq__(self, obj):
        if not isinstance(obj, SegBIC1):
            return False
        if self.flags != obj.flags or \
           self.sw_version != obj.sw_version or \
           self.fuse_version != obj.fuse_version or \
           self.images_count != obj.images_count or \
           self.sig_blk_offset != obj.sig_blk_offset or \
           self.images != obj.images or \
           self.sig_blk_hdr != obj.sig_blk_hdr or \
           self.sig_blk_size != obj.sig_blk_size:
            return False
        return True

    def info(self):
        msg = ""
        msg += " Flags:        0x{:08X}\n".format(self.flags)
        msg += " SW Version:   {}\n".format(self.sw_version)
        msg += " Fuse Version: {}\n".format(self.fuse_version)
        msg += " Images Count: {}\n".format(self.images_count)
        msg += " SigBlkOffset: 0x{:08X}\n".format(self.sig_blk_offset)
        msg += "\n"
        for i in range(self.images_count):
            msg += " IMAGE[{}] \n".format(i)
            msg += self.images[i].info()
        msg += " [ Signature Block Header ]\n"
        msg += self.sig_blk_hdr.info()
        msg += "\n"
        return msg

    def validate(self):
        pass

    def export(self, padding=False):
        """ Export segment as bytes array
        :param padding: True if use padding (default: False)
        :return: bytes
        """
        self.validate()

        data = self._header.export()
        data += pack(self.FORMAT,
                     self.flags,
                     self.sw_version,
                     self.fuse_version,
                     self.images_count,
                     self.sig_blk_offset,
                     self.reserved)
        for image in self.images:
            data += image.export()
        data += self.sig_blk_hdr.export()
        data += pack('<L', self.sig_blk_size)
        if padding:
            data += self._padding_export()
        return data

    @classmethod
    def parse(cls, data):
        """ Parse segment from bytes array
        :param data: The bytes array of BIC1 segment
        :return SegBIC1 object
        """
        header = Header2.parse(data, 0, SegTag.BIC1)
        offset = header.size
        obj = cls(header.param)

        (obj.flags,
         obj.sw_version,
         obj.fuse_version,
         obj.images_count,
         obj.sig_blk_offset,
         obj.reserved) = unpack_from(cls.FORMAT, data, offset)

        offset += calcsize(cls.FORMAT)
        for i in range(obj.images_count):
            obj.images[i] = SegBIM.parse(data[offset:])
            offset += SegBIM.SIZE

        obj.sig_blk_hdr = SegSIGB.parse(data[offset:])
        offset += SegSIGB.SIZE
        obj.sig_blk_size = unpack_from('<L', data, offset)

        obj.validate()

        return obj





