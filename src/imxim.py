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
        img = imx.Image()
        img.parse(data)
        click.echo(str(img))

    except Exception as e:
        click.echo(str(e) if str(e) else "Unknown Error !")


# IMX Image: Create new image from attached file
@cli.command(short_help="Create new image from attached file")
@click.argument('infile', nargs=1, type=click.Path(exists=True))
@click.argument('outfile', nargs=1, type=click.Path(readable=False))
def create(infile, outfile):
    """ Create new image from attached file """
    try:

        click.secho("Done Successfully")

    except Exception as e:
        click.echo(str(e) if str(e) else "Unknown Error !")


# IMX Image: Extract image content
@cli.command(short_help="Extract image content")
@click.argument('file', nargs=1, type=click.Path(exists=True))
def extract(file):
    """ Extract image content """
    try:

        click.secho("Done Successfully")

    except Exception as e:
        click.echo(str(e) if str(e) else "Unknown Error !")


# IMX Image: Update existing image
@cli.command(short_help="Update existing image")
@click.argument('infile', nargs=1, type=click.Path(exists=True))
def update(infile):
    """ Update existing image """
    try:

        click.secho("Done Successfully")

    except Exception as e:
        click.echo(str(e) if str(e) else "Unknown Error !")


def main():
    cli(obj={})


if __name__ == '__main__':
    main()
