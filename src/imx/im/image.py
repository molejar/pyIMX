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

from .header import Header, UnparsedException, CorruptedException
from .segments import SegIVT, SegBDT, SegDCD, SegAPP, SegCSF


########################################################################################################################
## IMX Image Class
########################################################################################################################

class Image(object):

    @property
    def ivt(self):
        return self._ivt

    @property
    def bdt(self):
        return self._bdt

    @property
    def dcd(self):
        return self._dcd

    @property
    def app(self):
        return self._app

    @property
    def csf(self):
        return self._csf

    @property
    def memory(self):
        return self._memory

    @memory.setter
    def memory(self, value):
        self._memory = value

    @property
    def size(self):
        sum  = self._ivt.space
        sum += self._bdt.space
        sum += self._dcd.space
        sum += self._app.space
        sum += self._csf.space
        return sum

    def __init__(self):
        self._memory = 0
        self._ivt = SegIVT()
        self._bdt = SegBDT()
        self._dcd = SegDCD()
        self._app = SegAPP()
        self._csf = SegCSF()

    def __str__(self):
        return self.info()

    def __repr__(self):
        return self.info()

    def info(self):
        msg  = str(self._ivt)
        msg += str(self._bdt)
        msg += str(self._app)
        if self.ivt.dcd > self.ivt.itself:
            msg += str(self._dcd)
        if self.ivt.csf > self.ivt.itself:
            msg += str(self._csf)
        return msg

    def parse(self, data, offset=0):
        assert type(data) in (str, bytes, bytearray)
        assert len(data) > offset + 0x1000

        imx_image = False
        while offset < len(data):
            try:
                self.ivt.parse(data, offset)
            except UnparsedException:
                offset += 0x400
            else:
                imx_image = True
                break

        if imx_image:
            self.bdt.parse(data, offset + self.ivt.bdt - self.ivt.itself)
            if self.ivt.dcd > self.ivt.itself:
                self.dcd.parse(data, offset + self.ivt.dcd - self.ivt.itself)
            if self.ivt.csf > self.ivt.itself:
                app_offset = offset + self.ivt.entry - self.ivt.itself
                csf_offset = offset + self.ivt.csf - self.ivt.itself
                self.csf.parse(data, csf_offset)
                self.app.parse(data[app_offset:csf_offset])
            else:
                self.app.parse(data, offset + self.ivt.entry - self.ivt.itself)
        else:
            pass

    def export(self):
        data = self.ivt.export()
        data += self.bdt.export()
        data += self.dcd.export()
        data += self.app.export()
        data += self.csf.export()
        return data
