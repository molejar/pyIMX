# Copyright (c) 2019 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
# The BSD-3-Clause license for this file can be found in the LICENSE file included with this distribution
# or at https://spdx.org/licenses/BSD-3-Clause.html#licenseText

import pytest
from imx import img


def test_ivt2_segment_api():
    ivt2 = img.SegIVT2(0x41)

    assert ivt2.version == 0x41
    assert ivt2.ivt_address == 0
    assert ivt2.bdt_address == 0
    assert ivt2.dcd_address == 0
    assert ivt2.app_address == 0
    assert ivt2.csf_address == 0

    with pytest.raises(ValueError):
        _ = ivt2.export()

    # set correct values
    ivt2.ivt_address = 0x877FF400
    ivt2.bdt_address = 0x877FF420
    ivt2.dcd_address = 0x877FF42C
    ivt2.app_address = 0x87800000
    ivt2.csf_address = 0

    data = ivt2.export()
    assert isinstance(data, bytes)
    assert len(data) == img.SegIVT2.SIZE

    ivt2_parsed = img.SegIVT2.parse(data)
    assert ivt2 == ivt2_parsed


def test_bdt_segment_api():
    bdt = img.SegBDT()

    assert bdt.start == 0
    assert bdt.length == 0
    assert bdt.plugin == 0
    assert bdt.padding == 0

    # set nonzero values
    bdt.start = 0x8000000
    bdt.length = 1024
    bdt.plugin = 1

    data = bdt.export()
    assert isinstance(data, bytes)
    assert len(data) == 12

    bdt_parsed = img.SegBDT.parse(data)
    assert bdt == bdt_parsed


def test_app_segment_api():
    app = img.SegAPP()

    assert app.size == 0
    assert app.padding == 0

    data = bytes([10]*10)
    app.data = data
    app.padding = 10

    assert app.size == len(data)

    data_exported = app.export()
    assert data == data_exported

    data_exported = app.export(True)
    assert len(data_exported) == 20


def test_ivt3a_segment_api():
    ivt3a = img.SegIVT3a(0)

    assert ivt3a.version == 0
    assert ivt3a.ivt_address == 0
    assert ivt3a.bdt_address == 0
    assert ivt3a.dcd_address == 0
    assert ivt3a.csf_address == 0

    with pytest.raises(ValueError):
        _ = ivt3a.export()

    # set correct values
    ivt3a.ivt_address = 0x800400
    ivt3a.bdt_address = 0x800480
    ivt3a.dcd_address = 0x800660
    ivt3a.csf_address = 0

    data = ivt3a.export()
    assert isinstance(data, bytes)
    assert len(data) == img.SegIVT3a.SIZE

    ivt3a_parsed = img.SegIVT3a.parse(data)
    assert ivt3a == ivt3a_parsed


def test_ivt3b_segment_api():
    ivt3b = img.SegIVT3b(0)

    assert ivt3b.ivt_address == 0
    assert ivt3b.bdt_address == 0
    assert ivt3b.dcd_address == 0
    assert ivt3b.scd_address == 0
    assert ivt3b.csf_address == 0

    with pytest.raises(ValueError):
        _ = ivt3b.export()

    # set correct values
    ivt3b.ivt_address = 0x2000E400
    ivt3b.bdt_address = 0x2000E480
    ivt3b.dcd_address = 0x2000E660
    ivt3b.scd_address = 0
    ivt3b.csf_address = 0

    data = ivt3b.export()
    assert isinstance(data, bytes)
    assert len(data) == img.SegIVT3b.SIZE

    ivt3b_parsed = img.SegIVT3b.parse(data)
    assert ivt3b == ivt3b_parsed
