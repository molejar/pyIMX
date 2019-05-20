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
SRK_TABLE = os.path.join(DATA_DIR, 'SRK_1_2_3_4_table.bin')
SRK_FUSES = os.path.join(DATA_DIR, 'SRK_1_2_3_4_fuse.bin')


def setup_module(module):
    pass


def test_srk_table_parser():
    with open(SRK_TABLE, 'rb') as f:
        srk_table = img.SrkTable.parse(f.read())

    assert len(srk_table) == 4
    assert srk_table.size == 2112

    with open(SRK_FUSES, 'rb') as f:
        srk_fuses = f.read()

    assert srk_table.export_fuses() == srk_fuses


def test_srk_table_export():
    pass
