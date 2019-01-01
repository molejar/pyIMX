# Copyright (c) 2017-2018 Martin Olejar
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
DCD_TXT = os.path.join(DATA_DIR, 'dcd_test.txt')


def setup_module(module):
    # Prepare test environment
    pass


def teardown_module(module):
    # Clean test environment
    pass


def test_01():

    with open(DCD_TXT, 'r') as f:
        dcd_obj = img.SegDCD.parse_txt(f.read())

    assert len(dcd_obj) == 12
