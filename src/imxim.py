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


# IMX Image: List image content
@cli.command(short_help="List image content")
@click.option('-o', '--offset', type=UINT, default=0, show_default=True, help="File Offset")
@click.argument('file', nargs=1, type=click.Path(exists=True))
def info(offset, file):
    """ List image content """
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


# IMX Image: Create new image from attached file
@cli.command(short_help="Create new image from attached file")
@click.argument('address', nargs=1, type=UINT)
@click.argument('infile', nargs=1, type=click.Path(exists=True))
@click.argument('outfile', nargs=1, type=click.Path(readable=False))
@click.option('-d', '--dcd', type=click.Path(exists=True), help="DCD File")
@click.option('-c', '--csf', type=click.Path(exists=True), help="CSF File")
@click.option('-o', '--offset', type=UINT, default=0x400, show_default=True, help="IVT Offset")
@click.option('-p/', '--plugin/', is_flag=True, default=False, show_default=True, help="Plugin Image")
def create(address, infile, outfile, offset, plugin, dcd=None, csf=None):
    """ Create new image from attached file """

    #try:
    img = imx.BootImage(address = address, offset = offset, plugin= plugin)

    with open(infile, 'rb') as f:
        img.app = f.read()

    if dcd:
        if dcd.lower().endswith(('.txt', '.dcd', '.yaml')):
            raise NotImplementedError()
        else:
            with open(dcd, 'rb') as f:
                img.dcd.parse(f.read())
    if csf:
        raise NotImplementedError()

    with open(outfile, 'wb') as f:
        f.write(img.export())

    #except Exception as e:
    #    click.echo(str(e) if str(e) else "Unknown Error !")
    #    sys.exit(ERROR_CODE)

    click.secho("Image successfully created: %s" % outfile)


# IMX Image: Extract image content
@cli.command(short_help="Extract image content")
@click.argument('file', nargs=1, type=click.Path(exists=True))
@click.option('-o', '--offset', type=UINT, default=0x400, show_default=True, help="IVT Offset")
def extract(file, offset):
    """ Extract image content """

    try:
        # Create IMX image instance
        img = imx.BootImage(offset = offset)
        # Open and parse IMX image
        with open(file, 'rb') as f:
            img.parse(f.read())
        # Create extraction dir
        file_path, file_name = os.path.split(file)
        out_path = os.path.normpath(os.path.join(file_path, file_name + ".ex"))
        os.makedirs(out_path, exist_ok=True)
        # Save U-Boot Image
        with open(os.path.join(out_path, 'u-boot.bin'), 'wb') as f:
            f.write(img.app)
        # Save DCD Section
        if img.dcd.enabled:
            with open(os.path.join(out_path, 'dcd.bin'), 'wb') as f:
                f.write(img.dcd.export())
        # Save CSF Section
        if img.csf.enabled:
            #with open(os.path.join(out_path, 'csf.bin'), 'wb') as f:
            #    f.write(img.csf.export())
            pass

    except Exception as e:
        click.echo(str(e) if str(e) else "Unknown Error !")
        sys.exit(ERROR_CODE)

    click.secho("Image successfully extracted into dir: %s" % out_path)


def main():
    cli(obj={})


if __name__ == '__main__':
    main()
