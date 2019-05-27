# Copyright (c) 2019 Martin Olejar
#
# SPDX-License-Identifier: BSD-3-Clause
# The BSD-3-Clause license for this file can be found in the LICENSE file included with this distribution
# or at https://spdx.org/licenses/BSD-3-Clause.html#licenseText

import os
import pytest
from imx import img

# Used Directories
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

# Test Files
UBOOT_IMX = os.path.join(DATA_DIR, 'imx7d_uboot.imx')


def setup_module(module):
    # Prepare test environment
    pass


def teardown_module(module):
    # Clean test environment
    pass


def test_create_image_api():
    image = img.BootImg2()

    assert image.version == 0x41
    assert image.address == 0
    assert image.offset == 0x400
    assert image.size == 44

    data = image.export()
    assert len(data) == 44

    image.add_image(bytes([0x20] * 100))
    assert image.size == 144

    data = image.export()
    assert len(data) == 4000 + 140

    assert image.info()


def test_parse_image_api():
    with open(UBOOT_IMX, 'rb') as f:
        image = img.BootImg2.parse(f.read())

    assert isinstance(image, img.BootImg2)
    assert image.version == 0x40
    assert image.address == 0x877FF000
    assert image.offset == 0x400
    assert image.size == 478208

    assert image.info()
