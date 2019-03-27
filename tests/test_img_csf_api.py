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
CSF_TXT = os.path.join(DATA_DIR, 'csf_test.txt')
CSF_BIN = os.path.join(DATA_DIR, 'csf_test.bin')


def setup_module(module):
    # Prepare reference CSF object
    global ref_csf_obj

    ref_csf_obj = img.SegCSF(enabled=True)
    ref_csf_obj.append(img.CmdWriteData(ops=img.EnumWriteOps.WRITE_VALUE, data=((0x30340004, 0x4F400005),)))
    ref_csf_obj.append(img.CmdCheckData(ops=img.EnumCheckOps.ALL_CLEAR, address=0x307900C4, mask=0x00000001, count=10))


def test_txt_parser():
    pass


def test_bin_parser():
    pass
