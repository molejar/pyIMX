# Copyright (c) 2017-2018 Martin Olejar
#
# SPDX-License-Identifier: BSD-3-Clause
# The BSD-3-Clause license for this file can be found in the LICENSE file included with this distribution
# or at https://spdx.org/licenses/BSD-3-Clause.html#licenseText

from io import BytesIO, BufferedReader
from .misc import read_raw_data, read_raw_segment
from .header import Header, Header2
from .segments import SegTag, SegIVT2, SegBDT, SegAPP, SegDCD, SegCSF, SegIVT3a, SegIVT3b, SegBDS3a, SegBDS3b, \
                      SegBIC1


########################################################################################################################
# i.MX Image Public Methods
########################################################################################################################

def parse(buffer, step=0x100):
    """ Common parser for all versions of i.MX boot images
    :param buffer: stream buffer to image
    :param step: Image searching step
    :return: the object of boot image
    """
    if isinstance(buffer, (bytes, bytearray)):
        buffer = BytesIO(buffer)

    if not isinstance(buffer, (BufferedReader, BytesIO)):
        raise TypeError(" Not correct value type: \"{}\" !".format(type(buffer)))

    start_index = buffer.tell()  # Get stream start index
    buffer.seek(0, 2)            # Seek to end
    last_index = buffer.tell()   # Get stream last index
    buffer.seek(start_index, 0)  # Seek to start

    while buffer.tell() < (last_index - Header.SIZE):
        hrd = read_raw_data(buffer, Header.SIZE)
        buffer.seek(-Header.SIZE, 1)
        if   hrd[0] == SegTag.IVT2 and ((hrd[1] << 8) | hrd[2]) == SegIVT2.SIZE:
            return BootImg2.parse(buffer)
        elif hrd[0] == SegTag.IVT2 and ((hrd[1] << 8) | hrd[2]) == SegIVT3b.SIZE:
            return BootImg3b.parse(buffer)
        elif hrd[0] == SegTag.IVT3 and ((hrd[1] << 8) | hrd[2]) == SegIVT3a.SIZE:
            return BootImg3a.parse(buffer)
        elif hrd[3] == SegTag.BIC1:
            return BootImg4.parse(buffer)
        else:
            buffer.seek(step, 1)

    raise Exception(' Not an i.MX Boot Image !')


########################################################################################################################
# i.MX Boot Image Classes
########################################################################################################################

class EnumAppType:
    SCFW = 1
    M4_0 = 2
    M4_1 = 3
    APP = 4
    A35 = 4
    A53 = 4
    A72 = 5
    SCD = 6


class BootImgBase(object):
    """ IMX Boot Image Base """

    @property
    def dcd(self):
        return self._dcd

    @dcd.setter
    def dcd(self, value):
        assert isinstance(value, SegDCD), "Value type not a DCD segment !"
        self._dcd = value

    def __init__(self, address, offset):
        """ Initialize boot image object
        :param address: The start address of img in target memory
        :param offset: The IVT offset
        :return: BootImage object
        """
        self.offset = offset
        self.address = address

    def __str__(self):
        return self.info()

    def __repr__(self):
        return self.info()

    def info(self):
        raise NotImplementedError()

    def add_image(self, data, img_type, address):
        raise NotImplementedError()

    def export(self):
        raise NotImplementedError()

    @classmethod
    def parse(cls, buffer, step=0x100):
        raise NotImplementedError()


########################################################################################################################
# Boot Image V1 Segments (i.MX5)
########################################################################################################################

# Obsolete, will not be implemented


########################################################################################################################
# Boot Image V2 (i.MX6, i.MX7)
########################################################################################################################

class BootImg2(BootImgBase):
    """ IMX Boot Image v2 """

    # The value of CSF segment size
    CSF_SIZE = 0x2000
    # The align value of APP segment
    APP_ALIGN = 0x1000
    # The value of img head size
    #           offset | size
    HEAD_SIZE = {0x400: 0xC00,
                 0x100: 0x300}

    @property
    def version(self):
        return self._ivt.version

    @version.setter
    def version(self, value):
        self._ivt.version = value

    @property
    def plugin(self):
        return self._plg

    @plugin.setter
    def plugin(self, value):
        assert isinstance(value, bool)
        self._plg = value

    @property
    def ivt(self):
        return self._ivt

    @ivt.setter
    def ivt(self, value):
        assert isinstance(value, SegIVT2), "Value type not a IVT2 segment !"
        self._ivt = value

    @property
    def bdt(self):
        return self._bdt

    @bdt.setter
    def bdt(self, value):
        assert isinstance(value, SegBDT), "Value type not a BDT segment !"
        self._bdt = value

    @property
    def app(self):
        return self._app

    @app.setter
    def app(self, value):
        assert isinstance(value, SegAPP), "Value type not an APP segment !"
        self._app = value

    @property
    def csf(self):
        return self._csf

    @csf.setter
    def csf(self, value):
        assert isinstance(value, SegCSF), "Value type not a CSF segment !"
        self._csf = value

    @property
    def size(self):
        sum = self.ivt.space
        sum += self.bdt.space
        sum += self.dcd.space
        sum += self.app.space
        sum += self.csf.space
        return sum

    def __init__(self, address=0, offset=0x400, version=0x41, plugin=False):
        """ Initialize boot image object
        :param address: The start address of img in target memory
        :param offset: The IVT offset
        :param version: The version of boot img format
        :return: BootImage object
        """
        super().__init__(address, offset)
        self._ivt = SegIVT2(version)
        self._bdt = SegBDT()
        self._app = SegAPP()
        self._dcd = SegDCD()
        self._csf = SegCSF()
        self._plg = plugin

    def _update(self):
        """ Update Image Object """
        # Set zero padding for IVT and BDT sections
        self.ivt.padding = 0
        self.bdt.padding = 0
        # Calculate padding for DCD, APP and CSF sections
        tmp_val = self.ivt.space + self.bdt.space + self.dcd.size
        head_size = 0xC00 if self.offset not in self.HEAD_SIZE else self.HEAD_SIZE[self.offset]
        self.dcd.padding = head_size - tmp_val
        tmp_val = self.app.size % self.APP_ALIGN
        self.app.padding = self.APP_ALIGN - tmp_val if tmp_val > 0 else 0
        # Set IVT section
        self.ivt.ivt_address = self.address + self.offset
        self.ivt.bdt_address = self.ivt.ivt_address + self.ivt.space
        if self.dcd.enabled:
            self.ivt.dcd_address = self.ivt.bdt_address + self.bdt.space
            self.ivt.app_address = self.ivt.dcd_address + self.dcd.space
        else:
            self.ivt.dcd_address = 0
            self.ivt.app_address = self.ivt.bdt_address + self.bdt.space
        if self.csf.enabled:
            self.ivt.csf_address = self.ivt.app_address + self.app.space
            self.csf.padding = self.CSF_SIZE - self.csf.size
        else:
            self.ivt.csf_address = 0
        # Set BDT section
        self.bdt.start = self.ivt.ivt_address - self.offset
        self.bdt.length = self.size + self.offset
        self.bdt.plugin = 1 if self.plugin else 0

    def info(self):
        self._update()
        # Print IVT
        msg = "#" * 60 + "\n"
        msg += "# IVT (Image Vector Table)\n"
        msg += "#" * 60 + "\n\n"
        msg += str(self.ivt)
        # Print DBI
        msg += "#" * 60 + "\n"
        msg += "# BDI (Boot Data Info)\n"
        msg += "#" * 60 + "\n\n"
        msg += str(self.bdt)
        # Print DCD
        if self.dcd.enabled:
            msg += "#" * 60 + "\n"
            msg += "# DCD (Device Config Data)\n"
            msg += "#" * 60 + "\n\n"
            msg += str(self.dcd)
        # Print CSF
        if self.csf.enabled:
            msg += "#" * 60 + "\n"
            msg += "# CSF (Code Signing Data)\n"
            msg += "#" * 60 + "\n\n"
            msg += str(self.csf)
        return msg

    def add_image(self, data, img_type=EnumAppType.APP, address=0):
        """ Add specific image into the main boot image
        :param data: Raw data of img
        :param img_type: Type of img
        :param address: address in RAM
        """
        if img_type == EnumAppType.APP:
            self.app.data = data
            if address != 0:
                self.address = address
        else:
            raise Exception('Unknown data type !')

    def export(self):
        """ Export image as bytes array
        :return: bytes
        """
        self._update()
        data = self.ivt.export(True)
        data += self.bdt.export(True)
        data += self.dcd.export(True)
        data += self.app.export(True)
        data += self.csf.export(True)
        return data

    @classmethod
    def parse(cls, buffer, step=0x100):
        """ Parse image from stream buffer or bytes array
        :param buffer: The stream buffer or bytes array
        :param step: The
        :return: BootImg2 object
        """
        if isinstance(buffer, (bytes, bytearray)):
            buffer = BytesIO(buffer)

        if not isinstance(buffer, (BufferedReader, BytesIO)):
            raise TypeError(" Not correct value type: \"{}\" !".format(type(buffer)))

        offset = buffer.tell()          # Get stream start index
        buffer.seek(0, 2)               # Seek to end
        bufend = buffer.tell()          # Get stream last index
        buffer.seek(offset, 0)          # Seek to start
        buffer_size = bufend - offset   # Read buffer size

        imx_image = False
        while buffer.tell() < (buffer_size - Header.SIZE):
            header = Header.parse(read_raw_data(buffer, Header.SIZE))
            buffer.seek(-Header.SIZE, 1)
            if header.tag == SegTag.IVT2 and \
               header.length == SegIVT2.SIZE and \
               header.param in (0x40, 0x41, 0x42, 0x43):
                offset = buffer.tell()
                imx_image = True
                break
            else:
                buffer.seek(step, 1)

        if not imx_image:
            raise Exception(' Not an i.MX Boot Image !')

        obj = cls()
        # Parse IVT
        obj.ivt = SegIVT2.parse(read_raw_segment(buffer, SegTag.IVT2))
        # Parse BDT
        obj.bdt = SegBDT.parse(read_raw_data(buffer, SegBDT.SIZE))
        obj.offset = obj.ivt.ivt_address - obj.bdt.start
        obj.address = obj.bdt.start
        obj.plugin = True if obj.bdt.plugin else False
        # Parse DCD
        if obj.ivt.dcd_address:
            obj.dcd = SegDCD.parse(read_raw_segment(buffer, SegTag.DCD))
            obj.dcd.padding = (obj.ivt.app_address - obj.ivt.dcd_address) - obj.dcd.size
        # Parse APP
        app_start = offset + (obj.ivt.app_address - obj.ivt.ivt_address)
        app_size = obj.ivt.csf_address - obj.ivt.app_address if obj.ivt.csf_address else \
                   obj.bdt.length - (obj.bdt.start - obj.ivt.app_address)
        app_size = buffer_size - app_start if app_size > (buffer_size - app_start) else app_size
        obj.app.data = read_raw_data(buffer, app_size, app_start)
        obj.app.padding = 0
        # Parse CSF
        #if obj.ivt.csf_address:
        #    obj.csf = SegCSF.parse(buffer)
        #    obj.csf.padding = obj.bdt.length - ((obj.ivt.csf_address - obj.ivt.ivt_address) + obj.csf.size)

        return obj


########################################################################################################################
# Boot Image V2b (i.MX8M)
########################################################################################################################

class BootImg8m(BootImgBase):
    """ IMX Boot Image """

    # The value of CSF segment size
    CSF_SIZE = 0x2000
    # The align value of APP segment
    APP_ALIGN = 0x1000
    # The value of img head size
    #           offset | size
    HEAD_SIZE = {0x400: 0xC00,
                 0x100: 0x300}

    @property
    def version(self):
        return self._ivt.version

    @version.setter
    def version(self, value):
        self._ivt.version = value

    @property
    def plugin(self):
        return self._plg

    @plugin.setter
    def plugin(self, value):
        assert isinstance(value, bool)
        self._plg = value

    @property
    def ivt(self):
        return self._ivt

    @ivt.setter
    def ivt(self, value):
        assert isinstance(value, SegIVT2), "Value type not a IVT2 segment !"
        self._ivt = value

    @property
    def bdt(self):
        return self._bdt

    @bdt.setter
    def bdt(self, value):
        assert isinstance(value, SegBDT), "Value type not a BDT segment !"
        self._bdt = value

    @property
    def app(self):
        return self._app

    @app.setter
    def app(self, value):
        assert isinstance(value, SegAPP), "Value type not an APP segment !"
        self._app = value

    @property
    def csf(self):
        return self._csf

    @csf.setter
    def csf(self, value):
        assert isinstance(value, SegCSF), "Value type not a CSF segment !"
        self._csf = value

    @property
    def size(self):
        sum = self.ivt.space
        sum += self.bdt.space
        sum += self.dcd.space
        sum += self.app.space
        sum += self.csf.space
        return sum

    def __init__(self, address=0, offset=0x400, version=0x41, plugin=False):
        """ Initialize boot image object
        :param address: The start address of img in target memory
        :param offset: The IVT offset
        :param version: The version of boot img format
        :return: BootImage object
        """
        super().__init__(address, offset)
        self._ivt = SegIVT2(version)
        self._bdt = SegBDT()
        self._app = SegAPP()
        self._dcd = SegDCD()
        self._csf = SegCSF()
        self._plg = plugin

    def _update(self):
        # Set zero padding for IVT and BDT sections
        self.ivt.padding = 0
        self.bdt.padding = 0
        # Calculate padding for DCD, APP and CSF sections
        tmp_val = self.ivt.space + self.bdt.space + self.dcd.size
        head_size = 0xC00 if self.offset not in self.HEAD_SIZE else self.HEAD_SIZE[self.offset]
        self.dcd.padding = head_size - tmp_val
        tmp_val = self.app.size % self.APP_ALIGN
        self.app.padding = self.APP_ALIGN - tmp_val if tmp_val > 0 else 0
        # Set IVT section
        self.ivt.ivt_address = self.address + self.offset
        self.ivt.bdt_address = self.ivt.ivt_address + self.ivt.space
        if self.dcd.enabled:
            self.ivt.dcd_address = self.ivt.bdt_address + self.bdt.space
            self.ivt.app_address = self.ivt.dcd_address + self.dcd.space
        else:
            self.ivt.dcd_address = 0
            self.ivt.app_address = self.ivt.bdt_address + self.bdt.space
        if self.csf.enabled:
            self.ivt.csf_address = self.ivt.app_address + self.app.space
            self.csf.padding = self.CSF_SIZE - self.csf.size
        else:
            self.ivt.csf_address = 0
        # Set BDT section
        self.bdt.start = self.ivt.ivt_address - self.offset
        self.bdt.length = self.size + self.offset
        self.bdt.plugin = 1 if self.plugin else 0

    def info(self):
        self._update()
        # Print IVT
        msg = "#" * 60 + "\n"
        msg += "# IVT (Image Vector Table)\n"
        msg += "#" * 60 + "\n\n"
        msg += str(self.ivt)
        # Print DBI
        msg += "#" * 60 + "\n"
        msg += "# BDI (Boot Data Info)\n"
        msg += "#" * 60 + "\n\n"
        msg += str(self.bdt)
        # Print DCD
        if self.dcd.enabled:
            msg += "#" * 60 + "\n"
            msg += "# DCD (Device Config Data)\n"
            msg += "#" * 60 + "\n\n"
            msg += str(self.dcd)
        # Print CSF
        if self.csf.enabled:
            msg += "#" * 60 + "\n"
            msg += "# CSF (Code Signing Data)\n"
            msg += "#" * 60 + "\n\n"
            msg += str(self.csf)
        return msg

    def add_image(self, data, img_type=EnumAppType.APP, address=0):
        """ Add specific image into the main boot image
        :param data: Raw data of img
        :param img_type: Type of img
        :param address: address in RAM
        :return:
        """
        if img_type == EnumAppType.APP:
            self.app.data = data
            if address != 0:
                self.address = address
        else:
            raise Exception('Unknown data type !')

    def export(self):
        """ Export Image as bytes array
        :return: bytes
        """
        self._update()
        data = self.ivt.export(True)
        data += self.bdt.export(True)
        data += self.dcd.export(True)
        data += self.app.export(True)
        data += self.csf.export(True)
        return data

    @classmethod
    def parse(cls, buffer, step=0x100):
        """ Parse image from stream buffer or bytes array
        :param buffer: The stream buffer or bytes array
        :param step: The
        :return: BootImg2 object
        """
        if isinstance(buffer, (bytes, bytearray)):
            buffer = BytesIO(buffer)

        if not isinstance(buffer, (BufferedReader, BytesIO)):
            raise TypeError(" Not correct value type: \"{}\" !".format(type(buffer)))

        offset = buffer.tell()          # Get stream start index
        buffer.seek(0, 2)               # Seek to end
        bufend = buffer.tell()          # Get stream last index
        buffer.seek(offset, 0)          # Seek to start
        buffer_size = bufend - offset   # Read buffer size

        imx_image = False
        while buffer.tell() < (buffer_size - Header.SIZE):
            header = Header.parse(read_raw_data(buffer, Header.SIZE))
            buffer.seek(-Header.SIZE, 1)
            if header.tag == SegTag.IVT2 and \
               header.length == SegIVT2.SIZE and \
               header.param in (0x40, 0x41, 0x42, 0x43):
                offset = buffer.tell()
                imx_image = True
                break
            else:
                buffer.seek(step, 1)

        if not imx_image:
            raise Exception(' Not an i.MX Boot Image !')

        obj = cls()
        # Parse IVT
        obj.ivt = SegIVT2.parse(read_raw_segment(buffer, SegTag.IVT2))
        # Parse BDT
        obj.bdt = SegBDT.parse(read_raw_data(buffer, SegBDT.SIZE))
        obj.offset = obj.ivt.ivt_address - obj.bdt.start
        obj.address = obj.bdt.start
        obj.plugin = True if obj.bdt.plugin else False
        # Parse DCD
        if obj.ivt.dcd_address:
            obj.dcd = SegDCD.parse(read_raw_segment(buffer, SegTag.DCD))
            obj.dcd.padding = (obj.ivt.app_address - obj.ivt.dcd_address) - obj.dcd.size
        # Parse APP
        app_start = offset + (obj.ivt.app_address - obj.ivt.ivt_address)
        app_size = obj.ivt.csf_address - obj.ivt.app_address if obj.ivt.csf_address else \
                   obj.bdt.length - (obj.bdt.start - obj.ivt.app_address)
        app_size = buffer_size - app_start if app_size > (buffer_size - app_start) else app_size
        obj.app.data = read_raw_data(buffer, app_size, app_start)
        obj.app.padding = 0
        # Parse CSF
        #if obj.ivt.csf_address:
        #    obj.csf = SegCSF.parse(buffer)
        #    obj.csf.padding = obj.bdt.length - ((obj.ivt.csf_address - obj.ivt.ivt_address) + obj.csf.size)

        return obj


########################################################################################################################
# Boot Image V3a: i.MX8QXP-A0
########################################################################################################################

class BootImg3a(BootImgBase):
    """ i.MX Boot Image v3a """

    IMG_TYPE_CSF = 0x01
    IMG_TYPE_SCD = 0x02
    IMG_TYPE_EXEC = 0x03
    IMG_TYPE_DATA = 0x04

    SCFW_FLAGS_APP = 0x01355FC4
    SCFW_FLAGS_M4_0 = 0x4a5162
    SCFW_FLAGS_M4_1 = 0x4f52a3
    SCFW_FLAGS_SCFW = 0x1

    INITIAL_LOAD_ADDR_SCU_ROM = 0x2000e000
    INITIAL_LOAD_ADDR_AP_ROM = 0x00110000
    INITIAL_LOAD_ADDR_FLEXSPI = 0x08000000

    # The value of CSF segment size
    CSF_SIZE = 0x2000
    # The align value of APP segment
    IMG_AUTO_ALIGN = 0x10
    SECTOR_SIZE = 0x200
    APP_ALIGN = 0x1200
    # The value of img head size
    #           offset | size
    HEAD_SIZE = {0x400: 0xC400,
                 0x1000: 0x1400}

    PADDING_VAL = 0x00

    COUNT_OF_CONTAINERS = 2

    @property
    def plg(self):
        return self._plg

    @plg.setter
    def plg(self, value):
        assert isinstance(value, bool)
        self._plg = value

    @property
    def ivt(self):
        return self._ivt

    @ivt.setter
    def ivt(self, value):
        assert isinstance(value, list) and isinstance(value[0], SegIVT3a), "Value must be a list of SegIVT3a !"
        self._ivt = value

    @property
    def bdt(self):
        return self._bdt

    @bdt.setter
    def bdt(self, value):
        assert isinstance(value, list) and isinstance(value[0], SegBDS3a), "Value must be a list of SegBDS3a !"
        self._bdt = value

    @property
    def app(self):
        return self._app

    @app.setter
    def app(self, value):
        self._app = value

    @property
    def csf(self):
        return self._csf

    @csf.setter
    def csf(self, value):
        assert isinstance(value, SegCSF), "Value type not a CSF segment !"
        self._csf = value

    def __init__(self, address=0, offset=0x400, version=0x43):
        """ Initialize boot image object
        :param address: The start address of img in target memory
        :param offset: The IVT offset
        :param version: The version of boot img format
        :return: BootImage object
        """
        super().__init__(address, offset)
        self._ivt = [SegIVT3a(version), SegIVT3a(version)]
        self._ivt[0].next = self._ivt[0].size
        self._ivt[0].version = 0x01
        self._ivt[1].version = 0x01
        self._bdt = [SegBDS3a(), SegBDS3a()]
        self._app = [[SegAPP() for i in range(SegBDS3a.IMAGES_MAX_COUNT)],
                     [SegAPP() for i in range(SegBDS3a.IMAGES_MAX_COUNT)]]
        self._dcd = SegDCD()
        self._csf = SegCSF()
        self._plg = False
        if not isinstance(self.address, list):
            self.address = [self.INITIAL_LOAD_ADDR_SCU_ROM, self.INITIAL_LOAD_ADDR_AP_ROM]
        self._sdc_address = 0

    @staticmethod
    def _compute_padding(size, sector_size):
        return ((size // sector_size + (size % sector_size > 0)) * sector_size) - size

    def _update(self):
        # Set zero padding for IVT and BDT sections
        for container in range(self.COUNT_OF_CONTAINERS):
            self.ivt[container].padding = 0
            self.bdt[container].padding = 0

            # Set IVT section
            self.ivt[container].ivt_address = self.address[container] + self.offset + \
                                              container * self.ivt[container].size
            self.ivt[container].bdt_address = self.ivt[container].ivt_address + \
                                              self.ivt[container].space * (self.COUNT_OF_CONTAINERS - container) + \
                                              container * self.bdt[container].size

            if container == 0:
                if self.dcd.enabled:
                    self.ivt[container].dcd_address = self.ivt[container].bdt_address + self.bdt[container].space * 2
                    if self.csf.enabled:
                        self.ivt[container].csf_address = self.ivt[container].dcd_address + self.dcd.space
                    else:
                        self.ivt[container].csf_address = 0
                else:
                    self.ivt[container].dcd_address = 0
                    if self.csf.enabled:
                        self.ivt[container].csf_address = self.ivt[container].bdt_address + \
                                                          self.bdt[container].space * 2
                    else:
                        self.ivt[container].csf_address = 0
            else:
                self.ivt[container].dcd_address = 0
                self.ivt[container].csf_address = 0

            self.app[container][0].padding = self._compute_padding(self.bdt[container].images[0].image_size,
                                                                   self.SECTOR_SIZE)
            if self.bdt[container].images_count != 0:
                self.bdt[container].boot_data_size = self.bdt[container].size
                if container == 0:
                    self.bdt[container].images[0].image_source = self.APP_ALIGN
                else:
                    last_image_index = self.bdt[container - 1].images_count - 1
                    last_image_address = self.bdt[container - 1].images[last_image_index].image_source
                    self.bdt[container].images[0].image_source = last_image_address + \
                                                                 self.app[container - 1][last_image_index].space
            for i in range(self.bdt[container].images_count - 1):
                self.bdt[container].images[i + 1].image_source = self.bdt[container].images[i].image_source + \
                                                                 self.app[container][i].space
                self.app[container][i + 1].padding = self._compute_padding(self.bdt[container].images[i + 1].image_size,
                                                                           self.SECTOR_SIZE)
            if container == self.COUNT_OF_CONTAINERS - 1:
                self.app[container][self.bdt[container].images_count - 1].padding = 0
                # Set BDT section

    def info(self):
        self._update()
        # Print IVT
        msg = "#" * 60 + "\n"
        msg += "# IVT (Image Vector Table)\n"
        msg += "#" * 60 + "\n\n"
        for index, ivt in enumerate(self.ivt):
            msg += "-" * 60 + "\n"
            msg += "- IVT[{}]\n".format(index)
            msg += "-" * 60 + "\n\n"
            msg += str(ivt)
        # Print BDI
        msg += "#" * 60 + "\n"
        msg += "# BDI (Boot Data Info)\n"
        msg += "#" * 60 + "\n\n"
        for index, bdi in enumerate(self.bdt):
            msg += "-" * 60 + "\n"
            msg += "- BDI[{}]\n".format(index)
            msg += "-" * 60 + "\n\n"
            msg += str(bdi)
        # Print DCD
        if self.dcd.enabled:
            msg += "#" * 60 + "\n"
            msg += "# DCD (Device Config Data)\n"
            msg += "#" * 60 + "\n\n"
            msg += str(self.dcd)
        # Print CSF
        if self.csf.enabled:
            msg += "#" * 60 + "\n"
            msg += "# CSF (Code Signing Data)\n"
            msg += "#" * 60 + "\n\n"
            msg += str(self.csf)
        return msg

    def add_image(self, data, img_type=EnumAppType.APP, address=0):
        """ Add specific image into the main boot image
        :param data: Raw data of image
        :param img_type: Type of image
        :param address: address in RAM
        :return:
        """
        if img_type == EnumAppType.A35:
            image_index = self.bdt[1].images_count
            self.bdt[1].images[image_index].image_destination = address
            self.bdt[1].images[image_index].image_entry = address
            self.bdt[1].images[image_index].image_size = len(data)
            self.bdt[1].images[image_index].rom_flags = 0
            self.bdt[1].images[image_index].hab_flags = self.IMG_TYPE_EXEC
            self.bdt[1].images[image_index].scfw_flags = self.SCFW_FLAGS_APP
            self.bdt[1].images_count += 1

            self.app[1][image_index].data = data
            self.app[1][image_index].padding = self._compute_padding(len(data), self.SECTOR_SIZE)

        elif img_type == EnumAppType.M4_0 or img_type == EnumAppType.M4_1:
            image_index = self.bdt[0].images_count
            self.bdt[0].images[image_index].image_destination = address
            self.bdt[0].images[image_index].image_entry = address
            self.bdt[0].images[image_index].image_size = len(data)
            self.bdt[0].images[image_index].rom_flags = 0
            self.bdt[0].images[image_index].hab_flags = self.IMG_TYPE_EXEC
            self.bdt[0].images[image_index].scfw_flags = self.SCFW_FLAGS_M4_0 if img_type == EnumAppType.M4_0 else \
                self.SCFW_FLAGS_M4_1
            self.bdt[0].images_count += 1

            self.app[0][image_index].data = data
            self.app[0][image_index].padding = self._compute_padding(len(data), self.SECTOR_SIZE)

        elif img_type == EnumAppType.SCFW:
            image_index = self.bdt[0].images_count
            self.bdt[0].images[image_index].image_destination = 0x1ffe0000
            self.bdt[0].images[image_index].image_entry = 0x1ffe0000
            self.bdt[0].images[image_index].image_size = len(data)
            self.bdt[0].images[image_index].rom_flags = 0
            self.bdt[0].images[image_index].hab_flags = self.IMG_TYPE_EXEC
            self.bdt[0].images[image_index].scfw_flags = self.SCFW_FLAGS_SCFW
            self.bdt[0].images_count += 1

            self.app[0][image_index].data = data
            self.app[0][image_index].padding = self._compute_padding(len(data), self.SECTOR_SIZE)
            self._sdc_address = self.bdt[0].images[image_index].image_destination + len(data) + \
                                self._compute_padding(len(data), self.IMG_AUTO_ALIGN)

        elif img_type == EnumAppType.SCD:
            if self._sdc_address == 0:
                raise Exception('SCFW have to be define before SCD !')
            image_index = self.bdt[0].images_count
            self.bdt[0].images[image_index].image_destination = self._sdc_address
            self.bdt[0].images[image_index].image_entry = 0
            self.bdt[0].images[image_index].image_size = len(data)
            self.bdt[0].images[image_index].rom_flags = 0
            self.bdt[0].images[image_index].hab_flags = self.IMG_TYPE_SCD
            self.bdt[0].images[image_index].scfw_flags = 0x1
            self.bdt[0].images_count += 1

            self._app[0][image_index].data = data
            self._app[0][image_index].padding = self._compute_padding(len(data), self.SECTOR_SIZE)

        else:
            raise Exception('Unknown data type !')

    def export(self):
        ''' Export Image as binary blob
        :return:
        '''
        self._update()
        data = bytes()
        data += self.ivt[0].export(True)
        data += self.ivt[1].export(True)
        data += self.bdt[0].export(True)
        data += self.bdt[1].export(True)
        data += self.dcd.export(True)
        data += self.csf.export(True)
        data += bytes([self.PADDING_VAL] * self._compute_padding(len(data), self.APP_ALIGN - self.offset))

        for container in range(self.COUNT_OF_CONTAINERS):
            for image in range(self.bdt[container].images_count):
                data += self.app[container][image].export(True)

        return data

    @classmethod
    def parse(cls, buffer, step=0x100):
        """
        :param buffer:
        :param ivt_offset:
        :return:
        """
        if isinstance(buffer, (bytes, bytearray)):
            buffer = BytesIO(buffer)

        if not isinstance(buffer, (BufferedReader, BytesIO)):
            raise TypeError(" Not correct value type: \"{}\" !".format(type(buffer)))

        offset = buffer.tell()          # Get stream start index
        buffer.seek(0, 2)               # Seek to end
        bufend = buffer.tell()          # Get stream last index
        buffer.seek(offset, 0)          # Seek to start
        buffer_size = bufend - offset   # Read buffer size

        imx_image = False
        while buffer.tell() < (buffer_size - Header.SIZE):
            header = Header.parse(read_raw_data(buffer, Header.SIZE))
            buffer.seek(-Header.SIZE, 1)
            if header.tag == SegTag.IVT3 and \
               header.length == SegIVT3a.SIZE and \
               header.param in (0x43,):
                offset = buffer.tell()
                imx_image = True
                break
            else:
                buffer.seek(step, 1)

        if not imx_image:
            raise Exception(' Not an i.MX Boot Image !')

        obj = cls()
        # Parse IVT
        obj.ivt[0] = SegIVT3a.parse(read_raw_segment(buffer, SegTag.IVT3))
        obj.ivt[1] = SegIVT3a.parse(read_raw_segment(buffer, SegTag.IVT3))
        # Parse BDT
        obj.bdt[0] = SegBDS3a.parse(read_raw_data(buffer, SegBDS3a.SIZE))
        obj.bdt[1] = SegBDS3a.parse(read_raw_data(buffer, SegBDS3a.SIZE))
        # Parse DCD
        if obj.ivt[0].dcd_address:
            buffer.seek(offset + (obj.ivt[0].dcd_address - obj.ivt[0].ivt_address), 0)
            obj.dcd = SegDCD.parse(read_raw_segment(buffer, SegTag.DCD))
        # Parse CSF
        if obj.ivt[0].csf_address:
            buffer.seek(offset + (obj.ivt[0].csf_address - obj.ivt[0].ivt_address), 0)
            obj.csf = SegCSF.parse(read_raw_segment(buffer, SegTag.CSF))
        # Parse IMAGES
        for container in range(obj.COUNT_OF_CONTAINERS):
            for i in range(obj.bdt[container].images_count):
                buffer.seek(obj.bdt[container].images[i].image_source - obj.offset + offset, 0)
                obj.app[container][i].data = read_raw_data(buffer, obj.bdt[container].images[i].image_size)

        return obj


########################################################################################################################
# Boot Image V3b: i.MX8QM-A0
########################################################################################################################

class BootImg3b(BootImgBase):
    """ IMX Boot Image v3b """

    IMG_TYPE_CSF = 0x01
    IMG_TYPE_SCD = 0x02
    IMG_TYPE_EXEC = 0x03
    IMG_TYPE_DATA = 0x04

    SCFW_FLAGS_A53 = 0x1354014
    SCFW_FLAGS_A72 = 0x1354065
    SCFW_FLAGS_M4_0 = 0x4a5162
    SCFW_FLAGS_M4_1 = 0x4f52a3
    SCFW_FLAGS_SCFW = 0x1

    INITIAL_LOAD_ADDR_SCU_ROM = 0x2000e000
    INITIAL_LOAD_ADDR_AP_ROM = 0x00110000
    INITIAL_LOAD_ADDR_FLEXSPI = 0x08000000

    # The value of CSF segment size
    CSF_SIZE = 0x2000
    # The align value for img
    IMG_AUTO_ALIGN = 0x10
    # The align value for sector
    SECTOR_SIZE = 0x200
    # The align value of APP segment
    APP_ALIGN = 0x1200

    PADDING_VAL = 0x00
    # The value of img head size
    #           offset | size
    HEAD_SIZE = {0x400:  0xC400,
                 0x1000: 0x1400}

    COUNT_OF_CONTAINERS = 2

    @property
    def plg(self):
        return self._plg

    @plg.setter
    def plg(self, value):
        assert isinstance(value, bool)
        self._plg = value

    @property
    def ivt(self):
        return self._ivt

    @ivt.setter
    def ivt(self, value):
        assert isinstance(value, list)
        assert len(value) == self.COUNT_OF_CONTAINERS
        assert isinstance(value[0], SegIVT3b), "Value must be a list of SegIVT3b !"
        self._ivt = value

    @property
    def bdt(self):
        return self._bdt

    @bdt.setter
    def bdt(self, value):
        assert isinstance(value, list)
        assert len(value) == self.COUNT_OF_CONTAINERS
        assert isinstance(value[0], SegBDS3b), "Value must be a list of SegBDS3b !"
        self._bdt = value

    @property
    def app(self):
        return self._app

    @app.setter
    def app(self, value):
        self._app = value

    @property
    def scd(self):
        return self._scd

    @scd.setter
    def scd(self, value):
        self._scd = value

    @property
    def csf(self):
        return self._csf

    @csf.setter
    def csf(self, value):
        assert isinstance(value, SegCSF), "Value type not a CSF segment !"
        self._csf = value

    def __init__(self, address=0, offset=0x400, version=0x43):
        """ Initialize boot image object
        :param address: The start address of img in target memory
        :param offset: The IVT offset
        :param version: The version of boot img format
        :return: BootImage object
        """
        super().__init__(address, offset)
        self._ivt = [SegIVT3b(version), SegIVT3b(version)]
        self._bdt = [SegBDS3b(), SegBDS3b()]
        self._app = [[SegAPP() for _ in range(SegBDS3b.IMAGES_MAX_COUNT)],
                     [SegAPP() for _ in range(SegBDS3b.IMAGES_MAX_COUNT)]]
        self._dcd = SegDCD()
        self._scd = SegAPP()
        self._csf = SegCSF()
        self._plg = False
        self._scd_address = 0
        if not isinstance(self.address, list):
            self.address = [self.INITIAL_LOAD_ADDR_SCU_ROM, self.INITIAL_LOAD_ADDR_AP_ROM]

    @staticmethod
    def _compute_padding(image_size, sector_size):
        return ((image_size // sector_size + (image_size % sector_size > 0)) * sector_size) - image_size

    def _update(self):
        # Set zero padding for IVT and BDT sections
        for container in range(self.COUNT_OF_CONTAINERS):
            self.ivt[container].padding = 0
            self.bdt[container].padding = 0

            # Set IVT section
            self.ivt[container].ivt_address = self.address[container] + self.offset + \
                                              container * self.ivt[container].size
            self.ivt[container].bdt_address = self.ivt[container].ivt_address + \
                                              self.ivt[container].space * (2 - container) + \
                                              container * self.bdt[container].size
            if container == 0:
                if self.dcd.enabled:
                    self.ivt[container].dcd_address = self.ivt[container].bdt_address + self.bdt[container].space * 2
                    if self.csf.enabled:
                        self.ivt[container].csf_address = self.ivt[container].dcd_address + self.dcd.space
                    else:
                        self.ivt[container].csf_address = 0
                else:
                    self.ivt[container].dcd_address = 0
                    if self.csf.enabled:
                        self.ivt[container].csf_address = self.ivt[container].bdt_address + \
                                                          self.bdt[container].space * 2
                    else:
                        self.ivt[container].csf_address = 0
            else:
                self.ivt[container].dcd_address = 0
                self.ivt[container].csf_address = 0

            self.app[container][0].padding = self._compute_padding(self.bdt[container].images[0].image_size,
                                                                   self.SECTOR_SIZE)
            if self.bdt[container].images_count != 0:
                self.bdt[container].boot_data_size = self.bdt[container].size
                if container == 0:
                    self.bdt[container].images[0].image_source = self.APP_ALIGN
                else:
                    last_image_index = self.bdt[container - 1].images_count - 1
                    last_image_address = self.bdt[container - 1].images[last_image_index].image_source
                    self.bdt[container].images[0].image_source = last_image_address + \
                                                                 self.app[container - 1][last_image_index].space
            next_image_address = 0
            for i in range(self.bdt[container].images_count - 1):
                self.bdt[container].images[i + 1].image_source = self.bdt[container].images[i].image_source + \
                                                                 self.app[container][i].space
                self.app[container][i + 1].padding = self._compute_padding(
                    self.bdt[container].images[i + 1].image_size, self.SECTOR_SIZE)
                next_image_address = self.bdt[container].images[i + 1].image_source + self.app[container][i + 1].space

            if container == 0:
                if self.bdt[container].scd.image_destination != 0:
                    self.bdt[container].scd.image_source = next_image_address
                    self.scd.padding = self._compute_padding(self.bdt[0].scd.image_size, self.SECTOR_SIZE)
                    next_image_address += self.scd.space
                    # Set BDT section

                if self.csf.enabled:
                    self.bdt[container].csf.image_source = next_image_address
                    self.csf.padding = self._compute_padding(self.bdt[0].csf.image_size, self.SECTOR_SIZE)
                    next_image_address += self.csf.space
                    # Set BDT section

    def info(self):
        self._update()
        # Print IVT
        msg = "#" * 60 + "\n"
        msg += "# IVT (Image Vector Table)\n"
        msg += "#" * 60 + "\n\n"
        for index, ivt in enumerate(self.ivt):
            msg += "-" * 60 + "\n"
            msg += "- IVT[{}]\n".format(index)
            msg += "-" * 60 + "\n\n"
            msg += str(ivt)
        # Print BDI
        msg += "#" * 60 + "\n"
        msg += "# BDI (Boot Data Info)\n"
        msg += "#" * 60 + "\n\n"
        for index, bdi in enumerate(self.bdt):
            msg += "-" * 60 + "\n"
            msg += "- BDI[{}]\n".format(index)
            msg += "-" * 60 + "\n\n"
            msg += str(bdi)
        # Print DCD
        if self.dcd.enabled:
            msg += "#" * 60 + "\n"
            msg += "# DCD (Device Config Data)\n"
            msg += "#" * 60 + "\n\n"
            msg += str(self.dcd)
        # Print CSF
        if self.csf.enabled:
            msg += "#" * 60 + "\n"
            msg += "# CSF (Code Signing Data)\n"
            msg += "#" * 60 + "\n\n"
            msg += str(self.csf)
        return msg

    def add_image(self, data, img_type=EnumAppType.APP, address=0):
        """ Add specific image into the main boot image
        :param data: Raw data of image
        :param img_type: Type of image
        :param address: address in RAM
        """
        if img_type == EnumAppType.A53 or img_type == EnumAppType.A72:
            image_index = self.bdt[1].images_count
            self.app[1][image_index].data = data

            self.bdt[1].images[image_index].image_destination = address
            self.bdt[1].images[image_index].image_entry = address
            self.bdt[1].images[image_index].image_size = len(data)

            if img_type == EnumAppType.A53:
                self.bdt[1].images[image_index].flags = self.SCFW_FLAGS_A53
            elif img_type == EnumAppType.A72:
                self.bdt[1].images[image_index].flags = self.SCFW_FLAGS_A72

            self.app[1][image_index].padding = self._compute_padding(len(data), self.SECTOR_SIZE)
            self.bdt[1].images_count += 1

        elif img_type == EnumAppType.M4_0 or img_type == EnumAppType.M4_1:
            image_index = self.bdt[0].images_count
            self.app[0][image_index].data = data

            self.bdt[0].images[image_index].image_destination = address
            self.bdt[0].images[image_index].image_entry = address
            self.bdt[0].images[image_index].image_size = len(data)

            if img_type == EnumAppType.M4_0:
                self.bdt[0].images[image_index].flags = self.SCFW_FLAGS_M4_0
            elif img_type == EnumAppType.M4_1:
                self.bdt[0].images[image_index].flags = self.SCFW_FLAGS_M4_1

            self.app[0][image_index].padding = ((len(data) // self.SECTOR_SIZE + (
                len(data) % self.SECTOR_SIZE > 0)) * self.SECTOR_SIZE) - len(data)
            self.bdt[0].images_count += 1

        elif img_type == EnumAppType.SCFW:
            image_index = self.bdt[0].images_count
            self.bdt[0].images[image_index].image_destination = 0x30fe0000
            self.bdt[0].images[image_index].image_entry = 0x1ffe0000
            self.bdt[0].images[image_index].image_size = len(data)
            self.bdt[0].images[image_index].flags = self.SCFW_FLAGS_SCFW
            self._scd_address = self.bdt[0].images[image_index].image_destination + len(data) + \
                                self._compute_padding(len(data), self.IMG_AUTO_ALIGN)
            self.bdt[0].images_count += 1

            self.app[0][image_index].data = data
            self.app[0][image_index].padding = self._compute_padding(len(data), self.SECTOR_SIZE)

        elif img_type == EnumAppType.SCD:
            if self._scd_address == 0:
                raise Exception('SCFW have to be define before SCD !')
            self.scd.data = data
            self.scd.padding = self._compute_padding(len(data), self.SECTOR_SIZE)
            self.bdt[0].scd.image_destination = self._scd_address
            self.bdt[0].scd.image_entry = 0
            self.bdt[0].scd.image_size = len(data)
            self.ivt[0].scd_address = self.bdt[0].scd.image_destination

        else:
            raise Exception(' Unknown image type !')

    def export(self):
        self._update()
        # data = bytearray(self._offset)
        data = bytes()
        data += self.ivt[0].export(True)
        data += self.ivt[1].export(True)
        data += self.bdt[0].export(True)
        data += self.bdt[1].export(True)
        data += self.dcd.export(True)
        data += bytes([self.PADDING_VAL] * self._compute_padding(len(data), self.APP_ALIGN - self.offset))

        for container in range(self.COUNT_OF_CONTAINERS):
            for i in range(self.bdt[container].images_count):
                data += self.app[container][i].export(True)

        if self.bdt[0].scd.image_source != 0:
            data += self.scd.export(True)

        if self.bdt[0].csf.image_source != 0:
            data += self.csf.export(True)

        return data

    @classmethod
    def parse(cls, buffer, step=0x100):
        """ Parse
        :param buffer:
        :param step:
        :return:
        """
        if isinstance(buffer, (bytes, bytearray)):
            buffer = BytesIO(buffer)

        if not isinstance(buffer, (BufferedReader, BytesIO)):
            raise TypeError(" Not correct value type: \"{}\" !".format(type(buffer)))

        offset = buffer.tell()          # Get stream start index
        buffer.seek(0, 2)               # Seek to end
        bufend = buffer.tell()          # Get stream last index
        buffer.seek(offset, 0)          # Seek to start
        buffer_size = bufend - offset   # Read buffer size

        imx_image = False
        while buffer.tell() < (buffer_size - Header.SIZE):
            header = Header.parse(read_raw_data(buffer, Header.SIZE))
            buffer.seek(-Header.SIZE, 1)
            if header.tag == SegTag.IVT2 and \
               header.length == SegIVT3b.SIZE and \
               header.param in (0x43,):
                offset = buffer.tell()
                imx_image = True
                break
            else:
                buffer.seek(step, 1)

        if not imx_image:
            raise Exception(' Not an i.MX Boot Image !')

        obj = cls()
        # Parse IVT
        obj.ivt[0] = SegIVT3b.parse(read_raw_segment(buffer, SegTag.IVT2))
        obj.ivt[1] = SegIVT3b.parse(read_raw_segment(buffer, SegTag.IVT2))
        # Parse BDT
        obj.bdt[0] = SegBDS3b.parse(read_raw_data(buffer, SegBDS3b.SIZE))
        obj.bdt[1] = SegBDS3b.parse(read_raw_data(buffer, SegBDS3b.SIZE))
        # Parse DCD
        if obj.ivt[0].dcd_address:
            buffer.seek(offset + (obj.ivt[0].dcd_address - obj.ivt[0].ivt_address), 0)
            obj.dcd = SegDCD.parse(read_raw_segment(buffer, SegTag.DCD))
        # Parse IMAGES
        for container in range(obj.COUNT_OF_CONTAINERS):
            for i in range(obj.bdt[container].images_count):
                buffer.seek(obj.bdt[container].images[i].image_source - obj.offset + offset, 0)
                obj.app[container][i].data = read_raw_data(buffer, obj.bdt[container].images[i].image_size)
        # Parse SCD
        if obj.bdt[0].scd.image_source != 0:
            buffer.seek(obj.bdt[0].scd.image_source - obj.offset + offset, 0)
            obj.scd.data = read_raw_data(buffer, obj.bdt[0].scd.image_size)
        # Parse CSF
        if obj.bdt[0].csf.image_source != 0:
            buffer.seek(obj.bdt[0].csf.image_source - obj.offset + offset, 0)
            obj.csf = SegCSF.parse(read_raw_segment(buffer, SegTag.CSF))

        return obj


########################################################################################################################
# Boot Image V4: i.MX8DM, i.MX8QM_B0, i.MX8QXP_B0
########################################################################################################################

class BootImg4(BootImgBase):
    """ i.MX Boot Image v4 """

    def __init__(self, address=0, offset=0x400):
        """ Initialize boot image object
        :param address: The start address of image in target memory
        :param offset: The image offset
        :return: BootImage object
        """
        super().__init__(address, offset)
        self._dcd = SegDCD()
        self._cont1_header = SegBIC1()
        self._cont2_header = SegBIC1()
        self._cont1_data = []
        self._cont2_data = []

    def _update(self):
        pass

    def info(self):
        self._update()
        msg = ""
        msg += "#" * 60 + "\n"
        msg += "# Boot Images Container 1\n"
        msg += "#" * 60 + "\n\n"
        msg += self._cont1_header.info()
        msg += "#" * 60 + "\n"
        msg += "# Boot Images Container 2\n"
        msg += "#" * 60 + "\n\n"
        msg += self._cont2_header.info()
        if self.dcd.enabled:
            msg += "#" * 60 + "\n"
            msg += "# DCD (Device Config Data)\n"
            msg += "#" * 60 + "\n\n"
            msg += self.dcd.info()
        return msg

    def add_image(self, data, img_type, address):
        raise NotImplementedError()

    def export(self):
        self._update()
        data = bytes()
        data += self._cont1_header.export(True)
        data += self._cont2_header.export(True)
        # TODO: Complete Implementation
        return data

    @classmethod
    def parse(cls, buffer, step=0x100):
        if isinstance(buffer, (bytes, bytearray)):
            buffer = BytesIO(buffer)

        if not isinstance(buffer, (BufferedReader, BytesIO)):
            raise TypeError(" Not correct value type: \"{}\" !".format(type(buffer)))

        offset = buffer.tell()          # Get stream start index
        buffer.seek(0, 2)               # Seek to end
        bufend = buffer.tell()          # Get stream last index
        buffer.seek(offset, 0)          # Seek to start
        buffer_size = bufend - offset   # Read buffer size

        imx_image = False
        while buffer.tell() < (buffer_size - Header2.SIZE):
            header = Header2.parse(read_raw_data(buffer, Header2.SIZE))
            buffer.seek(-Header2.SIZE, 1)
            if header.tag == SegTag.BIC1:
                offset = buffer.tell()
                imx_image = True
                break
            else:
                buffer.seek(step, 1)

        if not imx_image:
            raise Exception(' Not an i.MX Boot Image !')

        obj = cls()
        # Parse Containers
        obj._cont1_header = SegBIC1.parse(read_raw_data(buffer, 0x400))
        obj._cont2_header = SegBIC1.parse(read_raw_data(buffer, 0x400))
        # TODO: Complete Implementation
        return obj


########################################################################################################################
# i.MX Kernel Image Classes
########################################################################################################################

class KernelImg(object):
    """ IMX Kernel Image """

    IMAGE_MIN_SIZE = 0x1000

    @property
    def address(self):
        return self._ivt.app_address

    @address.setter
    def address(self, value):
        self._ivt.app_address = value

    @property
    def version(self):
        return self._ivt.version

    @version.setter
    def version(self, value):
        self._ivt.version = value

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
        self._ivt = SegIVT2(version)
        self._ivt.app_address = address
        self._app = SegAPP(app)
        self._csf = SegCSF() if csf is None else csf

    def __str__(self):
        return self.info()

    def __repr__(self):
        return self.info()

    def _update(self):
        pass

    def info(self):
        pass

    def export(self):
        self._update()
        data = self._app.export(True)
        data += self._ivt.export(True)
        data += self._csf.export(True)
        return data

    @classmethod
    def parse(cls, data):
        assert type(data) in (str, bytes, bytearray)
        assert len(data) > cls.IMAGE_MIN_SIZE
        pass
