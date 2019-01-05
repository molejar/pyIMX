#!/usr/bin/env python

# Copyright (c) 2017-2018 Martin Olejar
#
# SPDX-License-Identifier: BSD-3-Clause
# The BSD-3-Clause license for this file can be found in the LICENSE file included with this distribution
# or at https://spdx.org/licenses/BSD-3-Clause.html#licenseText

import os
import sys
import yaml
import click

from imx.img import parse, SegDCD, BootImg2, BootImg3a, BootImg3b, BootImg4, EnumAppType
from imx import __version__


########################################################################################################################
# Helper methods
########################################################################################################################
def get_path(root_dir, file_path):
    path = None
    for abs_path in [file_path, os.path.join(root_dir, file_path)]:
        abs_path = os.path.normpath(abs_path)
        if os.path.exists(abs_path):
            path = abs_path
            break

    if path is None:
        raise Exception("PATH: \"%s\" doesn't exist !" % file_path)

    return path


def load_dcd(root_dir, data):
    file_type = 'bin'
    dcd_obj = None

    if 'TYPE' in data:
        file_type = data['TYPE'].lower()

    if 'PATH' in data:
        path = get_path(root_dir, data['PATH'])
        if path.endswith('.txt') or file_type == 'txt':
            with open(path, 'r') as f:
                dcd_obj = SegDCD.parse_txt(f.read())
        else:
            with open(path, 'rb') as f:
                dcd_obj = SegDCD.parse(f.read())
    elif 'DATA' in data:
        dcd_obj = SegDCD.parse_txt(data['DATA'])
    else:
        raise Exception("DCD->PATH or DCD->DATA must be defined !")

    return dcd_obj


########################################################################################################################
# New argument types
########################################################################################################################

class UInt(click.ParamType):
    """ Custom argument type for UINT """
    name = 'UINT'

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
# CLI
########################################################################################################################

# Application error code
ERROR_CODE = 1

# Application version
VERSION = __version__

# Application description
DESCRIP = (
    "i.MX Boot Image Manager, ver.: " + VERSION + " Beta\n\n"
    "NOTE: Development version, be carefully with it usage !\n"
)


# IMX Image: Base options
@click.group(context_settings=dict(help_option_names=['-?', '--help']), help=DESCRIP)
@click.version_option(VERSION, '-v', '--version')
def cli():
    click.echo()


# IMX Image: List IMX boot img content
@cli.command(short_help="List i.MX boot image content")
@click.option('-t', '--type', type=click.Choice(['auto', '67RT', '8M', '8QXP_A0', '8QM_A0', '8X']),
              default='auto', show_default=True, help="Image type")
@click.option('-o', '--offset', type=UINT, default=0, show_default=True, help="File Offset")
@click.option('-s', '--step', type=UINT, default=0x100, show_default=True, help="Parsing step")
@click.argument('file', nargs=1, type=click.Path(exists=True))
def info(offset, type, step, file):
    """ List i.MX boot image content """
    try:
        with open(file, 'rb') as stream:
            stream.seek(offset)
            if type == "auto":
                boot_image = parse(stream, step)
            else:
                img_type = {'67RT': BootImg2,
                            '8M': BootImg2,
                            '8QXP_A0': BootImg3a,
                            '8QM_A0': BootImg3b,
                            '8X': BootImg4}
                boot_image = img_type[type].parse(stream, step)

        # print image info
        click.echo(str(boot_image))

    except Exception as e:
        click.echo(str(e) if str(e) else "Unknown Error !")
        sys.exit(ERROR_CODE)


@cli.command(short_help="Create new i.MX6/7/RT boot image from attached files")
@click.argument('address', nargs=1, type=UINT)
@click.argument('appfile', nargs=1, type=click.Path(exists=True))
@click.argument('outfile', nargs=1, type=click.Path(readable=False))
@click.option('-d', '--dcd', type=click.Path(exists=True), default=None, help="DCD File (*.txt or *.bin)")
@click.option('-c', '--csf', type=click.Path(exists=True), default=None, help="CSF File (*.txt or *.bin)")
@click.option('-o', '--offset', type=UINT, default=0x400, show_default=True, help="IVT Offset")
@click.option('-v', '--version', type=UINT, default=0x41, help="Header Version [default: 0x41]")
@click.option('-p/', '--plugin/', is_flag=True, default=False, help="Plugin Image if used")
def create2a(address, appfile, outfile, dcd, csf, offset, plugin, version):
    """ Create new i.MX6/7/RT boot image from attached files """
    try:
        boot_image = BootImg2(address, offset, version, plugin)

        # Open and import application image
        with open(appfile, 'rb') as f:
            boot_image.app.data = f.read()

        # Open and load/parse DCD segment
        if dcd is not None:
            if dcd.lower().endswith('.txt'):
                with open(dcd, 'r') as f:
                    boot_image.dcd = SegDCD.parse_txt(f.read())
            else:
                with open(dcd, 'rb') as f:
                    boot_image.dcd = SegDCD.parse(f.read())

        # Open and load/parse CSF segment
        if csf is not None:
            raise NotImplementedError('CSF support will be added later')

        # Save as IMX Boot image
        with open(outfile, 'wb') as f:
            f.write(boot_image.export())

    except Exception as e:
        click.echo(str(e) if str(e) else "Unknown Error !")
        sys.exit(ERROR_CODE)

    click.secho(" Image successfully created\n Path: %s\n" % outfile)


@cli.command(short_help="Create new i.MX8M boot image from attached files")
@click.argument('address', nargs=1, type=UINT)
@click.argument('appfile', nargs=1, type=click.Path(exists=True))
@click.argument('outfile', nargs=1, type=click.Path(readable=False))
@click.option('-d', '--dcd', type=click.Path(exists=True), default=None, help="DCD File (*.txt or *.bin)")
@click.option('-c', '--csf', type=click.Path(exists=True), default=None, help="CSF File (*.txt or *.bin)")
@click.option('-o', '--offset', type=UINT, default=0x400, show_default=True, help="IVT Offset")
@click.option('-v', '--version', type=UINT, default=0x43, help="Header Version [default: 0x43]")
@click.option('-p/', '--plugin/', is_flag=True, default=False, help="Plugin Image if used")
def create2b(address, appfile, outfile, dcd, csf, offset, plugin, version):
    """ Create new i.MX8M boot image from attached files """
    try:
        boot_image = BootImg2(address, offset, version, plugin)

        # Open and import application image
        with open(appfile, 'rb') as f:
            boot_image.app.data = f.read()

        # Open and load/parse DCD segment
        if dcd is not None:
            if dcd.lower().endswith('.txt'):
                with open(dcd, 'r') as f:
                    boot_image.dcd = SegDCD.parse_txt(f.read())
            else:
                with open(dcd, 'rb') as f:
                    boot_image.dcd = SegDCD.parse(f.read())

        # Open and load/parse CSF segment
        if csf is not None:
            raise NotImplementedError('CSF support will be added later')

        # Save as IMX Boot image
        with open(outfile, 'wb') as f:
            f.write(boot_image.export())

    except Exception as e:
        click.echo(str(e) if str(e) else "Unknown Error !")
        sys.exit(ERROR_CODE)

    click.secho(" Image successfully created\n Path: %s\n" % outfile)


@cli.command(short_help="Create new i.MX8QXP boot image from attached files")
@click.argument('scfw', nargs=1, type=click.Path(exists=True))
@click.argument('outfile', nargs=1, type=click.Path(readable=False))
@click.option('-a', '--app', default=None, help="Application image \"address|path;...\"")
@click.option('-m', '--cm4', default=None, help="Cortex-M4 binary \"address|core|path;...\", core: 0/1")
@click.option('-d', '--dcd', type=click.Path(exists=True), default=None, help="DCD File (*.txt or *.bin)")
@click.option('-s', '--scd', type=click.Path(exists=True), default=None, help="SCD File (*.bin)")
@click.option('-c', '--csf', type=click.Path(exists=True), default=None, help="CSF File (*.txt or *.bin)")
@click.option('-o', '--offset', type=UINT, default=0x400, show_default=True, help="IVT Offset")
@click.option('-v', '--version', type=UINT, default=0x43, help="Header Version [default: 0x43]")
def create3a(scfw, outfile, app, m4, dcd, scd, csf, offset, version):
    """ Create new i.MX8QXP boot image from attached files """
    try:
        boot_image = BootImg3a(0, offset, version)

        with open(scfw, 'rb') as f:
            boot_image.add_image(f.read(), EnumAppType.SCFW)

        # Open and load APP segment
        if app is not None:
            images_list = app.split(";")
            for image in images_list:
                address, path = image.split("|")
                address = int(address, 0)
                with open(path, 'rb') as f:
                    boot_image.add_image(f.read(), EnumAppType.A35, address)

        # Open and load M4 segment
        if m4 is not None:
            images_list = m4.split(";")
            images_type = {'0': EnumAppType.M4_0, '1': EnumAppType.M4_1}
            for image in images_list:
                address, core, path = image.split("|")
                with open(path, 'rb') as f:
                    boot_image.add_image(f.read(), images_type[core], int(address, 0))

        # Open and load SCD segment
        if scd is not None:
            with open(scd, 'rb') as f:
                boot_image.add_image(f.read(), EnumAppType.SCD)

        # Open and load/parse DCD segment
        if dcd is not None:
            if dcd.lower().endswith('.txt'):
                with open(dcd, 'r') as f:
                    boot_image.dcd = SegDCD.parse_txt(f.read())
                    boot_image.dcd.header.param = 0x43
            else:
                with open(dcd, 'rb') as f:
                    boot_image.dcd = SegDCD.parse(f.read())

        # Open and load/parse CSF segment
        if csf is not None:
            raise NotImplementedError('CSF support will be added later')

        # Save as IMX Boot image
        with open(outfile, 'wb') as f:
            f.write(boot_image.export())

    except Exception as e:
        click.echo(str(e) if str(e) else "Unknown Error !")
        sys.exit(ERROR_CODE)

    click.secho(" Image successfully created\n Path: %s\n" % outfile)


@cli.command(short_help="Create new i.MX8QM boot image from attached files")
@click.argument('scfw', nargs=1, type=click.Path(exists=True))
@click.argument('outfile', nargs=1, type=click.Path(readable=False))
@click.option('-a', '--app', default=None, help="Application image \"address|core|path;...\", core: A53/A72")
@click.option('-m', '--cm4', default=None, help="Cortex-M4 binary \"address|core|path;...\", core: 0/1")
@click.option('-d', '--dcd', type=click.Path(exists=True), default=None, help="DCD File (*.txt or *.bin)")
@click.option('-s', '--scd', type=click.Path(exists=True), default=None, help="SCD File (*.bin)")
@click.option('-c', '--csf', type=click.Path(exists=True), default=None, help="CSF File (*.txt or *.bin)")
@click.option('-o', '--offset', type=UINT, default=0x400, show_default=True, help="IVT Offset")
@click.option('-v', '--version', type=UINT, default=0x43, help="Header Version [default: 0x43]")
def create3b(scfw, outfile, app, m4, dcd, scd, csf, offset, version):
    """ Create new i.MX8QM boot image from attached files """
    try:
        boot_image = BootImg3b(0, offset, version)

        with open(scfw, 'rb') as f:
            boot_image.add_image(f.read(), EnumAppType.SCFW)

        # Open and load APP segment
        if app is not None:
            images_list = app.split(";")
            images_type = {"A53": EnumAppType.A53, "A72": EnumAppType.A72}
            for image in images_list:
                address, core, path = image.split("|")
                with open(path, 'rb') as f:
                    boot_image.add_image(f.read(), images_type[core], int(address, 0))

        # Open and load M4 segment
        if m4 is not None:
            images_list = m4.split(";")
            images_type = {'0': EnumAppType.M4_0, '1': EnumAppType.M4_1}
            for image in images_list:
                address, core, path = image.split("|")
                with open(path, 'rb') as f:
                    boot_image.add_image(f.read(), images_type[core], int(address, 0))

        # Open and load SCD segment
        if scd is not None:
            with open(scd, 'rb') as f:
                boot_image.add_image(f.read(), EnumAppType.SCD)

        # Open and load/parse DCD segment
        if dcd is not None:
            if dcd.lower().endswith('.txt'):
                with open(dcd, 'r') as f:
                    boot_image.dcd = SegDCD.parse_txt(f.read())
                    boot_image.dcd.header.param = 0x43
            else:
                with open(dcd, 'rb') as f:
                    boot_image.dcd = SegDCD.parse(f.read())

        # Open and load/parse CSF segment
        if csf is not None:
            raise NotImplementedError('CSF support will be added later')

        # Save as IMX Boot image
        with open(outfile, 'wb') as f:
            f.write(boot_image.export())

    except Exception as e:
        click.echo(str(e) if str(e) else "Unknown Error !")
        sys.exit(ERROR_CODE)

    click.secho(" Image successfully created\n Path: %s\n" % outfile)


@cli.command(short_help="Create new i.MX6/7/8/RT boot image")
@click.argument('infile', nargs=1, type=click.Path(exists=True))
@click.argument('outfile', nargs=1, type=click.Path(readable=False))
def create(infile, outfile):
    """ Create new i.MX6/7/8/RT boot image. \n
        INFILE - The i.MX boot image description file (*.yml) \n
        OUTFILE - The name of created i.MX boot image (*.imx)
    """

    # Supported images
    image_types = {'APP':     EnumAppType.APP,
                   'SCD':     EnumAppType.SCD,
                   'SCFW':    EnumAppType.SCFW,
                   'CM4-0':   EnumAppType.M4_0,
                   'CM4-1':   EnumAppType.M4_1,
                   'APP-A35': EnumAppType.A35,
                   'APP-A53': EnumAppType.A53,
                   'APP-A72': EnumAppType.A72}

    try:
        with open(infile, 'r') as f:
            data = yaml.load(f)

        # store path of yaml file
        yaml_dir = os.path.abspath(os.path.dirname(infile))

        # Validate key attribute
        if 'TARGET' not in data:
            raise Exception("Attribute \"TARGET\" must be defined !")

        if data['TARGET'].lower() == 'imx67':
            address = data['ADDRESS'] if 'ADDRESS' in data else 0
            version = data['VERSION'] if 'VERSION' in data else 0x41
            offset = data['OFFSET'] if 'OFFSET' in data else 0x400
            plugin = data['PLUGIN'] if 'PLUGIN' in data else False

            boot_image = BootImg2(address, offset, version, plugin)

        elif data['TARGET'] == 'imx8m':
            address = data['ADDRESS'] if 'ADDRESS' in data else 0
            version = data['VERSION'] if 'VERSION' in data else 0x41
            offset = data['OFFSET'] if 'OFFSET' in data else 0x400
            plugin = data['PLUGIN'] if 'PLUGIN' in data else False

            boot_image = BootImg2(address, offset, version, plugin)

        elif data['TARGET'] == 'imx8qxp':
            offset  = data['OFFSET'] if 'OFFSET' in data else 0x400
            address = data['ADDRESS'] if 'ADDRESS' in data else 0
            version = data['VERSION'] if 'VERSION' in data else 0x43

            boot_image = BootImg3a(address, offset, version)

        elif data['TARGET'] == 'imx8qm':
            offset  = data['OFFSET'] if 'OFFSET' in data else 0x400
            address = data['ADDRESS'] if 'ADDRESS' in data else 0
            version = data['VERSION'] if 'VERSION' in data else 0x43

            boot_image = BootImg3b(address, offset, version)

        else:
            raise Exception("Not supported TARGET: {} !".format(data['TARGET']))

        if 'DCD' in data:
            boot_image.dcd = load_dcd(yaml_dir, data['DCD'])

        for img in data['IMAGES']:
            # Validate key attributes
            if 'PATH' not in img:
                raise Exception("Attribute IMAGES->\"PATH\" must be defined !")
            if 'TYPE' not in img:
                raise Exception("Attribute IMAGES->\"TYPE\" must be defined !")
            if img['TYPE'] not in image_types:
                raise Exception("Not supported IMAGES->TYPE: {} !".format(img['TYPE']))

            # Get image type
            image_type = image_types[img['TYPE']]
            # Get image address
            image_addr = img['ADDR'] if 'ADDR' in img else 0

            # Add new image data into IMX Boot image
            with open(get_path(yaml_dir, img['PATH']), 'rb') as f:
                boot_image.add_image(f.read(), image_type, image_addr)

        # Save as IMX Boot image
        with open(outfile, 'wb') as f:
            f.write(boot_image.export())

    except Exception as e:
        click.echo(str(e) if str(e) else "Unknown Error !")
        sys.exit(ERROR_CODE)

    click.secho(" Image successfully created\n Path: %s\n" % outfile)


@cli.command(short_help="Extract i.MX boot image content")
@click.argument('file', nargs=1, type=click.Path(exists=True))
@click.option('-t', '--type', type=click.Choice(['auto', '67RT', '8M', '8QXP', '8QM']),
              default='auto', show_default=True, help="Image type")
@click.option('-e/', '--embedded/', is_flag=True, default=False, show_default=True,
              help="Embed DCD into image description file")
@click.option('-o', '--offset', type=UINT, default=0, show_default=True, help="Input file offset")
@click.option('-s', '--step', type=UINT, default=0x100, show_default=True, help="Parsing step")
def extract(file, type, offset, step, embedded):
    """ Extract IMX boot img content """
    img_type = {'67RT': BootImg2, '8M': BootImg2, '8QXP': BootImg3a, '8QM': BootImg3b}

    try:
        # Open and parse IMX img
        with open(file, 'rb') as buffer:
            buffer.seek(offset)
            img_obj = parse(buffer, step) if type == "auto" else img_type[type].parse(buffer, step)

        # Create extract directory
        file_path, file_name = os.path.split(file)
        out_path = os.path.normpath(os.path.join(file_path, file_name + ".ex"))
        os.makedirs(out_path, exist_ok=True)

        # Get image key attributes
        image_offset = img_obj.offset
        image_address = img_obj.address
        image_version = None
        image_plugin = None
        images = []

        if isinstance(img_obj, BootImg2):
            image_target = 'imx8m' if img_obj.version == 0x43 else 'imx67'
            image_version = img_obj.version
            image_plugin = 'yes' if img_obj.plugin else 'no'
            # Save Extracted Image
            images.append({'TYPE': 'APP', 'PATH': 'app.bin'})
            with open(os.path.join(out_path, 'app.bin'), 'wb') as f:
                f.write(img_obj.app.data)

        elif isinstance(img_obj, BootImg3a):
            image_target = 'imx8qxp'
            # Save Extracted Images
            for c in range(img_obj.COUNT_OF_CONTAINERS):
                for i in range(img_obj.bdt[c].images_count):
                    if img_obj.bdt[c].images[i].scfw_flags == BootImg3a.SCFW_FLAGS_APP:
                        image_type = 'APP-A35'
                    elif img_obj.bdt[c].images[i].scfw_flags == BootImg3a.SCFW_FLAGS_M4_0:
                        image_type = 'CM4-0'
                    elif img_obj.bdt[c].images[i].scfw_flags == BootImg3a.SCFW_FLAGS_M4_1:
                        image_type = 'CM4-1'
                    elif img_obj.bdt[c].images[i].scfw_flags == BootImg3a.SCFW_FLAGS_SCFW:
                        image_type = 'SCFW'
                    elif img_obj.bdt[c].images[i].hab_flags == BootImg3a.IMG_TYPE_SCD:
                        image_type = 'SCD'
                    else:
                        pass

                    image_name = "{}-{}.bin".format(image_type.lower(), c)
                    images.append({
                        'TYPE': image_type,
                        'CONT': c,
                        'ADDR': img_obj.bdt[c].images[i].image_entry,
                        'PATH': image_name
                    })

                    with open(os.path.join(out_path, image_name), 'wb') as f:
                        f.write(img_obj.app[c][i].data)
        else:
            image_target = 'imx8qm'
            # Save Extracted Images
            for c in range(img_obj.COUNT_OF_CONTAINERS):
                for i in range(img_obj.bdt[c].images_count):
                    if img_obj.bdt[c].images[i].flags == BootImg3b.SCFW_FLAGS_A72:
                        image_type = 'APP-A72'
                    elif img_obj.bdt[c].images[i].flags == BootImg3b.SCFW_FLAGS_A53:
                        image_type = 'APP-A53'
                    elif img_obj.bdt[c].images[i].flags == BootImg3b.SCFW_FLAGS_M4_0:
                        image_type = 'CM4-0'
                    elif img_obj.bdt[c].images[i].flags == BootImg3b.SCFW_FLAGS_M4_1:
                        image_type = 'CM4-1'
                    elif img_obj.bdt[c].images[i].flags == BootImg3b.SCFW_FLAGS_SCFW:
                        image_type = 'SCFW'
                    elif img_obj.bdt[c].images[i].flags == BootImg3b.IMG_TYPE_SCD:
                        image_type = 'SCD'
                    else:
                        pass

                    image_name = "{}-{}.bin".format(image_type.lower(), c)
                    images.append({
                        'TYPE': image_type,
                        'CONT': c,
                        'ADDR': img_obj.bdt[c].images[i].image_entry,
                        'PATH': image_name
                    })

                    with open(os.path.join(out_path, image_name), 'wb') as f:
                        f.write(img_obj.app[c][i].data)

        yaml_string = '#' * 40
        yaml_string += '\n# i.MX Boot Image Description File\n'
        yaml_string += '#' * 40
        yaml_string += '\n\n'
        yaml_string += '# Boot Image Target Platform:\n'
        yaml_string += '# imx67   - i.MX6xx and i.MX7xx\n'
        yaml_string += '# imx8m   - i.MX8M (M-Scale 850D, cores: A53 + M4)\n'
        yaml_string += '# imx8qm  - i.MX8QM (cores: A72 + A53 + M4)\n'
        yaml_string += '# imx8qxp - i.MX8QXP (cores: A35 + M4)\n'
        yaml_string += 'TARGET: {}\n'.format(image_target)
        yaml_string += '\n# Boot Image IVT Offset\n'
        yaml_string += 'OFFSET: 0x{:X}\n'.format(image_offset)
        yaml_string += '\n# Boot Image Address\n'
        if isinstance(image_address, list):
            yaml_string += 'ADDRESS_0: 0x{:08X}\n'.format(image_address[0])
            yaml_string += 'ADDRESS_1: 0x{:08X}\n'.format(image_address[1])
        else:
            yaml_string += 'ADDRESS: 0x{:08X}\n'.format(image_address)
        if image_version is not None:
            yaml_string += 'VERSION: 0x{:x}\n'.format(image_version)
        if image_plugin is not None:
            yaml_string += 'PLUGIN: {}\n'.format(image_plugin)

        # Save DCD Segment
        if img_obj.dcd.enabled:
            yaml_string += '\n# Device Configuration Data and DDR Initialization\n'
            yaml_string += 'DCD:\n'
            yaml_string += '  TYPE: TXT\n'
            if embedded:
                yaml_string += '  DATA: |\n'
                dcd_txt = img_obj.dcd.export_txt()
                for line in dcd_txt.split('\n'):
                    #if line.strip():
                    yaml_string += '    {}\n'.format(line)
            else:
                yaml_string += '  PATH: dcd.txt\n'
                with open(os.path.join(out_path, 'dcd.txt'), 'w') as f:
                    f.write(img_obj.dcd.export_txt())

        # Save CSF Segment
        if img_obj.csf.enabled:
            pass

        # Export images description into YAML string
        yaml_string += '\n# List of Executables\n'
        yaml_string += 'IMAGES:\n'
        for img in images:
            yaml_string += '\n'
            yaml_string += '  - TYPE: {}\n'.format(img['TYPE'])
            if 'CONT' in img:
                yaml_string += '    CONT: {:d}\n'.format(img['CONT'])
            if 'ADDR' in img:
                yaml_string += '    ADDR: 0x{:X}\n'.format(img['ADDR'])
            yaml_string += '    PATH: {}\n'.format(img['PATH'])

        # Save image description yaml file
        with open(os.path.join(out_path, '{}-img.yml'.format(image_target)), 'w') as f:
            f.write(yaml_string)

    except Exception as e:
        click.echo(str(e) if str(e) else "Unknown Error !")
        sys.exit(ERROR_CODE)

    click.secho(" Image successfully extracted\n Path: %s\n" % out_path)


@cli.command(short_help="DCD file converter (*.bin, *.txt)")
@click.argument('outfile', nargs=1, type=click.Path(readable=False))
@click.argument('infile', nargs=1, type=click.Path(exists=True))
@click.option('-o', '--outfmt', type=click.Choice(['txt', 'bin']),
              default='bin', show_default=True, help="Output file format")
@click.option('-i', '--infmt', type=click.Choice(['txt', 'bin']),
              default='txt', show_default=True, help="Input file format")
def dcdfc(outfile, infile, outfmt, infmt):
    """ DCD file converter """
    try:
        if infmt == 'bin':
            with open(infile, 'rb') as f:
                dcd = SegDCD.parse(f.read())
        else:
            with open(infile, 'r') as f:
                dcd = SegDCD.parse_txt(f.read())

        if outfmt == 'bin':
            # Save DCD as BIN File
            with open(outfile, 'wb') as f:
                f.write(dcd.export())
        else:
            # Save DCD as TXT File
            with open(outfile, 'w') as f:
                f.write(dcd.export_txt())

    except Exception as e:
        click.echo(str(e) if str(e) else "Unknown Error !")
        sys.exit(ERROR_CODE)

    click.secho(" Conversion was successful\n Output: %s\n" % outfile)


def main():
    cli(obj={})


if __name__ == '__main__':
    main()
