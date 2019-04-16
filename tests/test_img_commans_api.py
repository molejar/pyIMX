# Copyright (c) 2019 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
# The BSD-3-Clause license for this file can be found in the LICENSE file included with this distribution
# or at https://spdx.org/licenses/BSD-3-Clause.html#licenseText

import pytest
from imx import img


def test_write_value_cmd():
    cmd = img.CmdWriteData(data=((0, 1),))
    assert cmd.bytes == 4
    assert cmd.ops == img.EnumWriteOps.WRITE_VALUE
    assert len(cmd) == 1
    assert cmd[0] == [0, 1]

    data = cmd.export()
    assert len(data) == 12
    assert cmd == img.CmdWriteData.parse(data)


def test_set_bit_mask_cmd():
    cmd = img.CmdWriteData(ops=img.EnumWriteOps.SET_BITMASK)
    cmd.append(0, 1)
    assert cmd.bytes == 4
    assert cmd.ops == img.EnumWriteOps.SET_BITMASK
    assert len(cmd) == 1
    assert cmd[0] == [0, 1]

    data = cmd.export()
    assert len(data) == 12
    assert cmd == img.CmdWriteData.parse(data)


def test_clear_bit_mask_cmd():
    cmd = img.CmdWriteData(ops=img.EnumWriteOps.CLEAR_BITMASK)
    cmd.append(0, 1)
    cmd.append(1, 1)
    assert cmd.bytes == 4
    assert cmd.ops == img.EnumWriteOps.CLEAR_BITMASK
    assert len(cmd) == 2
    assert cmd[1] == [1, 1]

    data = cmd.export()
    assert len(data) == 20
    assert cmd == img.CmdWriteData.parse(data)


def test_check_any_clear_cmd():
    cmd = img.CmdCheckData(ops=img.EnumCheckOps.ANY_CLEAR, address=0, mask=0x00000001, count=5)
    assert cmd.bytes == 4
    assert cmd.ops == img.EnumCheckOps.ANY_CLEAR
    assert cmd.address == 0
    assert cmd.mask == 0x00000001
    assert cmd.count == 5

    data = cmd.export()
    assert len(data) == 16
    assert cmd == img.CmdCheckData.parse(data)


def test_check_all_clear_cmd():
    cmd = img.CmdCheckData(bytes=2, ops=img.EnumCheckOps.ALL_CLEAR, address=0, mask=0xFFFF)
    assert cmd.bytes == 2
    assert cmd.ops == img.EnumCheckOps.ALL_CLEAR
    assert cmd.address == 0
    assert cmd.mask == 0xFFFF
    assert cmd.count is None

    data = cmd.export()
    assert len(data) == 12
    assert cmd == img.CmdCheckData.parse(data)


def test_nop_cmd():
    cmd = img.CmdNop(param=0)
    assert cmd is not None
    assert cmd.size == 4

    data = cmd.export()
    assert len(data) == 4
    assert cmd == img.CmdNop.parse(data)


def test_set_cmd():
    cmd = img.CmdSet()
    assert cmd.itm == img.EnumItm.ENG
    assert cmd.size == 8


def test_initialize_cmd():
    cmd = img.CmdInitialize()
    assert cmd.engine == img.EnumEngine.ANY
    assert cmd.size == 4


def test_unlock_cmd():
    cmd = img.CmdUnlock()
    assert cmd.engine == img.EnumEngine.ANY
    assert cmd.size == 16


def test_install_key_cmd():
    cmd = img.CmdInstallKey()
    assert cmd.flags == img.EnumInsKey.CLR
    assert cmd.certificate_format == img.EnumCertFormat.SRK
    assert cmd.hash_algorithm == img.EnumAlgorithm.ANY
    assert cmd.source_index == 0
    assert cmd.target_index == 0
    assert cmd.key_location == 0
    assert cmd.size == 12


def test_authenticate_data_cmd():
    cmd = img.CmdAuthData()
    assert cmd.flags == img.EnumAuthDat.CLR
    assert cmd.key_index == 1
    assert cmd.engine == img.EnumEngine.ANY
    assert cmd.engine_cfg == 0
    assert cmd.location == 0
    assert cmd.size == 12
