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

from enum import IntEnum, unique

from .header import UnparsedException, CorruptedException
from .segments import SegIVT, SegBDT, SegAPP, SegDCD, SegCSF


########################################################################################################################
## IMX Image Classes
########################################################################################################################

class BootImage(object):
    ''' IMX Boot Image '''

    # The value of CSF segment size
    CSF_SIZE  = 0x2000
    # The align value of APP segment
    APP_ALIGN = 0x1000
    # The value of image head size
    #           offset | size
    HEAD_SIZE = {0x400: 0xC00,
                 0x100: 0x300}

    @property
    def address(self):
        return self._address

    @address.setter
    def address(self, value):
        self._address = value

    @property
    def offset(self):
        return self._offset

    @offset.setter
    def offset(self, value):
        self._offset = value

    @property
    def version(self):
        return self._ivt.header.param

    @version.setter
    def version(self, value):
        self._ivt.header.param = value

    @property
    def app(self):
        return self._app.data

    @app.setter
    def app(self, value):
        assert isinstance(value, (bytes, bytearray)), "Value type not a bytes or bytearray !"
        self._app.data = value

    @property
    def dcd(self):
        return self._dcd

    @dcd.setter
    def dcd(self, value):
        assert isinstance(value, SegDCD), "Value type not a DCD segment !"
        self._dcd = value

    @property
    def csf(self):
        return self._csf

    @csf.setter
    def csf(self, value):
        assert isinstance(value, SegCSF), "Value type not a CSF segment !"
        self._csf = value

    @property
    def plg(self):
        return self._plg

    @plg.setter
    def plg(self, value):
        assert isinstance(value, bool)
        self._plg = value

    @property
    def size(self):
        sum  = self._ivt.space
        sum += self._bdt.space
        sum += self._dcd.space
        sum += self._app.space
        sum += self._csf.space
        return sum

    def __init__(self, address=0, app=None, dcd=None, csf=None, offset=0x400, plugin=False, version=0x41):
        '''
        Initialize boot image object
        :param address: The start address of image in target memory
        :param app: The application image as bytes array
        :param dcd: The DCD segment as SegDCD object
        :param csf: The CSF segment as SegCSF object
        :param offset: The IVT offset
        :param plugin: The plugin flag as bool
        :param version: The version of boot image format
        :return: BootImage object
        '''
        self._ivt = SegIVT(version)
        self._bdt = SegBDT()
        self._app = SegAPP(app)
        self._dcd = SegDCD() if dcd is None else dcd
        self._csf = SegCSF() if csf is None else csf
        self._plg = plugin
        self._offset = offset
        self._address = address

    def __str__(self):
        return self.info()

    def __repr__(self):
        return self.info()

    def _update(self):
        # Set zero padding for IVT and BDT sections
        self._ivt.padding = 0
        self._bdt.padding = 0
        # Calculate padding for DCD, APP and CSF sections
        tmp_val = self._ivt.space + self._bdt.space + self._dcd.size
        head_size = 0xC00 if self._offset not in self.HEAD_SIZE else self.HEAD_SIZE[self._offset]
        self._dcd.padding = head_size - tmp_val
        tmp_val = self._app.size % self.APP_ALIGN
        self._app.padding = self.APP_ALIGN - tmp_val if tmp_val > 0 else 0
        # Set IVT section
        self._ivt.ivt_addr = self._address + self._offset
        self._ivt.bdt_addr = self._ivt.ivt_addr + self._ivt.space
        if self._dcd.enabled:
            self._ivt.dcd_addr = self._ivt.bdt_addr + self._bdt.space
            self._ivt.app_addr = self._ivt.dcd_addr + self._dcd.space
        else:
            # TODO: Check the Image format without DCD section
            self._ivt.dcd_addr = 0
            self._ivt.app_addr = self._ivt.bdt_addr + self._bdt.space
        if self._csf.enabled:
            self._ivt.csf_addr = self._ivt.app_addr + self._app.space
            self._csf.padding = self.CSF_SIZE - self._csf.size
        else:
            self._ivt.csf_addr = 0
        # Set BDT section
        self._bdt.start  = self._ivt.ivt_addr - self._offset
        self._bdt.length = self.size + self._offset
        self._bdt.plugin = 1 if self._plg else 0

    def info(self):
        self._update()
        # Print IVT
        msg  = "#" * 60 + "\n"
        msg += "# IVT (Image Vector Table)\n"
        msg += "#" * 60 + "\n\n"
        msg += str(self._ivt)
        # Print DBT
        msg += "#" * 60 + "\n"
        msg += "# BDT (Boot Data Table)\n"
        msg += "#" * 60 + "\n\n"
        msg += str(self._bdt)
        # Print DCD
        if self._dcd.enabled:
            msg += "#" * 60 + "\n"
            msg += "# DCD (Device Config Data)\n"
            msg += "#" * 60 + "\n\n"
            msg += str(self._dcd)
        # Print CSF
        if self._csf.enabled:
            msg += "#" * 60 + "\n"
            msg += "# CSF (Code Signing Data)\n"
            msg += "#" * 60 + "\n\n"
            msg += str(self._csf)
        return msg

    def parse(self, data, offset=0):
        assert type(data) in (str, bytes, bytearray)
        assert len(data) > offset + 0xC00 if self._offset not in self.HEAD_SIZE else self.HEAD_SIZE[self._offset]

        imx_image = False
        while offset < len(data):
            try:
                self._ivt.parse(data, offset)
            except UnparsedException:
                offset += self._offset
            else:
                imx_image = True
                break

        if imx_image:
            self._ivt.padding = (self._ivt.bdt_addr - self._ivt.ivt_addr) - self._ivt.size
            self._bdt.parse(data, (offset + self._ivt.bdt_addr) - self._ivt.ivt_addr)
            self._offset = self._ivt.ivt_addr - self._bdt.start
            self._address = self._bdt.start

            if self._ivt.dcd_addr > self._ivt.ivt_addr:
                self._bdt.padding = (self._ivt.dcd_addr - self._ivt.bdt_addr) - self._bdt.size
                self._dcd.parse(data, (offset + self._ivt.dcd_addr) - self._ivt.ivt_addr)
                self._dcd.padding = (self._ivt.app_addr - self._ivt.dcd_addr) - self._dcd.size
            else:
                self._bdt.padding = (self._ivt.app_addr - self._ivt.bdt_addr) - self._bdt.size

            img_start = offset + (self._ivt.app_addr - self._ivt.ivt_addr)
            if self._ivt.csf_addr > self._ivt.ivt_addr:
                csf_start = (offset + self._ivt.csf_addr) - self._ivt.ivt_addr
                self._app.data = data[img_start:csf_start]
                self._app.padding = 0
                self._csf.parse(data, csf_start)
                self._csf.padding = self._bdt.length - (csf_start + self._csf.size)
            else:
                img_end = self._bdt.length - self._offset
                self._app.data = data[img_start:img_end]
                self._app.padding = (len(data) - offset) - img_end

        else:
            raise Exception('No a IMX Boot image !')

    def export(self):
        self._update()
        data  = self._ivt.export(True)
        data += self._bdt.export(True)
        data += self._dcd.export(True)
        data += self._app.export(True)
        data += self._csf.export(True)
        return data


class KernelImage(object):
    ''' IMX Kernel Image '''

    IMAGE_MIN_SIZE = 0x1000

    @property
    def address(self):
        return self._ivt.app_addr

    @address.setter
    def address(self, value):
        self._ivt.app_addr = value

    @property
    def version(self):
        return self._ivt.header.param

    @version.setter
    def version(self, value):
        self._ivt.header.param = value

    @property
    def app(self):
        return self._app.data

    @app.setter
    def app(self, value):
        assert isinstance(value, (bytes, bytearray)), "Value type not a bytes or bytearray !"
        self._app.data = value

    @property
    def csf(self):
        return self._csf

    @csf.setter
    def csf(self, value):
        assert isinstance(value, SegCSF), "Value type not a CSF segment !"
        self._csf = value

    def __init__(self, address=0, app=None, csf=None, version=0x41):
        self._ivt = SegIVT(version)
        self._ivt.app_addr = address
        self._app = SegAPP(app)
        self._dcd = SegDCD()
        self._csf = csf if csf else SegCSF()

    def __str__(self):
        return self.info()

    def __repr__(self):
        return self.info()

    def _update(self):
        pass

    def info(self):
        pass

    def parse(self, data, offset=0):
        assert type(data) in (str, bytes, bytearray)
        assert len(data) > offset + self.IMAGE_MIN_SIZE
        pass

    def export(self):
        self._update()
        data  = self._app.export(True)
        data += self._ivt.export(True)
        data += self._csf.export(True)
        return data