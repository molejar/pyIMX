# Copyright (c) 2017-2018 Martin Olejar
#
# SPDX-License-Identifier: BSD-3-Clause
# The BSD-3-Clause license for this file can be found in the LICENSE file included with this distribution
# or at https://spdx.org/licenses/BSD-3-Clause.html#licenseText


########################################################################################################################
# Enum Base Class
########################################################################################################################

class Enum(object):

    @classmethod
    def is_valid(cls, value):
        return True if value in cls.desc else False

    @classmethod
    def get_desc(cls, value):
        return cls.desc[value] if cls.is_valid(value) else "Unknown"


########################################################################################################################
# Device type Flags
########################################################################################################################

class EnumDevType:
    IMX6 = 6
    IMX7 = 7


########################################################################################################################
# Status Flags
########################################################################################################################

class EnumHabStatus(Enum):
    UNKNOWN = 0x00
    WARNING = 0x69
    ERROR = 0x33
    OK = 0xF0

    desc = {
        UNKNOWN: 'Unknown',
        ERROR:   'Failure',  # Operation Failed (Not Completed)
        WARNING: 'Warning',  # Operation Completed With Warning
        OK:      'Success'   # Operation Completed Successfully
    }


class EnumHabReason(Enum):
    UNKNOWN = 0x00
    ENGINE_FAILURE = 0x30
    INVALID_ADDRESS = 0x22
    INVALID_ASSERTION = 0x0C
    INVALID_CERTIFICATE = 0x21
    INVALID_COMMAND = 0x06
    INVALID_CSF = 0x11
    INVALID_DCD = 0x27
    INVALID_IVT = 0x05
    INVALID_KEY = 0x1D
    INVALID_MAC = 0x32
    INVALID_BLOB = 0x31
    INVALID_INDEX = 0x0F
    FAILED_CALLBACK = 0x1E
    INVALID_SIGNATURE = 0x18
    INVALID_DATA_SIZE = 0x17
    MEMORY_FAILURE = 0x2E
    CALL_OUT_OF_SEQUENCE = 0x28
    EXPIRED_POLL_COUNT = 0x2B
    EXHAUSTED_STORAGE_REGION = 0x2D
    UNSUPPORTED_ALGORITHM = 0x12
    UNSUPPORTED_COMMAND = 0x03
    UNSUPPORTED_ENGINE = 0x0A
    UNSUPPORTED_CONF_ITEM = 0x24
    UNSUPPORTED_KEY_OR_PARAM = 0x1B
    UNSUPPORTED_PROTOCOL = 0x14
    UNSUITABLE_STATE = 0x09

    desc = {
        UNKNOWN: 'Unknown Reason',
        ENGINE_FAILURE: 'Engine Failure',
        INVALID_ADDRESS: 'Invalid Address: Access Denied',
        INVALID_ASSERTION: 'Invalid Assertion',
        CALL_OUT_OF_SEQUENCE: 'Function Called Out Of Sequence',
        INVALID_CERTIFICATE: 'Invalid Certificate',
        INVALID_COMMAND: 'Invalid Command: Malformed',
        INVALID_CSF: 'Invalid CSF',
        INVALID_DCD: 'Invalid DCD',
        INVALID_INDEX: 'Invalid Index: Access Denied',
        INVALID_IVT: 'Invalid IVT',
        INVALID_KEY: 'Invalid Key',
        FAILED_CALLBACK: 'Failed Callback Function',
        INVALID_SIGNATURE: 'Invalid Signature',
        INVALID_DATA_SIZE: 'Invalid Data Size',
        INVALID_BLOB: 'Invalid Blob',
        INVALID_MAC: 'Invalid MAC',
        MEMORY_FAILURE: 'Memory Failure',
        EXPIRED_POLL_COUNT: 'Expired Poll Count',
        EXHAUSTED_STORAGE_REGION: 'Exhausted Storage Region',
        UNSUPPORTED_ALGORITHM: 'Unsupported Algorithm',
        UNSUPPORTED_COMMAND: 'Unsupported Command',
        UNSUPPORTED_ENGINE: 'Unsupported Engine',
        UNSUPPORTED_CONF_ITEM: 'Unsupported Configuration Item',
        UNSUPPORTED_KEY_OR_PARAM: 'Unsupported Key Type or Parameters',
        UNSUPPORTED_PROTOCOL: 'Unsupported Protocol',
        UNSUITABLE_STATE: 'Unsuitable State'
    }


class EnumHabContext(Enum):
    HAB_FAB_TEST = 0xFF
    HAB_RVT_ENTRY = 0xE1
    RVT_CHECK_TARGET = 0x33
    RVT_AUTHENTICATE_IMG = 0x0A
    RVT_RUN_DCD = 0xDD
    RVT_RUN_CSF = 0xCF
    RVT_CSF_DCD_CMD = 0xC0
    RVT_ASSERT = 0xA0
    RVT_EXIT = 0xEE
    AUTH_DATA_BLOCK = 0xDB

    desc = {
        HAB_FAB_TEST: 'Event logged in hab_fab_test()',
        HAB_RVT_ENTRY: 'Event logged in hab_rvt.entry()',
        RVT_CHECK_TARGET: 'Event logged in hab_rvt.check_target()',
        RVT_AUTHENTICATE_IMG: 'Event logged in hab_rvt.authenticate_image()',
        RVT_RUN_DCD: 'Event logged in hab_rvt.run_dcd()',
        RVT_RUN_CSF: 'Event logged in hab_rvt.run_csf()',
        RVT_CSF_DCD_CMD: 'Event logged executing CSF or DCD command',
        RVT_ASSERT: 'Event logged in hab_rvt.assert()',
        RVT_EXIT: 'Event logged in hab_rvt.exit()',
        AUTH_DATA_BLOCK: 'Authenticated data block'
    }

