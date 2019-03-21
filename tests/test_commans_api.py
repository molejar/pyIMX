# Copyright (c) 2019 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
# The BSD-3-Clause license for this file can be found in the LICENSE file included with this distribution
# or at https://spdx.org/licenses/BSD-3-Clause.html#licenseText

import os
import pytest
from imx import img


def test_write_value_cmd():
    cmd = img.CmdWriteData(data=((0, 1),))
    assert cmd.bytes == 4
    assert cmd.ops == img.EnumWriteOps.WRITE_VALUE
    assert len(cmd) == 1
    assert cmd[0] == [0, 1]


def test_set_bit_mask_cmd():
    cmd = img.CmdWriteData(ops=img.EnumWriteOps.SET_BITMASK)
    cmd.append(0, 1)
    assert cmd.bytes == 4
    assert cmd.ops == img.EnumWriteOps.SET_BITMASK
    assert len(cmd) == 1
    assert cmd[0] == [0, 1]


def test_clear_bit_mask_cmd():
    cmd = img.CmdWriteData(ops=img.EnumWriteOps.CLEAR_BITMASK)
    cmd.append(0, 1)
    cmd.append(1, 1)
    assert cmd.bytes == 4
    assert cmd.ops == img.EnumWriteOps.CLEAR_BITMASK
    assert len(cmd) == 2
    assert cmd[1] == [1, 1]


def test_check_any_clear_cmd():
    cmd = img.CmdCheckData(ops=img.EnumCheckOps.ANY_CLEAR, address=0, mask=0x00000001, count=5)
    assert cmd.bytes == 4
    assert cmd.ops == img.EnumCheckOps.ANY_CLEAR
    assert cmd.address == 0
    assert cmd.mask == 0x00000001
    assert cmd.count == 5


def test_check_all_clear_cmd():
    cmd = img.CmdCheckData(bytes=2, ops=img.EnumCheckOps.ALL_CLEAR, address=0, mask=0xFFFF)
    assert cmd.bytes == 2
    assert cmd.ops == img.EnumCheckOps.ALL_CLEAR
    assert cmd.address == 0
    assert cmd.mask == 0xFFFF
    assert cmd.count is None


def test_nop_cmd():
    cmd = img.CmdNop(param=0)
    assert cmd is not None
    assert cmd.size == 4

