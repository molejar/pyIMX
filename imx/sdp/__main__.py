#!/usr/bin/env python

# Copyright (c) 2017-2018 Martin Olejar
#
# SPDX-License-Identifier: BSD-3-Clause
# The BSD-3-Clause license for this file can be found in the LICENSE file included with this distribution
# or at https://spdx.org/licenses/BSD-3-Clause.html#licenseText

import os
import sys
import imx
import click
import struct
import logging
import traceback


########################################################################################################################
# Misc
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
# HAB Parser
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
            'DEVTYPE':  imx.hab.EnumDevType.IMX6
        },
        'MX6SDL':   {
            'RELEASE': ('00.00.05', '01.01.02', '01.02.02', '01.03.00'),
            'PIDADDR': (0x00010E28, 0x0001108C, 0x000111AC, 0x000111CC),
            'VERADDR':  0x00000048,
            'DEVTYPE':  imx.hab.EnumDevType.IMX6
        },
        'MX6SL':   {
            'RELEASE': ('01.00.01', '01.02.00', '01.03.00'),
            'PIDADDR': (0x0000E0B0, 0x0000E210, 0x0000E2C2),
            'VERADDR':  0x00000048,
            'DEVTYPE':  imx.hab.EnumDevType.IMX6
        },
        'MX6SX':  {
            'RELEASE': ('01.00.02', '01.01.01'),
            'PIDADDR': (0x00012398, 0x00013124),
            'VERADDR':  0x00000080,
            'DEVTYPE':  imx.hab.EnumDevType.IMX6
        },
        'MX6UL':  {
            'RELEASE': ('01.00.00', '01.01.00'),
            'PIDADDR': (0x000129C4, 0x00012A04),
            'VERADDR':  0x00000080,
            'DEVTYPE':  imx.hab.EnumDevType.IMX6
        },
        'MX6ULL': {
            'RELEASE': ('01.00.01',),
            'PIDADDR': (0x00010E84,),
            'VERADDR':  0x00000080,
            'DEVTYPE':  imx.hab.EnumDevType.IMX6
        },
        'MX7SD':   {
            'RELEASE': ('01.00.05', '01.01.01'),
            'PIDADDR': (0x000130A0, 0x000130A0),
            'VERADDR':  0x00000080,
            'DEVTYPE':  imx.hab.EnumDevType.IMX7
        },
        'MX6SLL': {
            'RELEASE': ('01.00.00',),
            'PIDADDR': (0x0000F884,),
            'VERADDR':  0x00000080,
            'DEVTYPE':  imx.hab.EnumDevType.IMX6
        },
        'VIBRID': {
            'RELEASE': ('01.00.10',),
            'PIDADDR': (0x0000F884,),
            'VERADDR':  0x00000048,
            'DEVTYPE':  imx.hab.EnumDevType.IMX6
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


########################################################################################################################
# New argument types
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
# Command Line Interface
########################################################################################################################

# Application error code
ERROR_CODE = 1

# Application version
VERSION = imx.__version__

# Application description
DESCRIP = (
    "i.MX Serial Downloader, ver.: " + VERSION + " Beta\n\n"
    "NOTE: Development version, be carefully with it usage !\n"
)


# helper method
def scan_usb(device_name):
    # Scan for connected devices

    fsls = imx.sdp.scan_usb(device_name)

    if fsls:
        index = 0

        if len(fsls) > 1:
            i = 0
            click.echo('')
            for fsl in fsls:
                click.secho(" %d) %s" % (i, fsl.usbd.info))
                i += 1
            click.echo('\n Select: ', nl=False)
            c = input()
            click.echo()
            index = int(c, 10)

        click.secho("\n DEVICE: %s\n" % fsls[index].usbd.info)
        return fsls[index]

    else:
        click.echo("\n - No i.MX board detected !")
        sys.exit(ERROR_CODE)


@click.group(context_settings=dict(help_option_names=['-?', '--help']), help=DESCRIP)
@click.option('-t', '--target', type=click.STRING, default=None, help='Select target MX6SX, MX6UL, ... [optional]')
@click.option('-d', '--debug', type=click.IntRange(0, 2, True), default=0, help="Debug level (0-off, 1-info, 2-debug)")
@click.version_option(VERSION, '-v', '--version')
@click.pass_context
def cli(ctx, target, debug):

    if debug > 0:
        FORMAT = "[%(asctime)s.%(msecs)03d %(levelname)-5s] %(message)s"
        loglevel = [logging.NOTSET, logging.INFO, logging.DEBUG]
        logging.basicConfig(format=FORMAT, datefmt='%M:%S', level=loglevel[debug])

    ctx.obj['DEBUG'] = debug
    ctx.obj['TARGET'] = target


@cli.command(short_help="Read i.MX device info")
@click.pass_context
def info(ctx):
    ''' Read detailed information's about HAB and Chip from connected IMX device'''

    error = False

    def read_memory_32(addr):
        val = struct.unpack_from('I', flasher.read(addr, 4, 8))
        return val[0]

    def read_rom_release(rom_info, pid):
        pidaddr = rom_info['PIDADDR']
        release = rom_info['RELEASE']
        for i in range(len(pidaddr)):
            rpid = read_memory_32(pidaddr[i]) & 0xFFFF
            if rpid == pid:
                return release[i]
        return None

    # Create Flasher instance
    flasher = scan_usb(ctx.obj['TARGET'])

    try:
        # Connect IMX Device
        flasher.open()
        # Get Connected Device Name
        dev_name = flasher.device_name
        if dev_name is None:
            raise Exception('Not Connected or Unsupported Device')
        # Get Connected Device PID Value
        dev_pid  = flasher.usbd.pid
        # Get Device and ROM Specific Data
        rom_info = get_rom_info(dev_name)
        if rom_info is None:
            raise Exception('Unknown Device Info')
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
        click.echo(imx.hab.parse_hab_log(rom_info['DEVTYPE'], log_data))
        click.echo(" ---------------------------------------------------------")

    # Disconnect IMX Device
    flasher.close()

    if error:
        click.echo(error_msg)
        sys.exit(ERROR_CODE)


@cli.command(short_help="Read raw data from i.MX memory")
@click.argument('address', nargs=1, type=UINT)
@click.argument('length', nargs=1, type=UINT)
@click.option('-s', '--size', type=click.Choice(['8', '16', '32']), default='32', show_default=True, help="Access Size")
@click.option('-c/', '--compress/', is_flag=True, default=False, help="Compress dump output")
@click.option('-f', '--file', type=click.Path(readable=False), help="Output file name")
@click.pass_context
def read(ctx, address, length, size, compress, file):
    ''' Read raw data from specified address in connected IMX device.
        The address value must be aligned to selected access size !
    '''

    error = False
    # Create Flasher instance
    flasher = scan_usb(ctx.obj['TARGET'])

    try:
        # Connect IMX Device
        flasher.open()
        # Read data from IMX Device
        data = flasher.read(address, length, int(size))
    except imx.sdp.SdpGenericError as e:
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

            if ctx.obj['DEBUG']: click.echo()
            click.secho(" - Successfully saved into: %s." % file)
    else:
        # Print Error Message and exit
        click.echo(error_msg)
        sys.exit(ERROR_CODE)


@cli.command(short_help="Read value from i.MX register")
@click.argument('address', nargs=1, type=UINT)
@click.option('-c', '--count', type=UINT, default=0x1, show_default=True, help="Count of Regs")
@click.option('-s', '--size', type=click.Choice(['8', '16', '32']), default='32', show_default=True, help='Access Size')
@click.option('-f', '--format', type=click.Choice(['b', 'x', 'd']), default='x', show_default=True, help='Value Format')
@click.pass_context
def rreg(ctx, address, count, size, format):
    ''' Read value of register or memory at specified address from connected i.MX device.
        The address value must be aligned to selected access size !
    '''

    error = False
    reg_size = int(size) // 8

    # Create Flasher instance
    flasher = scan_usb(ctx.obj['TARGET'])

    try:
        # Connect IMX Device
        flasher.open()
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
        i = 0
        if ctx.obj['DEBUG']: click.echo()
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


@cli.command(short_help="Write value into i.MX register")
@click.argument('address', nargs=1, type=UINT)
@click.argument('value', nargs=1, type=UINT)
@click.option('-s', '--size', type=click.Choice(['8', '16', '32']), default='32', show_default=True, help='Access Size')
@click.option('-b', '--bytes', type=click.IntRange(1, 4, True), default=4, show_default=True, help='Count of Bytes')
@click.pass_context
def wreg(ctx, address, value, size, bytes):
    ''' Write value into register or memory at specified address in connected IMX device.
        The address value must be aligned to selected access size !
    '''

    error = False

    # Create Flasher instance
    flasher = scan_usb(ctx.obj['TARGET'])

    try:
        # Connect IMX Device
        flasher.open()
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


@cli.command(short_help="Write image into i.MX device and RUN it")
@click.argument('file', nargs=1, type=click.Path(exists=True))
@click.option('-a', '--addr', type=UINT, default=None, help='Start Address (required for *.bin)')
@click.option('-o', '--offset', type=UINT, default=0, show_default=True, help='Offset of input data')
@click.option('-m', '--ocram', type=UINT, default=0x910000, help='OCRAM Address for DDR init [default: 0x910000]')
@click.option('-i/','--init/', is_flag=True, default=False, help='Init DDR from *.imx img')
@click.option('-r/','--run/', is_flag=True, default=False, help='Run loaded *.imx img')
@click.option('-s/','--skipdcd/', is_flag=True, default=False, help='Skip DCD Header from *.imx img')
@click.pass_context
def wimg(ctx, addr, offset, ocram, init, run, skipdcd, file):
    ''' Write image file (uboot.imx, uImage, ...) into i.MX device and RUN it '''

    error = False

    # Create Flasher instance
    flasher = scan_usb(ctx.obj['TARGET'])

    try:
        # Connect IMX Device
        flasher.open()
        # Load img
        if file.lower().endswith('.imx'):
            data = bytearray(os.path.getsize(file))
            with open(file, 'rb') as f:
                f.readinto(data)

            img = imx.img.parse(data)

            if addr is None:
                addr = img.address + img.offset

            if init:
                if ocram == 0:
                    raise Exception('Argument: -m/--ocram must be specified !')

                click.echo(' - Init DDR')
                dcd = img.dcd.export()
                flasher.write_dcd(ocram, dcd)

                if flasher.device_name in ('MX6UL', 'MX6ULL', 'MX6SLL', 'MX7SD', 'MX7ULP'):
                    skipdcd = True
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
        # Write data from img into device
        flasher.write_file(addr, data)
        # Skip DCD header if set
        if file.lower().endswith('.imx') and skipdcd:
            click.echo(' - Skip DCD content')
            flasher.skip_dcd()
            if ctx.obj['DEBUG']: click.echo()
        # Run loaded uboot.imx img
        if file.lower().endswith('.imx') and run:
            if isinstance(flasher, imx.sdp.SdpMXRT):
                addr = img.address
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


@cli.command(short_help="Write DCD blob into i.MX device")
@click.argument('address', nargs=1, type=UINT)
@click.argument('file', nargs=1, type=click.Path(exists=True))
@click.option('-o', '--offset', type=UINT, default=0, show_default=True, help='Offset of input data')
@click.pass_context
def wdcd(ctx, address, file, offset):
    ''' Write Device Configuration Data into i.MX device '''

    error = False

    if file.lower().endswith('.imx'):
        raw_data = bytearray(os.path.getsize(file))
        with open(file, 'rb') as f:
            f.readinto(raw_data)

        img = imx.img.parse(raw_data)
        data = img.dcd.export()

    else:
        with open(file, "rb") as f:
            if offset > 0:
                f.seek(offset)
            data = f.read()
            f.close()

    # Create Flasher instance
    flasher = scan_usb(ctx.obj['TARGET'])

    try:
        # Connect i.MX Device
        flasher.open()
        click.secho(' - Writing DCD from %s, please wait !' % file)
        # Write value into register from IMX Device
        flasher.write_dcd(address, data)
    except Exception as e:
        error = True
        if ctx.obj['DEBUG']:
            error_msg = '\n' + traceback.format_exc()
        else:
            error_msg = ' - ERROR: %s' % str(e)

    # Disconnect i.MX Device
    flasher.close()

    if not error:
        if ctx.obj['DEBUG']: click.echo()
        click.secho(" - Done")
    else:
        click.echo(error_msg)
        sys.exit(ERROR_CODE)


@cli.command(short_help="Write CSF file into i.MX device")
@click.argument('address', nargs=1, type=UINT)
@click.argument('file', nargs=1, type=click.Path(exists=True))
@click.option('-o', '--offset', type=UINT, default=0, show_default=True, help='Offset of input data')
@click.pass_context
def wcsf(ctx, address, file, offset):
    ''' Write Code Signing File file into i.MX device '''

    error = False

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
    flasher = scan_usb(ctx.obj['TARGET'])

    try:
        # Connect IMX Device
        flasher.open()
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


@cli.command(short_help="Jump to specified address and RUN")
@click.argument('address', nargs=1, type=UINT)
@click.pass_context
def jump(ctx, address):
    ''' Jump to specified address and RUN i.MX device '''

    error = False

    # Create Flasher instance
    flasher = scan_usb(ctx.obj['TARGET'])

    try:
        # Connect IMX Device
        flasher.open()
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


@cli.command(short_help="Read status of i.MX device")
@click.pass_context
def stat(ctx):
    ''' Read status of i.MX device '''

    error = False

    # Create Flasher instance
    flasher = scan_usb(ctx.obj['TARGET'])

    try:
        # Connect IMX Device
        flasher.open()
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
        click.secho(" - Return Value: 0x%08X" % status)
        click.secho(" - Description : %s" % imx.hab.status_info(status))
    else:
        click.echo(error_msg)
        sys.exit(ERROR_CODE)


def main():
    cli(obj={})


if __name__ == '__main__':
    main()
