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

from .header import UnparsedException, CorruptedException
from .segments import SegIVT, SegBDT, SegAPP, SegDCD, SegCSF


########################################################################################################################
## IMX Image Class
########################################################################################################################

class Image(object):
    ''' IMX Image '''

    IMAGE_MIN_SIZE = 0x1000

    @property
    def address(self):
        return self._ivt.ivtAddress

    @address.setter
    def address(self, value):
        self._ivt.ivtAddress = value

    @property
    def offset(self):
        return self._offset

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

    def __init__(self, addr=0, app=None, dcd=None, csf=None, plg=None, version=0x41, offset=0x400):
        self._ivt = SegIVT(addr, version)
        self._bdt = SegBDT()
        self._app = SegAPP(app)
        self._dcd = dcd if dcd else SegDCD()
        self._csf = csf if csf else SegCSF()
        self._plg = plg
        self._offset = offset

    def __str__(self):
        return self.info()

    def __repr__(self):
        return self.info()

    def _update(self):
        self._bdt.start  = self.address - self.offset
        self._bdt.length = self.size
        self._ivt.bdtAddress = self._ivt.ivtAddress + self._ivt.space

        if self._dcd.enabled:
            self._ivt.dcdAddress = self._ivt.bdtAddress + self._bdt.space
            self._ivt.imgAddress = self._ivt.dcdAddress + self._dcd.space
        else:
            self._ivt.dcdAddress = 0
            self._ivt.imgAddress = self._ivt.bdtAddress + self._bdt.space

        if self._csf.enabled:
            self._ivt.csfAddress = self._ivt.imgAddress + self._app.space
        else:
            self._ivt.csfAddress = 0

    def info(self):
        self._update()
        # Print IVT
        msg  = "#" * 60 + "\n"
        msg += "# IVT (Image Vector Table)\n"
        msg += "#" * 60 + "\n\n"
        msg += str(self._ivt) + "\n"
        # Print DBT
        msg += "#" * 60 + "\n"
        msg += "# BDT (Boot Data Table)\n"
        msg += "#" * 60 + "\n\n"
        msg += str(self._bdt) + "\n"
        # Print DCD
        if self._dcd.enabled:
            msg += "#" * 60 + "\n"
            msg += "# DCD (Device Config Data)\n"
            msg += "#" * 60 + "\n\n"
            msg += str(self._dcd) + "\n"
        # Print CSF
        if self._csf.enabled:
            msg += "#" * 60 + "\n"
            msg += "# CSF (Code Signing Data)\n"
            msg += "#" * 60 + "\n\n"
            msg += str(self._csf) + "\n"
        return msg

    def parse(self, data, offset=0):
        assert type(data) in (str, bytes, bytearray)
        assert len(data) > offset + self.IMAGE_MIN_SIZE

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
            self._ivt.padding = (self._ivt.bdtAddress - self._ivt.ivtAddress) - self._ivt.size
            self._bdt.parse(data, (offset + self._ivt.bdtAddress) - self._ivt.ivtAddress)
            self._offset = self._bdt.start - self._ivt.ivtAddress

            if self._ivt.dcdAddress:
                self._bdt.padding = (self._ivt.dcdAddress - self._ivt.bdtAddress) - self._bdt.size
                self._dcd.parse(data, (offset + self._ivt.dcdAddress) - self._ivt.ivtAddress)
                self._dcd.padding = (self._ivt.imgAddress - self._ivt.dcdAddress) - self._dcd.size
            else:
                self._bdt.padding = (self._ivt.imgAddress - self._ivt.bdtAddress) - self._bdt.size

            img_start = (offset + self._ivt.imgAddress) - self._ivt.ivtAddress
            if self._ivt.csfAddress:
                csf_start = (offset + self._ivt.csfAddress) - self._ivt.ivtAddress
                self._app.data = data[img_start:csf_start]
                self._csf.parse(data, csf_start)
                self._csf.padding = self._bdt.length - (csf_start + self._csf.size)
            else:
                img_end = self._bdt.length - self._offset
                self._app.data = data[img_start:img_end]
                self._app.padding = len(data) - offset - img_end
        else:
            pass

    def export(self):
        self._update()
        data  = self._ivt.export(True)
        data += self._bdt.export(True)
        data += self._dcd.export(True)
        data += self._app.export(True)
        data += self._csf.export(True)
        return data
