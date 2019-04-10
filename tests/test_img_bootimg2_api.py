# Copyright (c) 2019 Martin Olejar
#
# SPDX-License-Identifier: BSD-3-Clause
# The BSD-3-Clause license for this file can be found in the LICENSE file included with this distribution
# or at https://spdx.org/licenses/BSD-3-Clause.html#licenseText

import os
import pytest
from imx import img


def setup_module(module):
    # Prepare test environment
    pass


def teardown_module(module):
    # Clean test environment
    pass


def test_create_image():
    image = img.BootImg2()

    assert image.size == 44

    data = image.export()
    assert len(data) == 44

    image.add_image(bytes([0x20] * 100))
    assert image.size == 144

    data = image.export()
    assert len(data) == 4000 + 140

    assert image.info()
