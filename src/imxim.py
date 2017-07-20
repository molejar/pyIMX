#!/usr/bin/env python3

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
import imx


########################################################################################################################
## Local methods
########################################################################################################################

def export_dcd(dcd_obj):
    assert isinstance(dcd_obj, imx.SegDCD)

    engines = {
        int(imx.EnumEngine.HAB_ENG_ANY):    'ANY',
        int(imx.EnumEngine.HAB_ENG_SCC):    'SCC',
        int(imx.EnumEngine.HAB_ENG_RTIC):   'RTIC',
        int(imx.EnumEngine.HAB_ENG_SAHARA): 'SAHARA',
        int(imx.EnumEngine.HAB_ENG_CSU):    'CSU',
        int(imx.EnumEngine.HAB_ENG_SRTC):   'SRTC',
        int(imx.EnumEngine.HAB_ENG_DCP):    'DCP',
        int(imx.EnumEngine.HAB_ENG_CAAM):   'CAAM',
        int(imx.EnumEngine.HAB_ENG_SNVS):   'SNVS',
        int(imx.EnumEngine.HAB_ENG_OCOTP):  'OCOTP',
        int(imx.EnumEngine.HAB_ENG_DTCP):   'DTCP',
        int(imx.EnumEngine.HAB_ENG_ROM):    'ROM',
        int(imx.EnumEngine.HAB_ENG_HDCP):   'HDCP',
        int(imx.EnumEngine.HAB_ENG_SW):     'SW'
    }
    write_ops = ('WriteValue', 'WriteValue', 'ClearBitMask', 'SetBitMask')
    check_ops = ('CheckAllClear', 'CheckAllSet', 'CheckAnyClear', 'CheckAnySet')
    text_file = "# IMX DCD Content\n\n"

    for cmd in dcd_obj:
        if type(cmd)  is imx.CmdWriteData:
            for (address, value) in cmd:
                text_file += "{0:s} {1:d} 0x{2:08X} 0x{3:08X}\n".format(write_ops[cmd.ops], cmd.bytes, address, value)
            text_file += '\n'
        elif type(cmd)  is imx.CmdCheckData:
            text_file += "{0:s} {1:d} 0x{2:08X} 0x{3:08X}".format(check_ops[cmd.ops], cmd.bytes, cmd.address, cmd.mask)
            if cmd.count:
                text_file += "{0:d}\n".format(cmd.count)
            else:
                text_file += "\n"
            text_file += '\n'
        elif type(cmd) is imx.CmdUnlock:
            text_file += "Unlock {0:s}".format(engines[cmd.engine])
            for value in cmd:
                text_file += " 0x{0:08X}".format(value)
            text_file += '\n\n'
        else:
            text_file += "Nop\n\n"

    return text_file


def parse_dcd(text_file):

    cmds = {
        'WriteValue':    ('write', int(imx.EnumWriteOps.WRITE_VALUE)),
        'ClearBitMask':  ('write', int(imx.EnumWriteOps.CLEAR_BITMASK)),
        'SetBitMask':    ('write', int(imx.EnumWriteOps.SET_BITMASK)),
        'CheckAllClear': ('check', int(imx.EnumCheckOps.ALL_CLEAR)),
        'CheckAllSet':   ('check', int(imx.EnumCheckOps.ALL_SET)),
        'CheckAnyClear': ('check', int(imx.EnumCheckOps.ANY_CLEAR)),
        'CheckAnySet':   ('check', int(imx.EnumCheckOps.ANY_SET)),
        'Unlock':        None,
        'Nop':           None
    }

    engines = {
        'ANY':    int(imx.EnumEngine.HAB_ENG_ANY),
        'SCC':    int(imx.EnumEngine.HAB_ENG_SCC),
        'RTIC':   int(imx.EnumEngine.HAB_ENG_RTIC),
        'SAHARA': int(imx.EnumEngine.HAB_ENG_SAHARA),
        'CSU':    int(imx.EnumEngine.HAB_ENG_CSU),
        'SRTC':   int(imx.EnumEngine.HAB_ENG_SRTC),
        'DCP':    int(imx.EnumEngine.HAB_ENG_DCP),
        'CAAM':   int(imx.EnumEngine.HAB_ENG_CAAM),
        'SNVS':   int(imx.EnumEngine.HAB_ENG_SNVS),
        'OCOTP':  int(imx.EnumEngine.HAB_ENG_OCOTP),
        'DTCP':   int(imx.EnumEngine.HAB_ENG_DTCP),
        'ROM':    int(imx.EnumEngine.HAB_ENG_ROM),
        'HDCP':   int(imx.EnumEngine.HAB_ENG_HDCP),
        'SW':     int(imx.EnumEngine.HAB_ENG_SW)
    }

    dcd = imx.SegDCD(True)
    cmd = None

    for line in text_file.split('\n'):
        line = line.rstrip('\0')
        # ignore comments
        if not line or line.startswith('#'):
            continue
        # Split line and validate command
        cmd_line = line.split(' ')
        if cmd_line[0] not in cmds:
            continue
        # Parse command
        if cmd_line[0] == 'Nop':
            if cmd is not None:
                dcd.append(cmd)
                cmd = None

            dcd.append(imx.CmdNop())

        elif cmd_line[0] == 'Unlock':
            if cmd is not None:
                dcd.append(cmd)
                cmd = None

            if cmd_line[1] not in engines:
                raise SyntaxError("Unlock CMD: wrong engine")

            engine = engines[cmd_line[1]]
            data   = [int(value, 0) for value in cmd_line[2:]]
            dcd.append(imx.CmdUnlock(engine, data))

        elif cmds[cmd_line[0]][0] == 'write':

            if len(cmd_line) < 4:
                raise SyntaxError("Write CMD: too weak arguments")

            ops   = cmds[cmd_line[0]][1]
            bytes = int(cmd_line[1])
            addr  = int(cmd_line[2], 0)
            value = int(cmd_line[3], 0)

            if cmd is not None:
                if cmd.ops != ops or cmd.bytes != bytes:
                    dcd.append(cmd)
                    cmd = None

            if cmd is None:
                cmd = imx.CmdWriteData(bytes, ops)

            cmd.append(addr, value)
        else:
            if len(cmd_line) < 4:
                raise SyntaxError("Check CMD: too weak arguments")

            if cmd is not None:
                dcd.append(cmd)
                cmd = None

            ops   = cmds[cmd_line[0]][1]
            bytes = int(cmd_line[1])
            addr  = int(cmd_line[2], 0)
            mask  = int(cmd_line[3], 0)
            count = int(cmd_line[4], 0) if len(cmd_line) > 4 else None
            dcd.append(imx.CmdCheckData(bytes, ops, addr, mask, count))

    if cmd is not None:
        dcd.append(cmd)

    return dcd


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


# Instance of custom argument types
UINT = UInt()


########################################################################################################################
## CLI
########################################################################################################################

# Application error code
ERROR_CODE = 1

# The version of IMX module
VERSION = imx.__version__

# Short description of imxim tool
DESCRIP = (
    "IMX Image Manager, ver.: " + VERSION + "\n\n"
    "NOTE: This tool is still in deep development. Please, be carefully with it usage !\n"
)


# IMX Image: Base options
@click.group(context_settings=dict(help_option_names=['-?', '--help']), help=DESCRIP)
@click.version_option(VERSION, '-v', '--version')
def cli():
    click.echo()


# IMX Image: List IMX boot image content
@cli.command(short_help="List IMX boot image content")
@click.option('-o', '--offset', type=UINT, default=0, show_default=True, help="File Offset")
@click.argument('file', nargs=1, type=click.Path(exists=True))
def info(offset, file):
    """ List IMX boot image content """
    try:
        data = bytearray(os.path.getsize(file) - offset)

        with open(file, 'rb') as f:
            f.seek(offset)
            f.readinto(data)

        img = imx.BootImage()
        img.parse(data)

        click.echo(str(img))

    except Exception as e:
        click.echo(str(e) if str(e) else "Unknown Error !")
        sys.exit(ERROR_CODE)


# IMX Image: Create new IMX boot image from attached files
@cli.command(short_help="Create new IMX boot image from attached files")
@click.argument('address', nargs=1, type=UINT)
@click.argument('dcdfile', nargs=1, type=click.Path(exists=True))
@click.argument('appfile', nargs=1, type=click.Path(exists=True))
@click.argument('outfile', nargs=1, type=click.Path(readable=False))
@click.option('-c', '--csf', type=click.Path(exists=True), help="CSF File")
@click.option('-o', '--offset', type=UINT, default=0x400, show_default=True, help="IVT Offset")
@click.option('-p/', '--plugin/', is_flag=True, default=False, show_default=True, help="Plugin Image")
def create(address, dcdfile, appfile, outfile, offset, plugin, csf=None):
    """ Create new IMX boot image from attached files """
    try:
        img = imx.BootImage(address = address, offset = offset, plugin = plugin)

        # Open and import application image
        with open(appfile, 'rb') as f:
            img.app = f.read()

        # Open and import DCD segment
        if dcdfile.lower().endswith('.txt'):
            with open(dcdfile, 'r') as f:
                img.dcd = parse_dcd(f.read())
        else:
            with open(dcdfile, 'rb') as f:
                img.dcd.parse(f.read())

        # Open and import CSF segment
        if csf:
            raise NotImplementedError('CSF support will be added later')

        # Save as IMX Boot image
        with open(outfile, 'wb') as f:
            f.write(img.export())

    except Exception as e:
        click.echo(str(e) if str(e) else "Unknown Error !")
        sys.exit(ERROR_CODE)

    click.secho(" Image successfully created\n Path: %s\n" % outfile)


# IMX Image: Extract IMX boot image content
@cli.command(short_help="Extract IMX boot image content")
@click.argument('file', nargs=1, type=click.Path(exists=True))
@click.option('-o', '--offset', type=UINT, default=0x400, show_default=True, help="IVT Offset")
@click.option('-f', '--format', type=click.Choice(('bin', 'txt')), default='bin', show_default=True,
              help="DCD and CSF section output format")
def extract(file, offset, format):
    """ Extract IMX boot image content """
    try:
        # Create IMX image instance
        img = imx.BootImage(offset = offset)

        # Open and parse IMX image
        with open(file, 'rb') as f:
            img.parse(f.read())

        msg  = "---------------------------\n"
        msg += "     Image Description\n"
        msg += "---------------------------\n"
        msg += "Start Address: 0x{0:08X}\n".format(img.address)
        msg += "IVT Offset:    0x{0:X}\n".format(img.offset)

        # Create extraction dir
        file_path, file_name = os.path.split(file)
        out_path = os.path.normpath(os.path.join(file_path, file_name + ".ex"))
        os.makedirs(out_path, exist_ok=True)

        # Save APP Segment
        with open(os.path.join(out_path, 'app.bin'), 'wb') as f:
            msg += "APP Segment:   app.bin\n"
            f.write(img.app)

        # Save DCD Segment
        if img.dcd.enabled:
            if format == 'txt':
                msg += "DCD Segment:   dcd.txt\n"
                with open(os.path.join(out_path, 'dcd.txt'), 'w') as f:
                    f.write(export_dcd(img.dcd))
            else:
                msg += "DCD Segment:   dcd.bin\n"
                with open(os.path.join(out_path, 'dcd.bin'), 'wb') as f:
                    f.write(img.dcd.export())

        # Save CSF Segment
        if img.csf.enabled:
            #msg += "CSF Segment:   csf.bin\n"
            #with open(os.path.join(out_path, 'csf.bin'), 'wb') as f:
            #    f.write(img.csf.export())
            pass

        # Save image info into nfo.txt file
        with open(os.path.join(out_path, 'nfo.txt'), 'w') as f:
            f.write(msg)

    except Exception as e:
        click.echo(str(e) if str(e) else "Unknown Error !")
        sys.exit(ERROR_CODE)

    click.secho(" Image successfully extracted\n Path: %s\n" % out_path)


def main():
    cli(obj={})


if __name__ == '__main__':
    main()
