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

from struct import pack, unpack_from, calcsize

from .header import Header, SegTag, UnparsedException, CorruptedException
from .commands import CmdWriteData, CmdCheckData, CmdNop, CmdSet, CmdInitialize, CmdUnlock, CmdInstallKey, CmdAuthData
from .secret import SecretKeyBlob, Certificate, Signature


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
        if self._padding > 0:
            return bytearray([self.PADDING_VAL] * self._padding)
        else:
            return b''

    def __init__(self):
        self._padding = 0

    def __str__(self):
        return self.info()

    def __repr__(self):
        return self.info()

    def info(self):
        ''' object info '''
        raise NotImplementedError()

    def parse(self, data, offset=0):
        ''' parse interface '''
        raise NotImplementedError()

    def export(self, padding=False):
        ''' export interface '''
        raise NotImplementedError()


########################################################################################################################
## Image Segments
########################################################################################################################


class SegIVT(BaseSegment):
    ''' IVT segment '''
    FORMAT = '<7L'

    @property
    def header(self):
        return self._header

    @property
    def app_addr(self):
        return self._app

    @app_addr.setter
    def app_addr(self, value):
        self._app = value

    @property
    def dcd_addr(self):
        return self._dcd

    @dcd_addr.setter
    def dcd_addr(self, value):
        self._dcd = value

    @property
    def bdt_addr(self):
        return self._bdt

    @bdt_addr.setter
    def bdt_addr(self, value):
        self._bdt = value

    @property
    def ivt_addr(self):
        return self._ivt

    @ivt_addr.setter
    def ivt_addr(self, value):
        self._ivt = value

    @property
    def csf_addr(self):
        return self._csf

    @csf_addr.setter
    def csf_addr(self, value):
        self._csf = value

    @property
    def size(self):
        return self._header.length

    def __init__(self, version):
        '''
        Initialize IVT segment
        :param version: The version of IVT and Image format
        '''
        super().__init__()
        self._header = Header(SegTag.HAB_TAG_IVT, version)
        self._header.length = self._header.size + calcsize(self.FORMAT)
        self._app = 0
        self._rs1 = 0
        self._dcd = 0
        self._bdt = 0
        self._ivt = 0
        self._csf = 0
        self._rs2 = 0

    def info(self):
        msg  = " IVT: 0x{0:08X}\n".format(self._ivt)
        msg += " BDT: 0x{0:08X}\n".format(self._bdt)
        msg += " DCD: 0x{0:08X}\n".format(self._dcd)
        msg += " APP: 0x{0:08X}\n".format(self._app)
        msg += " CSF: 0x{0:08X}\n".format(self._csf)
        msg += "\n"
        return msg

    def parse(self, data, offset=0):
        '''
        :param data:
        :param offset:
        '''
        self._header.parse(data, offset)
        offset += self._header.size
        (self._app,
         self._rs1,
         self._dcd,
         self._bdt,
         self._ivt,
         self._csf,
         self._rs2) = unpack_from(self.FORMAT, data, offset)

    def export(self, padding=False):
        '''
        :param padding:
        :return:
        '''
        data = self.header.export()
        data += pack(self.FORMAT,
                     self._app,
                     self._rs1,
                     self._dcd,
                     self._bdt,
                     self._ivt,
                     self._csf,
                     self._rs2)
        if padding:
            data += self._padding_export()
        return data


class SegBDT(BaseSegment):
    ''' Boot data segment '''
    FORMAT = '<3L'

    @property
    def start(self):
        return self._start

    @start.setter
    def start(self, value):
        self._start = value

    @property
    def length(self):
        return self._length

    @length.setter
    def length(self, value):
        self._length = value

    @property
    def plugin(self):
        return self._plugin

    @plugin.setter
    def plugin(self, value):
        self._plugin = value

    @property
    def size(self):
        return calcsize(self.FORMAT)

    def __init__(self, start=0, length=0, plugin=0):
        '''
        :param start:
        :param length:
        :param plugin:
        '''
        super().__init__()
        self._start = start
        self._length = length
        self._plugin = plugin

    def info(self):
        '''
        The info string of BDT segment
        :return: string
        '''
        msg  = " Start:  0x{0:08X}\n".format(self._start)
        msg += " Length: {0:d} Bytes\n".format(self._length)
        msg += " Plugin: {0:s}\n".format('YES' if self._plugin else 'NO')
        msg += "\n"
        return msg

    def parse(self, data, offset=0):
        (self._start, self._length, self._plugin) = unpack_from(self.FORMAT, data, offset)

    def export(self, padding=False):
        data = pack(self.FORMAT, self._start, self._length, self._plugin)
        if padding:
            data += self._padding_export()
        return data


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
        data = self._data
        if padding:
            data += self._padding_export()
        return data


class SegDCD(BaseSegment):
    ''' DCD segment '''
    @property
    def commands(self):
        return self._commands

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
    def size(self):
        return self._header.length if self.enabled else 0

    @property
    def space(self):
        return self.size + self.padding if self.enabled else 0

    def __init__(self, enabled=False, param=0x41):
        super().__init__()
        self._enabled = enabled
        self._header = Header(SegTag.HAB_TAG_DCD, param)
        self._header.length = self._header.size
        self._commands = []
        self._command_types = (CmdWriteData, CmdCheckData, CmdNop, CmdUnlock)

    def __len__(self):
        len(self._commands)

    def __getitem__(self, key):
        return self._commands[key]

    def __setitem__(self, key, value):
        assert type(value) in self._command_types
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
        assert type(cmd) in self._command_types
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

    def parse(self, data, offset=0):
        self._header.parse(data, offset)
        element_offset = self._header.size
        while element_offset < self._header.length:
            passed = False
            for command_type in self._command_types:
                command = command_type()
                try:
                    command.parse(data, offset + element_offset)
                except UnparsedException:
                    passed = False
                    del command
                    continue
                self._commands.append(command)
                element_offset += command.size
                passed = True
                break
            if not passed:
                raise CorruptedException
        self.enabled = True

    def export(self, padding=False):
        data = b''
        if self.enabled:
            data = self._header.export()
            for command in self._commands:
                data += command.export()
            if padding:
                data += self._padding_export()

        return data


class SegCSF(BaseSegment):
    ''' Csf segment '''
    @property
    def header(self):
        return self._header

    @property
    def commands(self):
        return self._commands

    @property
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, value):
        self._enabled = value

    @property
    def size(self):
        return self.header.length if self.enabled else 0

    @property
    def space(self):
        return self.size + self.padding if self.enabled else 0

    def __init__(self, enabled=False, param=0):
        super().__init__()
        self._enabled = enabled
        self._header = Header(SegTag.HAB_TAG_CSF, param)
        self._commands = []
        self._command_types = (
            CmdWriteData,
            CmdCheckData,
            CmdNop,
            CmdSet,
            CmdInitialize,
            CmdUnlock,
            CmdInstallKey,
            CmdAuthData
        )

    def __len__(self):
        len(self._commands)

    def __str__(self):
        return self.info()

    def __repr__(self):
        return self.info()

    def __getitem__(self, key):
        return self._commands[key]

    def __setitem__(self, key, value):
        assert type(value) in self._command_types
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
        assert type(cmd) in self._command_types
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

    def parse(self, data, offset=0):
        self.header.parse(data, offset)
        cmd_offset = self.header.size
        while cmd_offset < self.header.length:
            passed = False
            for command_type in self._command_types:
                command = command_type()
                try:
                    command.parse(data, offset + cmd_offset)
                except UnparsedException:
                    passed = False
                    del command
                    continue
                cmd_offset += command.size
                self._commands.append(command)
                passed = True
                break
            if not passed:
                raise CorruptedException("at position: " + hex(offset + cmd_offset))
        self._enabled = True
        # TODO: Parse CSF blob
        for cmd in self._commands:
            if isinstance(cmd, CmdInstallKey):
                header = Header(SegTag.HAB_TAG_CRT)
                header.parse(data, offset + cmd.keydat)
                #print(header)
                index = offset + cmd.keydat + header.size
                #print(data[index:index+header.length])
            elif isinstance(cmd, CmdAuthData):
                header = Header(SegTag.HAB_TAG_SIG)
                header.parse(data, offset + cmd.auth_start)
                #print(header)
                index = offset + cmd.auth_start + header.size
                #print(data[index:index+header.length])
            else:
                continue

    def export(self, padding=False):
        data = b''
        if self.enabled:
            data = self.header.export()
            for command in self._commands:
                data += command.export()
            if padding:
                data += self._padding_export()

        return data



