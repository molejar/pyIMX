#!/usr/bin/env python

# Copyright (c) 2017 Martin Olejar
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

import os
import sys
import click
import struct
import logging
import traceback
import imx


########################################################################################################################
## Misc
########################################################################################################################


def hexdump(data, saddr=0, compress=True, length=16, sep='.'):
    """ Return string array in hex dump.format
    :param data:     {List} The data array of {Bytes}
    :param saddr:    {Int}  Absolute Start Address
    :param compress: {Bool} Compressed output (remove duplicated content, rows)
    :param length:   {Int}  Number of Bytes for row (max 16).
    :param sep:      {Char} For the text part, {sep} will be used for non ASCII char.
    """
    result = []

    # The max line length is 16 bytes
    if length > 16: length = 16

    # Create header
    header = '  ADDRESS | '
    for i in range(0, length):
        header += "{0:02X} ".format(i)
    header += '| '
    for i in range(0, length):
        header += "{0:X}".format(i)
    result.append(header)
    result.append((' ' + '-' * (13 + 4 * length)))

    # Check address align
    offset = saddr % length
    address = saddr - offset
    align = True if (offset > 0) else False

    # Print flags
    prev_line = None
    print_mark = True

    # process data
    for i in range(0, len(data) + offset, length):

        hexa = ''
        if align:
            subSrc = data[0: length - offset]
        else:
            subSrc = data[i - offset: i + length - offset]
            if compress:
                # compress output string
                if subSrc == prev_line:
                    if print_mark:
                        print_mark = False
                        result.append(' *')
                    continue
                else:
                    prev_line = subSrc
                    print_mark = True

        if align:
            hexa += '   ' * offset

        for h in range(0, len(subSrc)):
            h = subSrc[h]
            if not isinstance(h, int):
                h = ord(h)
            hexa += "{0:02X} ".format(h)

        text = ''
        if align:
            text += ' ' * offset

        for c in subSrc:
            if not isinstance(c, int):
                c = ord(c)
            if 0x20 <= c < 0x7F:
                text += chr(c)
            else:
                text += sep

        result.append((' %08X | %-' + str(length * 3) + 's| %s') % (address + i, hexa, text))
        align = False

    result.append((' ' + '-' * (13 + 4 * length)))
    return '\n'.join(result)


########################################################################################################################
## HAB Parser
########################################################################################################################

# mx6Codes from Analog Digprog register
# [mx6DQ, mx6SDL, mx6SL, mx6SX, mx6UL, mx6ULL]
mx6Codes = [0x63, 0x61, 0x60, 0x62, 0x64, 0x65]
mx7Codes = [0x72]

# Create list of ROM addresses for reading USB VID/PID
# Search elf file for a2 15 or c9 1f subtract elf offset (0x38 or 0x60 or 0x34)
def get_rom_info(dev_name):

    # RELEASE -> The ROM code official releases number
    # PIDADDR -> The absolute address of USB-PID value in ROM code
    # VERADDR -> The absolute address of silicon revision value in ROM code
    ROMVER = {
        'MX6DQP':  {
            'RELEASE': ('01.01.01', '01.02.00', '01.03.00', '01.04.01', '01.05.02', '02.00.02'),
            'PIDADDR': (0x0001108C, 0x00011130, 0x000111E4, 0x000112A0, 0x00011330, 0x000115B8),
            'VERADDR':  0x00000048,
            'DEVTYPE':  6
        },
        'MX6SDL':   {
            'RELEASE': ('00.00.05', '01.01.02', '01.02.02', '01.03.00'),
            'PIDADDR': (0x00010E28, 0x0001108C, 0x000111AC, 0x000111CC),
            'VERADDR':  0x00000048,
            'DEVTYPE':  6
        },
        'MX6SL':   {
            'RELEASE': ('01.00.01', '01.02.00', '01.03.00'),
            'PIDADDR': (0x0000E0B0, 0x0000E210, 0x0000E2C2),
            'VERADDR':  0x00000048,
            'DEVTYPE':  6
        },
        'MX6SX':  {
            'RELEASE': ('01.00.02', '01.01.01'),
            'PIDADDR': (0x00012398, 0x00013124),
            'VERADDR':  0x00000080,
            'DEVTYPE':  6
        },
        'MX6UL':  {
            'RELEASE': ('01.00.00', '01.01.00'),
            'PIDADDR': (0x000129C4, 0x00012A04),
            'VERADDR':  0x00000080,
            'DEVTYPE':  6
        },
        'MX6ULL': {
            'RELEASE': ('01.00.01',),
            'PIDADDR': (0x00010E84,),
            'VERADDR':  0x00000080,
            'DEVTYPE':  6
        },
        'MX7SD':   {
            'RELEASE': ('01.00.05', '01.01.01'),
            'PIDADDR': (0x000130A0, 0x000130A0),
            'VERADDR':  0x00000080,
            'DEVTYPE':  7
        },
        'MX6SLL': {
            'RELEASE': ('01.00.00',),
            'PIDADDR': (0x0000F884,),
            'VERADDR':  0x00000080,
            'DEVTYPE':  6
        },
        'VIBRID': {
            'RELEASE': ('01.00.10',),
            'PIDADDR': (0x0000F884,),
            'VERADDR':  0x00000048,
            'DEVTYPE':  6
        },
    }

    retval = None

    if dev_name in ROMVER:
        retval = ROMVER[dev_name]

    return retval


def get_dev_info(dev_name, rom_ver):
    # Create List of details for each device
    # 0 - Analog Digprog Address
    # 1 - SBMR1 Address
    # 2 - SBMR2 Address
    # 3 - Persist Reg Address
    # 4 - WDOG Fuse Address
    # 5 - Free Space Address
    # 6 - Log Buffer Address

    if dev_name == 'MX6DQP':
        if rom_ver >= 0x20:
            desc = 'iMX6 Dual/Quad Plus'
            regs = (0x020C8260, 0x020D8004, 0x020D801C, 0x020D8044, 0x021BC460, 0x00907000, 0x00902190)
        elif rom_ver < 0x15:
            desc = 'iMX6 Dual/Quad'
            regs = (0x020C8260, 0x020D8004, 0x020D801C, 0x020D8044, 0x021BC460, 0x00907000, 0x00902190)
        else:
            desc = 'iMX6 Dual/Quad'
            regs = (0x020C8260, 0x020D8004, 0x020D801C, 0x020D8044, 0x021BC460, 0x00907000, 0x00902190)
    elif dev_name == 'MX6SDL':
        if rom_ver > 0x11:
            desc = 'iMX6 Solo/DualLite'
            regs = (0x020C8260, 0x020D8004, 0x020D801C, 0x020D8044, 0x021BC460, 0x00907000, 0x00901AB8)
        else:
            desc = 'iMX6 Solo/DualLite'
            regs = (0x020C8260, 0x020D8004, 0x020D801C, 0x020D8044, 0x021BC460, 0x00907000, 0x00901AB8)
    elif dev_name == 'MX6SL':
        desc     = 'iMX6 SoloLite'
        regs     = (0x020C8280, 0x020D8004, 0x020D801C, 0x020D8044, 0x021BC460, 0x00907000, 0x00901948)
    elif dev_name == 'MX6SX':
        desc     = 'iMX6 SoloX'
        if rom_ver < 0x11:
            regs = (0x020C8260, 0x020D8004, 0x020D801C, 0x020D8044, 0x021BC460, 0x00907000, 0x00901BE4)
        else:
            regs = (0x020C8260, 0x020D8004, 0x020D801C, 0x020D8044, 0x021BC460, 0x00907000, 0x00901CD8)
    elif dev_name == 'MX6UL':
        desc     = 'iMX6 UltraLite'
        regs     = (0x020C8260, 0x020D8004, 0x020D801C, 0x020D8044, 0x021BC460, 0x00907000, 0x00901D14)
    elif dev_name == 'MX6ULL':
        desc     = 'iMX6 UltraLiteLite'
        regs     = (0x020C8280, 0x020D8004, 0x020D801C, 0x020D8044, 0x021BC460, 0x00907000, 0x00901CF4)
    elif dev_name == 'MX7SD':
        desc     = 'iMX7 Solo/Dual'
        if rom_ver < 0x11:
            regs = (0x30360800, 0x30390058, 0x30390070, 0x30390098, 0x30350480, 0x00910000, 0x00909150)
        else:
            regs = (0x30360800, 0x30390058, 0x30390070, 0x30390098, 0x30350480, 0x00910000, 0x0090915C)
    elif dev_name == 'MX6SLL':
        desc = 'iMX6 SoloLiteLite'
        regs = None
    elif dev_name == 'VIBRID':
        desc = 'VFxxx Controller'
        regs = None
    else:
        desc = None
        regs = None

    return desc, regs


def parse_hablog_mx6(data):
    logNamesSingle    = {0x00010000: "BOOTMODE - Internal Fuse",
                         0x00010001: "BOOTMODE - Serial Bootloader",
                         0x00010002: "BOOTMODE - Internal/Override",
                         0x00010003: "BOOTMODE - Test Mode",
                         0x00020000: "Security Mode - Fab",
                         0x00020033: "Security Mode - Return",
                         0x000200F0: "Security Mode - Open",
                         0x000200CC: "Security Mode - Closed",
                         0x00030000: "DIR_BT_DIS = 0",
                         0x00030001: "DIR_BT_DIS = 1",
                         0x00040000: "BT_FUSE_SEL = 0",
                         0x00040001: "BT_FUSE_SEL = 1",
                         0x00050000: "Primary Image Selected",
                         0x00050001: "Secondary Image Selected",
                         0x00060000: "NAND Boot",
                         0x00060001: "USDHC Boot",
                         0x00060002: "SATA Boot",
                         0x00060003: "I2C Boot",
                         0x00060004: "ECSPI Boot",
                         0x00060005: "NOR Boot",
                         0x00060006: "ONENAND Boot",
                         0x00060007: "QSPI Boot",
                         0x00061003: "Recovery Mode I2C",
                         0x00061004: "Recovery Mode ECSPI",
                         0x00061FFF: "Recovery Mode NONE",
                         0x00062001: "MFG Mode USDHC",
                         0x00070000: "Device INIT Call",
                         0x000700F0: "Device INIT Pass",
                         0x00070033: "Device INIT Fail",
                         0x000800F0: "Device READ Data Pass",
                         0x00080033: "Device READ Data Fail",
                         0x000A00F0: "Plugin Image Pass",
                         0x000A0033: "Plugin Image Fail",
                         0x000C0000: "Serial Downloader Entry",
                         0x000E0000: "ROMCP Patch"}

    logNamesDouble    = {0x00080000: "Device READ Data Call",
                         0x00090000: "HAB Authentication Status Code:",
                         0x000A0000: "Plugin Image Call",
                         0x000B0000: "Program Image Call",
                         0x000D0000: "Serial Downloader Call"}

    logNamesHABstatus = {0xF0: "Success",
                         0x33: "Failure",
                         0x69: "Warning",
                         0x00: "Unknown"}

    logNamesHABreason = {0x22: "Invalid Address",
                         0x30: "Engine Failure",
                         0x0C: "Invalid Assertion",
                         0x28: "Out of Sequence Function Call",
                         0x21: "Invalid Certificate",
                         0x06: "Invalid Command",
                         0x11: "Invalid CSF",
                         0x27: "Invalid DCD",
                         0x0F: "Invalid Index",
                         0x05: "Invalid IVT",
                         0x1D: "Invalid Key",
                         0x1E: "Callback Function Failed",
                         0x18: "Invalid Signature",
                         0x17: "Invalid Data Size",
                         0x2E: "Memory Failure",
                         0x2B: "Poll Count Expired",
                         0x2D: "Exhausted Storage Region",
                         0x12: "Algorithm Unsupported",
                         0x03: "Command Unsupported",
                         0x0a: "Engine Unsupported",
                         0x24: "Configuration Item Unsupported",
                         0x1B: "Key Unsupported",
                         0x14: "Protocol Unsupported",
                         0x09: "Unsuitable State",
                         0x00: "Unknown"}

    retmsg = ''
    logLoop = 0
    while logLoop < 64:
        logValue = struct.unpack_from('I', data, logLoop * 4)[0]

        if logValue == 0x0:
            break
        else:
            if logValue in logNamesSingle:
                retmsg += " %02d. (0x%08X) -> %s\n" % (logLoop, logValue, logNamesSingle[logValue])
                if logValue & 0xffff0000 == 0x00060000:
                  bootType = logValue & 0xff
            elif logValue in logNamesDouble:
                retmsg += " %02d. (0x%08X) -> %s\n" % (logLoop, logValue, logNamesDouble[logValue])
                logLoop += 1
                logData = struct.unpack_from('I', data, logLoop * 4)[0]
                if logValue == 0x00090000:
                    retmsg += " %02d. (0x%08X) -> HAB Status Code: 0x%02X  %s\n" % (logLoop, logData, logData & 0xff,
                                                                                    logNamesHABstatus[logData & 0xff])
                    retmsg += "                     HAB Reason Code: 0x%02X  %s\n" % ((logData >> 8) & 0xff,
                                                                             logNamesHABreason[(logData >> 8) & 0xff])
                else:
                    retmsg += " %02d. (0x%08X) -> Address: 0x%08X\n" % (logLoop, logData, logData)
            else:
                retmsg += " Log Buffer Code not found\n"

            logLoop += 1

    return retmsg


def parse_hablog_mx7(data):
    logNamesAll    = {0x10: "BOOTMODE - Internal Fuse",
                      0x11: "BOOTMODE - Serial Bootloader ",
                      0x12: "BOOTMODE - Internal/Override ",
                      0x13: "BOOTMODE - Test Mode ",
                      0x20: "Security Mode - Fab ",
                      0x21: "Security Mode - Return ",
                      0x22: "Security Mode - Open ",
                      0x23: "Security Mode - Closed ",
                      0x30: "DIR_BT_DIS = 0 ",
                      0x31: "DIR_BT_DIS = 1 ",
                      0x40: "BT_FUSE_SEL = 0 ",
                      0x41: "BT_FUSE_SEL = 1 ",
                      0x50: "Primary Image Selected ",
                      0x51: "Secondary Image Selected ",
                      0x60: "NAND Boot ",
                      0x61: "USDHC Boot ",
                      0x62: "SATA Boot ",
                      0x63: "I2C Boot ",
                      0x64: "ECSPI Boot ",
                      0x65: "NOR Boot ",
                      0x66: "ONENAND Boot ",
                      0x67: "QSPI Boot ",
                      0x70: "Recovery Mode I2C ",
                      0x71: "Recovery Mode ECSPI ",
                      0x72: "Recovery Mode NONE ",
                      0x73: "MFG Mode USDHC ",
                      0xB1: "Plugin Image Pass ",
                      0xBF: "Plugin Image Fail ",
                      0xD0: "Serial Downloader Entry ",
                      0xE0: "ROMCP Patch ",
                      0x80: "Device INIT Call ",
                      0x81: "Device INIT Pass ",
                      0x91: "Device READ Data Pass ",
                      0xA0: "HAB Authentication Status Code:  ",
                      0x90: "Device READ Data Call ",
                      0xB0: "Plugin Image Call ",
                      0xC0: "Program Image Call ",
                      0xD1: "Serial Downloader Call ",
                      0x8F: "Device INIT Fail ",
                      0x9F: "Device READ Data Fail "}

    logNamesError  = {0x8F: "Device INIT Fail ",
                      0x9F: "Device READ Data Fail ",
                      0xBF: "Plugin Image Fail "}

    logNamesTick   = {0x80: "Device INIT Call ",
                      0x81: "Device INIT Pass ",
                      0x8F: "Device INIT Fail ",
                      0x91: "Device READ Data Pass ",
                      0x9F: "Device READ Data Fail ",
                      0xB0: "Plugin Image Call ",
                      0xC0: "Program Image Call "}

    logNamesAddress ={0x90: "Device READ Data Call ",
                      0xB0: "Plugin Image Call ",
                      0xC0: "Program Image Call ",
                      0xD1: "Serial Downloader Call "}

    logNamesHAB    = {0xA0: "HAB Authentication Status Code "}

    logNamesHABstatus = {0xF0: "Success",
                         0x33: "Failure",
                         0x69: "Warning",
                         0x00: "Unknown"}

    logNamesHABreason = {0x22: "Invalid Address",
                         0x30: "Engine Failure",
                         0x0C: "Invalid Assertion",
                         0x28: "Out of Sequence Function Call",
                         0x21: "Invalid Certificate",
                         0x06: "Invalid Command",
                         0x11: "Invalid CSF",
                         0x27: "Invalid DCD",
                         0x0F: "Invalid Index",
                         0x05: "Invalid IVT",
                         0x1D: "Invalid Key",
                         0x1E: "Callback Function Failed",
                         0x18: "Invalid Signature",
                         0x17: "Invalid Data Size",
                         0x2E: "Memory Failure",
                         0x2B: "Poll Count Expired",
                         0x2D: "Exhausted Storage Region",
                         0x12: "Algorithm Unsupported",
                         0x03: "Command Unsupported",
                         0x0a: "Engine Unsupported",
                         0x24: "Configuration Item Unsupported",
                         0x1B: "Key Unsupported",
                         0x14: "Protocol Unsupported",
                         0x09: "Unsuitable State",
                         0x00: "Unknown"}
    retmsg = ''
    logLoop = 0
    while logLoop < 64:
        logValueFull = struct.unpack_from('I', data, logLoop * 4)[0]
        logValue = (logValueFull >> 24) & 0xff

        if logValue == 0x0:
            break
        else:
            if logValue in logNamesAll:
                retmsg += " %02d. (0x%08X) -> %s\n" % (logLoop, logValueFull, logNamesAll[logValue])
            else:
                retmsg += " %02d. Log Buffer Code not found\n"
            if logValue in logNamesAddress :
                logLoop += 1
                logData = struct.unpack_from('I', data, logLoop * 4)[0]
                retmsg += " %02d. (0x%08X) -> Address: 0x%08X\n" % (logLoop, logData, logData)
            if logValue in logNamesHAB:
                logLoop += 1
                logData = struct.unpack_from('I', data, logLoop * 4)[0]
                retmsg += " %02d. (0x%08X) -> HAB Status Code: 0x%02X  %s\n" % (logLoop, logData, logData & 0xff,
                                                                                logNamesHABstatus[logData & 0xff])
                retmsg += "                     HAB Reason Code: 0x%02X  %s\n" % ((logData >> 8) & 0xff,
                                                                         logNamesHABreason[(logData >> 8) & 0xff])
            if logValue in logNamesError:
                retmsg += "                     Error Code: 0x%06X\n" % (logValueFull & 0xffffff)
            if logValue in logNamesTick:
                logLoop += 1
                logData = struct.unpack_from('I', data, logLoop * 4)[0]
                retmsg += " %02d. (0x%08X) -> Tick: 0x%08X\n" % (logLoop, logData, logData)

            logLoop = logLoop + 1

    return retmsg


def parse_hablog(dev_type, data):
  if dev_type == 6:
    return parse_hablog_mx6(data)
  elif dev_type == 7:
    return parse_hablog_mx7(data)
  else:
    return "\n Not Implemented Log Parser \n"


########################################################################################################################
## New argument types
########################################################################################################################

class UInt(click.ParamType):
    """ Custom argument type for UINT """
    name = 'unsigned int'

    def __repr__(self):
        return 'UINT'

    def convert(self, value, param, ctx):
        try:
            val = value if isinstance(value, int) else int(value, 0)
        except:
            self.fail('%s is not a valid value' % value, param, ctx)

        if val > 0xFFFFFFFF:
            self.fail('%s is out of range (0 - 0xFFFFFFFF)' % value, param, ctx)

        return val


# Instances of custom argument types
UINT = UInt()


########################################################################################################################
## CLI
########################################################################################################################

# Application error code
ERROR_CODE = 1

# Application version
VERSION = imx.__version__

# Application description
DESCRIP = (
    "IMX Serial Downloader, ver.: " + VERSION + " Beta\n\n"
    "NOTE: Development version, be carefully with it usage !\n"
)

# Supported Targets
TARGETS = imx.SerialDownloader.HID_DEV.keys()


@click.group(context_settings=dict(help_option_names=['-?', '--help']), help=DESCRIP)
@click.option('-t', '--target', type=click.STRING, default=None, help='Select target MX6SX, MX6UL, ... [optional]')
@click.option('-d', '--debug', type=click.IntRange(0, 2, True), default=0, help="Debug level (0-off, 1-info, 2-debug)")
@click.version_option(VERSION, '-v', '--version')
@click.pass_context
def cli(ctx, target=None, debug=0):

    if debug > 0:
        FORMAT = "[%(asctime)s.%(msecs)03d %(levelname)-5s] %(message)s"
        loglevel = [logging.NOTSET, logging.INFO, logging.DEBUG]
        logging.basicConfig(format=FORMAT, datefmt='%M:%S', level=loglevel[debug])

    ctx.obj['DEBUG']  = debug
    ctx.obj['DEVICE'] = None

    # Scan for connected target
    devs = imx.SerialDownloader.scan_usb(target)
    if devs:
        index = 0
        if len(devs) > 1:
            i = 0
            click.echo('')
            for dev in devs:
                click.secho(" %d) %s" % (i, dev.getInfo()))
                i += 1
            click.echo('\n Select: ', nl=False)
            c = input()
            click.echo()
            index = int(c, 10)

        ctx.obj['DEVICE'] = devs[index]


# IMX SD: Read device info
@cli.command(help = "Read detailed information's about HAB and Chip from connected IMX device")
@click.pass_context
def info(ctx):
    ''' Read device info '''

    error = False

    def read_memory_32(addr):
        val = struct.unpack_from('I', flasher.read(addr, 4))
        return val[0]

    def read_rom_release(rom_info, pid):
        pidaddr = rom_info['PIDADDR']
        release = rom_info['RELEASE']
        for i in range(len(pidaddr)):
            rpid = read_memory_32(pidaddr[i]) & 0xFFFF
            if rpid == pid:
                return release[i]
        return None

    if ctx.obj['DEVICE'] is None:
        click.echo("\n - No IMX board detected !")
        sys.exit(ERROR_CODE)

    # Create Flasher instance
    flasher = imx.SerialDownloader()

    try:
        click.secho("\n DEVICE: %s\n" % ctx.obj['DEVICE'].getInfo())
        # Connect IMX Device
        flasher.open_usb(ctx.obj['DEVICE'])
        # Get Connected Device Name
        dev_name = flasher.get_target_name()
        if dev_name is None:
            raise Exception('Not Connected or Unsupported Device')
        # Get Connected Device PID Value
        dev_pid  = ctx.obj['DEVICE'].pid
        # Get Device and ROM Specific Data
        rom_info = get_rom_info(dev_name)
        # Get ROM Release Number
        rom_release = read_rom_release(rom_info, dev_pid)
        if rom_release is None:
            raise Exception('Unknown Device Variant')
        # Read ROM Version
        rom_version = read_memory_32(rom_info['VERADDR'])
        # Get Device description and addresses to specific regs
        desc, regs = get_dev_info(dev_name, rom_version)
        # Read values of specific regs
        digprog_val = read_memory_32(regs[0])
        sbmr1_val   = read_memory_32(regs[1])
        sbmr2_val   = read_memory_32(regs[2])
        persist_val = read_memory_32(regs[3])
        wdog_val    = read_memory_32(regs[4])
        # Read HAB Log Data
        log_data = flasher.read(regs[6], 64 * 4)
    except Exception as e:
        error = True
        if ctx.obj['DEBUG']:
            error_msg = '\n' + traceback.format_exc()
        else:
            error_msg = ' - ERROR: %s' % str(e)
    else:
        bmodList = {
            0: "Boot from Fuses",
            1: "Serial Downloader",
            2: "Boot from GPIO/Fuses",
            3: "Reserved"
        }

        bmodName = bmodList[(sbmr2_val >> 24 ) & 0x3]

        if rom_info['DEVTYPE'] == 7:
            wdogBit = wdog_val & 0x4
            mxRevMajor = (digprog_val >> 4 & 0xf)
            mxRevMinor = digprog_val & 0xf
        else:
            wdogBit = wdog_val & 0x00200000
            mxRevMajor = (digprog_val >> 8 & 0xff) + 1
            mxRevMinor = digprog_val & 0xff

        if ctx.obj['DEBUG']: click.echo()

        click.echo(" ---------------------------------------------------------")
        click.echo(" Connected Device Info")
        click.echo(" ---------------------------------------------------------")
        click.echo()
        click.secho(" Device:        %s" % (desc))
        click.secho(" Silicon Rev:   %d.%d" % (mxRevMajor, mxRevMinor))
        click.echo()
        click.secho(" iROM Release:  %s" % rom_release)
        click.secho(" iROM Version:  0x%02x" % (rom_version & 0xff))
        click.echo()
        click.secho(" WDOG State:    %s" % ('Enabled' if wdogBit > 0 else 'Disabled'))
        click.echo()
        click.secho(" SBMR1: 0x%08x" % sbmr1_val)
        click.secho("   BOOT_CFG_1  = 0x%02x" % (sbmr1_val & 0xff))
        click.secho("   BOOT_CFG_2  = 0x%02x" % ((sbmr1_val >> 8) & 0xff))
        click.secho("   BOOT_CFG_3  = 0x%02x" % ((sbmr1_val >> 16) & 0xff))
        click.secho("   BOOT_CFG_4  = 0x%02x" % ((sbmr1_val >> 24) & 0xff))
        click.echo()
        click.secho(" SBMR2: 0x%08x" % sbmr2_val)
        click.secho("   BMOD        = %1d%1d\t%s" % (((sbmr2_val >> 25) & 0x1),
                                                     ((sbmr2_val >> 24) & 0x1), bmodName))
        click.secho("   BT_FUSE_SEL = %1d" % ((sbmr2_val >> 4) & 0x1))
        click.secho("   DIR_BT_DIS  = %1d" % ((sbmr2_val >> 3) & 0x1))
        click.secho("   SEC_CONFIG  = %1d%1d" % (((sbmr2_val >> 1) & 0x1), sbmr2_val & 0x1))
        click.echo()
        click.secho(" PersistReg Val: 0x%08x" % persist_val)
        click.secho(" ANALOG DIGPROG: 0x%08x" % digprog_val)
        click.echo()
        click.echo(" HAB Log Info --------------------------------------------\n")
        click.echo(parse_hablog(rom_info['DEVTYPE'], log_data))
        click.echo(" ---------------------------------------------------------")

    # Disconnect IMX Device
    flasher.close()

    if error:
        click.echo(error_msg)
        sys.exit(ERROR_CODE)


# IMX SD: Read Memory/Regs command
@cli.command(help = "Read raw data from specified address in connected IMX device. "
                    "The address value must be aligned to selected access size !")
@click.argument('address', nargs=1, type=UINT)
@click.argument('length', nargs=1, type=UINT)
@click.option('-s', '--size', type=click.Choice(['8', '16', '32']), default='32', show_default=True, help="Access Size")
@click.option('-c/', '--compress/', is_flag=True, default=False, help="Compress dump output")
@click.option('-f', '--file', type=click.Path(readable=False), help="Output file name")
@click.pass_context
def read(ctx, address, length, size, compress, file):
    ''' Read data from IMX regs or memory '''

    error = False

    if ctx.obj['DEVICE'] is None:
        click.echo("\n - No IMX board detected !")
        sys.exit(ERROR_CODE)

    # Create Flasher instance
    flasher = imx.SerialDownloader()

    try:
        click.secho("\n DEVICE: %s\n" % ctx.obj['DEVICE'].getInfo())
        # Connect IMX Device
        flasher.open_usb(ctx.obj['DEVICE'])
        # Read data from IMX Device
        data = flasher.read(address, length, int(size))
    except imx.SD_GenericError as e:
        error = True
        if ctx.obj['DEBUG']:
            error_msg = '\n' + traceback.format_exc()
        else:
            error_msg = ' - ERROR: %s' % str(e)

    # Disconnect IMX Device
    flasher.close()

    if not error:
        if file is None:
            if ctx.obj['DEBUG']: click.echo()
            click.echo(hexdump(data, address, compress))
        else:
            with open(file, "wb") as f:
                f.write(data)
                f.close()

            if not error:
                if ctx.obj['DEBUG']: click.echo()
                click.secho(" - Successfully saved into: %s." % file)

    if error:
        click.echo(error_msg)
        sys.exit(ERROR_CODE)


# IMX SD: Read Register command
@cli.command(help = "Read value of register or memory at specified address from connected IMX device. "
                    "The address value must be aligned to selected access size !")
@click.argument('address', nargs=1, type=UINT)
@click.option('-c', '--count', type=UINT, default=0x1, show_default=True, help="Count of Regs")
@click.option('-s', '--size', type=click.Choice(['8', '16', '32']), default='32', show_default=True, help='Access Size')
@click.option('-f', '--format', type=click.Choice(['b', 'x', 'd']), default='x', show_default=True, help='Value Format')
@click.pass_context
def rreg(ctx, address, count, size, format):
    ''' Read value from IMX register '''

    error = False

    if ctx.obj['DEVICE'] is None:
        click.echo("\n - No IMX board detected !")
        sys.exit(ERROR_CODE)

    reg_size = int(size) // 8

    # Create Flasher instance
    flasher = imx.SerialDownloader()

    try:
        click.secho("\n DEVICE: %s\n" % ctx.obj['DEVICE'].getInfo())
        # Connect IMX Device
        flasher.open_usb(ctx.obj['DEVICE'])
        # Read data from IMX Device
        data = flasher.read(address, int(count * reg_size), int(size))
    except Exception as e:
        error = True
        if ctx.obj['DEBUG']:
            error_msg = '\n' + traceback.format_exc()
        else:
            error_msg = ' - ERROR: %s' % str(e)

    # Disconnect IMX Device
    flasher.close()

    if format == 'b':
        val_format = '0b{2:0' + str(reg_size*8) + 'b}'
    elif format == 'x':
        val_format = '0x{2:0' + str(reg_size*2) + 'X}'
    else:
        val_format = '{2:d}'

    if not error:
        if ctx.obj['DEBUG'] > 0:
            click.echo()
        i = 0
        while i < (count * reg_size):
            reg_addr = address + i
            reg_val  = data[i]; i += 1
            if reg_size > 1:
                reg_val |= data[i] << 8; i += 1
            if reg_size > 2:
                reg_val |= data[i] << 16; i += 1
                reg_val |= data[i] << 24; i += 1
            click.echo((' REG{0:s}[0x{1:08X}] = ' + val_format).format(size, reg_addr, reg_val))
    else:
        click.echo(error_msg)
        sys.exit(ERROR_CODE)


# IMX SD: Write Register command
@cli.command(help = "Write value into register or memory at specified address in connected IMX device. "
                    "The address value must be aligned to selected access size !")
@click.argument('address', nargs=1, type=UINT)
@click.argument('value', nargs=1, type=UINT)
@click.option('-s', '--size', type=click.Choice(['8', '16', '32']), default='32', show_default=True, help='Access Size')
@click.option('-b', '--bytes', type=click.IntRange(1, 4, True), default=4, show_default=True, help='Count of Bytes')
@click.pass_context
def wreg(ctx, address, value, size, bytes):
    ''' Write value into IMX register '''

    error = False

    if ctx.obj['DEVICE'] is None:
        click.echo("\n - No IMX board detected !")
        sys.exit(ERROR_CODE)

    # Create Flasher instance
    flasher = imx.SerialDownloader()

    try:
        click.secho("\n DEVICE: %s\n" % ctx.obj['DEVICE'].getInfo())
        # Connect IMX Device
        flasher.open_usb(ctx.obj['DEVICE'])
        # Write value into register from IMX Device
        flasher.write(address, value, bytes, int(size))
    except Exception as e:
        error = True
        if ctx.obj['DEBUG']:
          error_msg = '\n' + traceback.format_exc()
        else:
          error_msg = ' - ERROR: %s' % str(e)

    # Disconnect IMX Device
    flasher.close()

    if not error:
        if ctx.obj['DEBUG']: click.echo()
        click.secho(" - Done")
    else:
        click.echo(error_msg)
        sys.exit(ERROR_CODE)


# IMX SD: Write File command
@cli.command(help = "Write U-Boot image file into connected device and RUN it")
@click.argument('file', nargs=1, type=click.Path(exists=True))
@click.option('-a', '--addr', type=UINT, help='Start Address (required for *.bin)')
@click.option('-o', '--offset', type=UINT, default=0, show_default=True, help='Offset of input data')
@click.option('-m', '--ocram', type=UINT, default=0, help='IMX OCRAM Address, required for DDR init')
@click.option('-i/','--init/', is_flag=True, default=False, help='Init DDR from *.imx image')
@click.option('-r/','--run/', is_flag=True, default=False, help='Run loaded *.imx image')
@click.option('-s/','--skipdcd/', is_flag=True, default=False, help='Skip DCD Header from *.imx image')
@click.pass_context
def wimg(ctx, addr, offset, ocram, init, run, skipdcd, file):
    ''' Write image file (uboot.imx, uImage, ...) '''

    error = False

    if ctx.obj['DEVICE'] is None:
        click.echo("\n - No IMX board detected !")
        sys.exit(ERROR_CODE)

    # Create Flasher instance
    flasher = imx.SerialDownloader()

    try:
        click.secho("\n DEVICE: %s\n" % ctx.obj['DEVICE'].getInfo())
        # Connect IMX Device
        flasher.open_usb(ctx.obj['DEVICE'])
        # Load image
        if file.lower().endswith('.imx'):
            img = imx.BootImage()
            data = bytearray(os.path.getsize(file))
            with open(file, 'rb') as f:
                f.readinto(data)
                img.parse(data)

            if not addr:
                addr = img.address + img.offset

            if init:
                if ocram == 0:
                    raise Exception('Argument: -m/--ocram must be specified !')

                click.echo(' - Init DDR')
                dcd = img.dcd.export()
                flasher.write_dcd(ocram, dcd)
        else:
            if addr is None:
                raise Exception('Argument: -a/--addr must be specified !')

            with open(file, "rb") as f:
                if offset > 0:
                    f.seek(offset)
                data = f.read()
                f.close()

        click.secho(" - Writing %s, please wait !" % file)
        if ctx.obj['DEBUG']: click.echo()
        # Write data from image into device
        flasher.write_file(addr, data)
        # Skip DCD header if set
        if file.lower().endswith('.imx') and skipdcd:
            click.echo(' - Skip DCD content')
            flasher.skip_dcd()
            if ctx.obj['DEBUG']: click.echo()
        # Run loaded uboot.imx image
        if file.lower().endswith('.imx') and run:
            click.secho(' - Jump to ADDR: 0x%08X and RUN' % addr)
            flasher.jump_and_run(addr)

    except Exception as e:
        error = True
        if ctx.obj['DEBUG']:
            error_msg = '\n' + traceback.format_exc()
        else:
            error_msg = ' - ERROR: %s' % str(e)

    # Disconnect IMX Device
    flasher.close()

    if not error:
        if ctx.obj['DEBUG']: click.echo()
        click.secho(" - Done")
    else:
        click.echo(error_msg)
        sys.exit(ERROR_CODE)


# IMX SD: Write DCD command
@cli.command(short_help="Write DCD file")
@click.argument('address', nargs=1, type=UINT)
@click.argument('file', nargs=1, type=click.Path(exists=True))
@click.option('-o', '--offset', type=UINT, default=0, show_default=True, help='Offset of input data')
@click.pass_context
def wdcd(ctx, address, file, offset):
    ''' Write DCD file '''

    error = False

    if ctx.obj['DEVICE'] is None:
        click.echo("\n - No IMX board detected !")
        sys.exit(ERROR_CODE)

    if file.lower().endswith('.imx'):
        img = imx.BootImage()
        raw_data = bytearray(os.path.getsize(file))
        with open(file, 'rb') as f:
            f.readinto(raw_data)
            img.parse(raw_data)

        data = img.dcd.export()

    else:
        with open(file, "rb") as f:
            if offset > 0:
                f.seek(offset)
            data = f.read()
            f.close()

    # Create Flasher instance
    flasher = imx.SerialDownloader()

    try:
        click.secho("\n DEVICE: %s\n" % ctx.obj['DEVICE'].getInfo())
        # Connect IMX Device
        flasher.open_usb(ctx.obj['DEVICE'])
        click.secho(' - Writing DCD from %s, please wait !' % file)
        # Write value into register from IMX Device
        flasher.write_dcd(address, data)
    except Exception as e:
        error = True
        if ctx.obj['DEBUG']:
            error_msg = '\n' + traceback.format_exc()
        else:
            error_msg = ' - ERROR: %s' % str(e)

    # Disconnect IMX Device
    flasher.close()

    if not error:
        if ctx.obj['DEBUG']: click.echo()
        click.secho(" - Done")
    else:
        click.echo(error_msg)
        sys.exit(ERROR_CODE)


# IMX SD: Write CSF command
@cli.command(short_help="Write CSF file")
@click.argument('address', nargs=1, type=UINT)
@click.argument('file', nargs=1, type=click.Path(exists=True))
@click.option('-o', '--offset', type=UINT, default=0, show_default=True, help='Offset of input data')
@click.pass_context
def wcsf(ctx, address, file, offset):
    error = False

    if ctx.obj['DEVICE'] is None:
        click.echo("\n - No IMX board detected !")
        sys.exit(ERROR_CODE)

    if file.lower().endswith('.imx'):
        click.echo('\n - ERROR: The parser of CFS blob from *.imx is not implemented yet')
        sys.exit(ERROR_CODE)

    else:
        with open(file, "rb") as f:
            if offset > 0:
                f.seek(offset)
            data = f.read()
            f.close()

    # Create Flasher instance
    flasher = imx.SerialDownloader()

    try:
        click.secho("\n DEVICE: %s\n" % ctx.obj['DEVICE'].getInfo())
        # Connect IMX Device
        flasher.open_usb(ctx.obj['DEVICE'])
        click.secho(' - Writing %s, please wait !' % file)
        # Write value into register from IMX Device
        flasher.write_csf(address, data)
    except Exception as e:
        error = True
        if ctx.obj['DEBUG']:
            error_msg = '\n' + traceback.format_exc()
        else:
            error_msg = ' - ERROR: %s' % str(e)

    # Disconnect IMX Device
    flasher.close()

    if not error:
        if ctx.obj['DEBUG']: click.echo()
        click.secho(' - Done')
    else:
        click.echo(error_msg)
        sys.exit(ERROR_CODE)


# IMX SD: RUN command
@cli.command(short_help="Jump to specified address and RUN")
@click.argument('address', nargs=1, type=UINT)
@click.pass_context
def jump(ctx, address):
    error = False

    if ctx.obj['DEVICE'] is None:
        click.echo("\n - No IMX board detected !")
        sys.exit(ERROR_CODE)

    # Create Flasher instance
    flasher = imx.SerialDownloader()

    try:
        click.secho("\n DEVICE: %s\n" % ctx.obj['DEVICE'].getInfo())
        # Connect IMX Device
        flasher.open_usb(ctx.obj['DEVICE'])
        # Write value into register from IMX Device
        flasher.jump_and_run(address)
    except Exception as e:
        error = True
        if ctx.obj['DEBUG']:
            error_msg = '\n' + traceback.format_exc()
        else:
            error_msg = ' - ERROR: %s' % str(e)

    # Disconnect IMX Device
    flasher.close()

    if not error:
        if ctx.obj['DEBUG']: click.echo()
        click.secho(" - Jump to ADDR: 0x%08X and RUN" % address)
    else:
        click.echo(error_msg)
        sys.exit(ERROR_CODE)


# IMX SD: Read Status command
@cli.command(short_help="Read status value")
@click.pass_context
def stat(ctx):
    error = False

    if ctx.obj['DEVICE'] is None:
        click.echo('\n - No IMX board detected !')
        sys.exit(ERROR_CODE)

    # Create Flasher instance
    flasher = imx.SerialDownloader()

    try:
        click.secho("\n DEVICE: %s\n" % ctx.obj['DEVICE'].getInfo())
        # Connect IMX Device
        flasher.open_usb(ctx.obj['DEVICE'])
        # Read Status from IMX Device
        status = flasher.read_status()
    except Exception as e:
        error = True
        if ctx.obj['DEBUG']:
            error_msg = '\n' + traceback.format_exc()
        else:
            error_msg = ' - ERROR: %s' % str(e)

    # Disconnect IMX Device
    flasher.close()

    if not error:
        if ctx.obj['DEBUG']: click.echo()
        click.secho(" - Status: 0x%08X" % status)
    else:
        click.echo(error_msg)
        sys.exit(ERROR_CODE)


def main():
    cli(obj={})


if __name__ == '__main__':
    main()