# Copyright (c) 2017-2018 Martin Olejar
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


def test_ivt2_segment():
    ivt = img.SegIVT2(0x41)

    assert ivt.header.tag == 0xD1
    assert ivt.header.length == ivt.SIZE
