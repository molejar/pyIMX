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
DCD_BIN = os.path.join(DATA_DIR, 'dcd_test.bin')


def setup_module(module):
    # Prepare reference DCD
    global ref_dcd_obj

    ref_dcd_obj = img.SegDCD(enabled=True)
    ref_dcd_obj.append(img.CmdWriteData(ops=img.EnumWriteOps.WRITE_VALUE, data=((0x30340004, 0x4F400005),)))
    ref_dcd_obj.append(img.CmdWriteData(ops=img.EnumWriteOps.CLEAR_BITMASK, data=((0x307900C4, 0x00000001),)))
    ref_dcd_obj.append(img.CmdWriteData(ops=img.EnumWriteOps.SET_BITMASK, data=((0x307900C4, 0x00000001),)))
    ref_dcd_obj.append(img.CmdCheckData(ops=img.EnumCheckOps.ALL_CLEAR, address=0x307900C4, mask=0x00000001))
    ref_dcd_obj.append(img.CmdCheckData(ops=img.EnumCheckOps.ALL_CLEAR, address=0x307900C4, mask=0x00000001, count=5))
    ref_dcd_obj.append(img.CmdCheckData(ops=img.EnumCheckOps.ANY_CLEAR, address=0x307900C4, mask=0x00000001))
    ref_dcd_obj.append(img.CmdCheckData(ops=img.EnumCheckOps.ANY_CLEAR, address=0x307900C4, mask=0x00000001, count=5))
    ref_dcd_obj.append(img.CmdCheckData(ops=img.EnumCheckOps.ALL_SET, address=0x307900C4, mask=0x00000001))
    ref_dcd_obj.append(img.CmdCheckData(ops=img.EnumCheckOps.ALL_SET, address=0x307900C4, mask=0x00000001, count=5))
    ref_dcd_obj.append(img.CmdCheckData(ops=img.EnumCheckOps.ANY_SET, address=0x307900C4, mask=0x00000001))
    ref_dcd_obj.append(img.CmdCheckData(ops=img.EnumCheckOps.ANY_SET, address=0x307900C4, mask=0x00000001, count=5))
    ref_dcd_obj.append(img.CmdNop())


def test_txt_parser():

    with open(DCD_TXT, 'r') as f:
        dcd_obj = img.SegDCD.parse_txt(f.read())
        # compare with reference DCD
        assert dcd_obj == ref_dcd_obj


def test_bin_parser():

    with open(DCD_BIN, 'rb') as f:
        dcd_obj = img.SegDCD.parse(f.read())
        # compare with reference DCD
        assert dcd_obj == ref_dcd_obj
