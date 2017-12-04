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
import imx


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

# Application version
VERSION = imx.__version__

# Application description
DESCRIP = (
    "IMX Image Manager, ver.: " + VERSION + " Beta\n\n"
    "NOTE: Development version, be carefully with it usage !\n"
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
@click.argument('appfile', nargs=1, type=click.Path(exists=True))
@click.argument('outfile', nargs=1, type=click.Path(readable=False))
@click.option('-d', '--dcd', type=click.Path(exists=True), help="DCD File (*.txt or *.bin)")
@click.option('-c', '--csf', type=click.Path(exists=True), help="CSF File (*.txt or *.bin)")
@click.option('-o', '--offset', type=UINT, default=0x400, show_default=True, help="IVT Offset")
@click.option('-p/', '--plugin/', is_flag=True, default=False, help="Plugin Image if used")
def create(address, appfile, outfile, offset, plugin, dcd, csf):
    """ Create new IMX boot image from attached files """
    try:
        img = imx.BootImage(address = address, offset = offset, plugin = plugin)

        # Open and import application image
        with open(appfile, 'rb') as f:
            img.app = f.read()

        # Open and load/parse DCD segment
        if dcd:
            if dcd.lower().endswith('.txt'):
                with open(dcd, 'r') as f:
                    img.dcd.load(f.read())
            else:
                with open(dcd, 'rb') as f:
                    img.dcd.parse(f.read())

        # Open and load/parse CSF segment
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
                    f.write(img.dcd.store())
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

    click.secho(" Image successfully extracted\n Output: %s\n" % out_path)


# IMX Image: DCD file converter
@cli.command(short_help="DCD file converter (*.bin, *.txt)")
@click.argument('outfile', nargs=1, type=click.Path(readable=False))
@click.argument('infiles', nargs=-1, type=click.Path(exists=True))
@click.option('-o', '--outfmt', type=click.Choice(['txt', 'bin']),
              default='bin', show_default=True, help="Output file format")
@click.option('-i', '--infmt', type=click.Choice(['txt', 'bin']),
              default='txt', show_default=True, help="Input file format")
def dcdfc(outfile, infiles, outfmt, infmt):
    """ DCD file converter """
    try:
        dcd = imx.SegDCD()

        if not isinstance(infiles, (list, tuple)):
            infiles = [infiles]
        for file in infiles:
            if infmt == 'bin':
                with open(file, 'rb') as f:
                    dcd.parse(f.read())
            else:
                with open(file, 'r') as f:
                    dcd.load(f.read(), False)

        if outfmt == 'bin':
            # Save DCD as BIN File
            with open(outfile, 'wb') as f:
                f.write(dcd.export())
        else:
            # Save DCD as TXT File
            with open(outfile, 'w') as f:
                f.write(dcd.store())

    except Exception as e:
        click.echo(str(e) if str(e) else "Unknown Error !")
        sys.exit(ERROR_CODE)

    click.secho(" Conversion was successful\n Output: %s\n" % outfile)


def main():
    cli(obj={})


if __name__ == '__main__':
    main()
