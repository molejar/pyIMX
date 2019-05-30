# Copyright (c) 2019 Martin Olejar
#
# SPDX-License-Identifier: BSD-3-Clause
# The BSD-3-Clause license for this file can be found in the LICENSE file included with this distribution
# or at https://spdx.org/licenses/BSD-3-Clause.html#licenseText

import os
import pytest
import shutil

# Used Directories
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
TEMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp')


def setup_module(module):
    # Create temp directory
    os.makedirs(TEMP_DIR, exist_ok=True)


def teardown_module(module):
    # Delete created files
    shutil.rmtree(TEMP_DIR)


@pytest.mark.script_launch_mode('subprocess')
def test_imxim_create2a(script_runner):
    ret = script_runner.run('imxim',
                            'create2a',
                            '--version', '0x41',
                            '--dcd', os.path.join(DATA_DIR, 'dcd_test.bin'),
                            '0x877FF000',
                            os.path.join(DATA_DIR, 'dcd_test.bin'),
                            os.path.join(TEMP_DIR, 'test_image.imx'))
    assert ret.success


@pytest.mark.script_launch_mode('subprocess')
def test_imxim_create2b(script_runner):
    pass


@pytest.mark.script_launch_mode('subprocess')
def test_imxim_create3a(script_runner):
    pass


@pytest.mark.script_launch_mode('subprocess')
def test_imxim_create3b(script_runner):
    pass


@pytest.mark.script_launch_mode('subprocess')
def test_imxim_create(script_runner):
    ret = script_runner.run('imxim', 'create',
                            os.path.join(DATA_DIR, 'imx7d_bootimg.yaml'),
                            os.path.join(TEMP_DIR, 'imx7d_bootimg.imx'))
    assert ret.success


@pytest.mark.script_launch_mode('subprocess')
def test_imxim_extract(script_runner):
    ret = script_runner.run('imxim', 'extract', os.path.join(TEMP_DIR, 'test_image.imx'))
    assert ret.success


@pytest.mark.script_launch_mode('subprocess')
def test_imxim_info(script_runner):
    ret = script_runner.run('imxim', 'info', os.path.join(TEMP_DIR, 'test_image.imx'))
    assert ret.success


@pytest.mark.script_launch_mode('subprocess')
def test_imxim_srktable(script_runner):
    # generate SRK table and fuses
    ret = script_runner.run('imxim',
                            'srkgen',
                            '-t', os.path.join(TEMP_DIR, 'srk_table.bin'),
                            '-f', os.path.join(TEMP_DIR, 'srk_fuses.bin'),
                            os.path.join(DATA_DIR, 'SRK1_sha256_4096_65537_v3_ca_crt.pem'),
                            os.path.join(DATA_DIR, 'SRK2_sha256_4096_65537_v3_ca_crt.pem'),
                            os.path.join(DATA_DIR, 'SRK3_sha256_4096_65537_v3_ca_crt.pem'),
                            os.path.join(DATA_DIR, 'SRK4_sha256_4096_65537_v3_ca_crt.pem'))
    assert ret.success


@pytest.mark.script_launch_mode('subprocess')
def test_imxim_dcdfc(script_runner):
    # convert DCD in TXT format to Binary format (default conversion)
    ret = script_runner.run('imxim',
                            'dcdfc',
                            os.path.join(TEMP_DIR, 'dcd_test.bin'),
                            os.path.join(DATA_DIR, 'dcd_test.txt'))
    assert ret.success

    # convert DCD in Binary format to TXT format
    ret = script_runner.run('imxim',
                            'dcdfc',
                            '-o', 'txt',
                            '-i', 'bin',
                            os.path.join(TEMP_DIR, 'dcd_test.txt'),
                            os.path.join(DATA_DIR, 'dcd_test.bin'))
    assert ret.success
