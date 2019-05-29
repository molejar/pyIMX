# Copyright (c) 2019 Martin Olejar
#
# SPDX-License-Identifier: BSD-3-Clause
# The BSD-3-Clause license for this file can be found in the LICENSE file included with this distribution
# or at https://spdx.org/licenses/BSD-3-Clause.html#licenseText

import os
import pytest
from imx import img
from cryptography import x509
from cryptography.hazmat.backends import default_backend

# Used Directories
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

# Test Files
SRK_TABLE = os.path.join(DATA_DIR, 'SRK_1_2_3_4_table.bin')
SRK_FUSES = os.path.join(DATA_DIR, 'SRK_1_2_3_4_fuse.bin')


def setup_module(module):
    global srk_pem

    srk_pem = []
    for i in range(4):
        srk_pem_file = 'SRK{}_sha256_4096_65537_v3_ca_crt.pem'.format(i+1)
        with open(os.path.join(DATA_DIR, srk_pem_file), 'rb') as f:
            srk_pem.append(f.read())


def test_srk_table_parser():
    with open(SRK_TABLE, 'rb') as f:
        srk_table = img.SrkTable.parse(f.read())

    assert len(srk_table) == 4
    assert srk_table.size == 2112

    with open(SRK_FUSES, 'rb') as f:
        srk_fuses = f.read()

    assert srk_table.export_fuses() == srk_fuses


def test_srk_table_export():
    srk_table = img.SrkTable(version=0x40)

    for pem_data in srk_pem:
        cert = x509.load_pem_x509_certificate(pem_data, default_backend())
        srk_table.append(img.SrkItem.from_certificate(cert))

    with open(SRK_TABLE, 'rb') as f:
        srk_table_data = f.read()

    assert srk_table.export() == srk_table_data
    assert srk_table == img.SrkTable.parse(srk_table_data)


def test_mac_class():
    mac = img.MAC(version=0x40)

    assert mac.size == 8
    assert mac.info()


def test_signature_class():
    sig = img.Signature(version=0x40)

    assert sig.size == 4
    assert sig.info()


def test_certificate_class():
    cer = img.Certificate(version=0x40)

    assert cer.size == 4
    assert cer.info()


def test_secret_key_blob_class():
    sec_key = img.SecretKeyBlob(mode=0, algorithm=0, flag=0)
    sec_key.blob = bytes([0xFF] * 32)

    assert sec_key.size == 36
    assert sec_key.info()
