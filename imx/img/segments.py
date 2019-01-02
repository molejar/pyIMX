# Copyright (c) 2017-2018 Martin Olejar
#
# SPDX-License-Identifier: BSD-3-Clause
# The BSD-3-Clause license for this file can be found in the LICENSE file included with this distribution
# or at https://spdx.org/licenses/BSD-3-Clause.html#licenseText

from io import BytesIO, BufferedReader
from struct import pack, unpack_from, calcsize

from .header import Header, SegTag, UnparsedException, CorruptedException
from .commands import CmdWriteData, CmdCheckData, CmdNop, CmdSet, CmdInitialize, CmdUnlock, CmdInstallKey, CmdAuthData,\
                      EnumWriteOps, EnumCheckOps, EnumEngine
from .secret import SecretKeyBlob, Certificate, Signature
from .misc import sizeof_fmt, read_raw_data, read_raw_segment


########################################################################################################################
## Base Segment Class
########################################################################################################################


class BaseSegment(object):
    ''' base segment '''

    # padding fill value
    PADDING_VAL = 0x00

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
        return bytes([self.PADDING_VAL] * self._padding) if self._padding > 0 else b''

    def __init__(self):
        self._padding = 0

    def __str__(self):
        return self.info()

    def __repr__(self):
        return self.info()

    def info(self):
        ''' object info '''
        raise NotImplementedError()

    def export(self, padding=False):
        ''' export interface '''
        raise NotImplementedError()

    @classmethod
    def parse(cls, buffer):
        ''' parse interface '''
        raise NotImplementedError()


########################################################################################################################
## Image Segments
########################################################################################################################

class SegIVT2(BaseSegment):
    ''' IVT2 segment '''
    FORMAT = '<7L'
    SIZE = Header.SIZE + calcsize(FORMAT)

    @property
    def header(self):
        return self._header

    @property
    def size(self):
        return self._header.length

    def __init__(self, version):
        '''
        Initialize IVT segment
        :param version: The version of IVT and Image format
        '''
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
        '''
        :param padding:
        :return:
        '''
        self.validate()

        data = self.header.export()
        data += pack(self.FORMAT, self.app_address, self.rs1, self.dcd_address, self.bdt_address, self.ivt_address,
                     self.csf_address, self.rs2)
        if padding:
            data += self._padding_export()

        return data

    @classmethod
    def parse(cls, data):
        '''
        :param data:
        '''
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


class SegIVT3a(BaseSegment):
    ''' IVT3a segment '''
    FORMAT = '<1L5Q'
    SIZE = Header.SIZE + calcsize(FORMAT)

    @property
    def header(self):
        return self._header

    @property
    def size(self):
        return self.SIZE

    def __init__(self, param):
        '''
        Initialize IVT segment
        :param version: The version of IVT and Image format
        '''
        super().__init__()
        self._header = Header(SegTag.IVT3, param)
        self._header.length = self.SIZE
        self.version = 0
        self.dcd_address = 0
        self.bdt_address = 0
        self.ivt_address = 0
        self.csf_address = 0
        self.next = 0

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
        '''
        :param padding:
        :return:
        '''
        self.validate()

        data = self.header.export()
        data += pack(self.FORMAT, self.version, self.dcd_address, self.bdt_address, self.ivt_address,
                     self.csf_address, self.next)
        if padding:
            data += self._padding_export()
        return data

    @classmethod
    def parse(cls, data):
        '''
        :param data:
        '''
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
    ''' IVT3b segment '''
    FORMAT = '<1L7Q'
    SIZE = calcsize(FORMAT) + calcsize(Header.FORMAT)

    @property
    def header(self):
        return self._header

    @property
    def size(self):
        return self.SIZE

    def __init__(self, version):
        '''
        Initialize IVT segment
        :param version: The version of IVT and Image format
        '''
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
        '''
        :param padding:
        :return:
        '''
        self.validate()

        data = self.header.export()
        data += pack(self.FORMAT, self.rs1, self.dcd_address, self.bdt_address, self.ivt_address, self.csf_address,
                     self.scd_address, self.rs2h, self.rs2l)
        if padding:
            data += self._padding_export()
        return data

    @classmethod
    def parse(cls, data):
        '''
        :param data:
        '''
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
    ''' IDS3a segment '''
    FORMAT = '<3Q4L'
    SIZE = calcsize(FORMAT)

    @property
    def size(self):
        return self.SIZE

    def __init__(self):
        '''
        Initialize IDS3a segment
        '''
        super().__init__()
        self.image_source = 0
        self.image_destination = 0
        self.image_entry = 0
        self.image_size = 0
        self.hab_flags = 0
        self.scfw_flags = 0
        self.rom_flags = 0

    def info(self):
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
        '''
        :param padding:
        :return:
        '''
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
        '''
        :param data:
        '''
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
    ''' BDS3a segment '''
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
        '''
        Initialize BDS3a segment
        '''
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
        '''
        :param padding:
        :return:
        '''
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
        '''
        :param data:
        '''
        obj = cls()
        (obj.images_count,
         obj.boot_data_size,
         obj.boot_data_flag,
         obj.rs) = unpack_from(cls.FORMAT, data)

        for i in range(obj.images_count):
            obj.images[i] = SegIDS3a.parse(data[cls.HEADER_SIZE + i * SegIDS3a.SIZE:])

        return obj


class SegIDS3b(BaseSegment):
    ''' IDS3b segment '''
    FORMAT = '<3Q2L'
    SIZE = calcsize(FORMAT)

    @property
    def size(self):
        return calcsize(self.FORMAT)

    def __init__(self):
        '''
        Initialize IDS3b segment
        '''
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
        '''
        :param padding:
        :return:
        '''
        data = pack(self.FORMAT,
                    self.image_source, self.image_destination, self.image_entry, self.image_size, self.flags)
        if padding:
            data += self._padding_export()

        return data

    @classmethod
    def parse(cls, data):
        '''
        :param data:
        '''
        ids = cls()
        (ids.image_source,
         ids.image_destination,
         ids.image_entry,
         ids.image_size,
         ids.flags) = unpack_from(cls.FORMAT, data)

        return ids


class SegBDS3b(BaseSegment):
    ''' BDS3b segment '''
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
        '''
        Initialize BDS3b segment
        '''
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
        '''
        :param padding:
        :return:
        '''
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
        '''
        :param data:
        '''
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


class SegBDT(BaseSegment):
    ''' Boot data segment '''
    FORMAT = '<3L'
    SIZE = calcsize(FORMAT)

    @property
    def plugin(self):
        return self._plugin

    @plugin.setter
    def plugin(self, value):
        assert value in (0, 1, 2), "Plugin value must be 0 or 1"
        self._plugin = value

    @property
    def size(self):
        return self.SIZE

    def __init__(self, start=0, length=0, plugin=0):
        '''
        :param start:
        :param length:
        :param plugin:
        '''
        super().__init__()
        self.start  = start
        self.length = length
        self.plugin = plugin

    def info(self):
        '''
        The info string of BDT segment
        :return: string
        '''
        msg  = " Start:  0x{0:08X}\n".format(self.start)
        msg += " Length: {0:s} ({1:d} Bytes)\n".format(sizeof_fmt(self.length), self.length)
        msg += " Plugin: {0:s}\n".format('YES' if self.plugin else 'NO')
        msg += "\n"

        return msg

    def export(self, padding=False):
        data = pack(self.FORMAT, self.start, self.length, self.plugin)
        if padding:
            data += self._padding_export()

        return data

    @classmethod
    def parse(cls, data):
        return cls(*unpack_from(cls.FORMAT, data))


class SegAPP(BaseSegment):
    ''' Boot data segment '''

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, value):
        self._data = value

    @property
    def size(self):
        return len(self._data)

    def __init__(self, data=None):
        '''
        :param data:
        '''
        super().__init__()
        self._data = data

    def info(self):
        msg  = " Size: {0:d} Bytes\n".format(len(self._data))
        msg += "\n"
        return msg

    def export(self, padding=False):
        data = bytes(self._data)
        if padding:
            data += self._padding_export()
        return data


class SegDCD(BaseSegment):
    ''' DCD segment '''
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
                txt_data += "Unlock {0:s}".format(EnumEngine.value_to_str(cmd.engine))
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

                if cmd[1] not in EnumEngine.get_names():
                    raise SyntaxError("Unlock CMD: wrong engine parameter at line %d" % (line_cnt - 1))

                engine = EnumEngine.str_to_value(cmd[1])
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
        # Parse DCD segment
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
    ''' Csf segment '''
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

    def __len__(self):
        len(self._commands)

    def __str__(self):
        return self.info()

    def __repr__(self):
        return self.info()

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
