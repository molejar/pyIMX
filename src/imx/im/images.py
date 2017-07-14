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
## Enums
########################################################################################################################
@unique
class BootDev(IntEnum):
    SD_eSD_SDXC = 0x00
    MMC_eMMC = 0x01
    RawNAND = 0x02
    QSPI = 0x03
    NOR_OneNAND = 0x04
    SerialROM  = 0x05


########################################################################################################################
## IMX Image Classes
########################################################################################################################

class BootImage(object):
    ''' IMX Boot Image '''

    BDEV = (
        {'NAME': 'SD/eSD/SDXC', 'OFFSET': 0x400, 'HEAD_SIZE': 0xC00, 'APP_ALIGN': 0x1000, 'CSF_SIZE': 0x2000},
        {'NAME': 'MMC/eMMC',    'OFFSET': 0x400, 'HEAD_SIZE': 0xC00, 'APP_ALIGN': 0x1000, 'CSF_SIZE': 0x2000},
        {'NAME': 'RawNAND',     'OFFSET': 0x400, 'HEAD_SIZE': 0xC00, 'APP_ALIGN': 0x1000, 'CSF_SIZE': 0x2000},
        {'NAME': 'QSPI',        'OFFSET': 0x400, 'HEAD_SIZE': 0xC00, 'APP_ALIGN': 0x1000, 'CSF_SIZE': 0x2000},
        {'NAME': 'NOR/OneNAND', 'OFFSET': 0x400, 'HEAD_SIZE': 0xC00, 'APP_ALIGN': 0x1000, 'CSF_SIZE': 0x2000},
        {'NAME': 'SerialROM',   'OFFSET': 0x400, 'HEAD_SIZE': 0xC00, 'APP_ALIGN': 0x1000, 'CSF_SIZE': 0x2000}
    )

    @property
    def address(self):
        return self._ivt.ivt_addr

    @address.setter
    def address(self, value):
        self._ivt.ivt_addr = value

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
        assert isinstance(value, SegDCD), "Value type not a segment DCD !"
        self._dcd = value

    @property
    def csf(self):
        return self._csf

    @csf.setter
    def csf(self, value):
        assert isinstance(value, SegCSF), "Value type not a segment CSF !"
        self._csf = value

    @property
    def plg(self):
        return self._plg

    @plg.setter
    def plg(self, value):
        self._plg = value

    @property
    def size(self):
        sum  = self._ivt.space
        sum += self._bdt.space
        sum += self._dcd.space
        sum += self._app.space
        sum += self._csf.space
        return sum

    def __init__(self, addr=0, app=None, dcd=None, csf=None, plg=None, dev=BootDev.SD_eSD_SDXC, ver=0x41):
        self._ivt = SegIVT(ivt_addr=addr, version=ver)
        self._bdt = SegBDT()
        self._app = SegAPP(app)
        self._dcd = dcd if dcd else SegDCD()
        self._csf = csf if csf else SegCSF()
        self._plg = plg
        self._dev = int(dev)

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
        self._dcd.padding = self.BDEV[self._dev]['HEAD_SIZE'] - tmp_val
        # TODO: Check calculation of APP padding
        tmp_val = self._app.size % self.BDEV[self._dev]['APP_ALIGN']
        self._app.padding = self.BDEV[self._dev]['APP_ALIGN'] - tmp_val if tmp_val > 0 else 0
        # Set IVT section
        if self._dcd.enabled:
            self._ivt.dcd_addr = self._ivt.bdt_addr + self._bdt.space
            self._ivt.img_addr = self._ivt.dcd_addr + self._dcd.space
        else:
            # TODO: Check the Image format without DCD section
            self._ivt.dcd_addr = 0
            self._ivt.img_addr = self._ivt.bdt_addr + self._bdt.space
        if self._csf.enabled:
            self._ivt.csf_addr = self._ivt.img_addr + self._app.space
            self._csf.padding = self.BDEV[self._dev]['CSF_SIZE'] - self._csf.size
        else:
            self._ivt.csf_addr = 0
        # Set BDT section
        self._bdt.start  = self._ivt.ivt_addr - self.BDEV[self._dev]['OFFSET']
        self._bdt.length = self.size
        self._ivt.bdt_addr = self._ivt.ivt_addr + self._ivt.space

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
        assert len(data) > offset + self.BDEV[self._dev]['HEAD_SIZE']

        imx_image = False
        while offset < len(data):
            try:
                self._ivt.parse(data, offset)
            except UnparsedException:
                offset += self.BDEV[self._dev]['OFFSET']
            else:
                imx_image = True
                break

        if imx_image:
            self._ivt.padding = (self._ivt.bdt_addr - self._ivt.ivt_addr) - self._ivt.size
            self._bdt.parse(data, (offset + self._ivt.bdt_addr) - self._ivt.ivt_addr)
            img_offset = self._ivt.ivt_addr - self._bdt.start

            if self._ivt.dcd_addr > self._ivt.ivt_addr:
                self._bdt.padding = (self._ivt.dcd_addr - self._ivt.bdt_addr) - self._bdt.size
                self._dcd.parse(data, (offset + self._ivt.dcd_addr) - self._ivt.ivt_addr)
                self._dcd.padding = (self._ivt.img_addr - self._ivt.dcd_addr) - self._dcd.size
            else:
                self._bdt.padding = (self._ivt.img_addr - self._ivt.bdt_addr) - self._bdt.size

            img_start = offset + (self._ivt.img_addr - self._ivt.ivt_addr)
            if self._ivt.csf_addr > self._ivt.ivt_addr:
                csf_start = (offset + self._ivt.csf_addr) - self._ivt.ivt_addr
                self._app.data = data[img_start:csf_start]
                self._app.padding = 0
                self._csf.parse(data, csf_start)
                self._csf.padding = self._bdt.length - (csf_start + self._csf.size)
            else:
                img_end = self._bdt.length - img_offset
                self._app.data = data[img_start:img_end]
                self._app.padding = (len(data) - offset) - img_end

            #msg  = "IVT -> size: {0:d}, padding: {1:d}\n".format(self._ivt.size, self._ivt.padding)
            #msg += "BDT -> size: {0:d}, padding: {1:d}\n".format(self._bdt.size, self._bdt.padding)
            #msg += "DCD -> size: {0:d}, padding: {1:d}\n".format(self._dcd.size, self._dcd.padding)
            #msg += "APP -> size: {0:d}, padding: {1:d}\n".format(self._app.size, self._app.padding)
            #msg += "CSF -> size: {0:d}, padding: {1:d}\n".format(self._csf.size, self._csf.padding)
            #print(msg)
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
        return self._ivt.img_addr

    @address.setter
    def address(self, value):
        self._ivt.img_addr = value

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
        assert isinstance(value, SegCSF), "Value type not a segment CSF !"
        self._csf = value

    def __init__(self, addr=0, app=None, csf=None, ver=0x41):
        self._ivt = SegIVT(img_addr=addr, version=ver)
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