# Copyright (c) 2017-2018 Martin Olejar
#
# SPDX-License-Identifier: BSD-3-Clause
# The BSD-3-Clause license for this file can be found in the LICENSE file included with this distribution
# or at https://spdx.org/licenses/BSD-3-Clause.html#licenseText

from easy_enum import EEnum as Enum


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
    UNKNOWN = (0x00, 'Unknown')
    WARNING = (0x69, 'Warning')
    ERROR = (0x33, 'Failure')
    OK = (0xF0, 'Success')


class EnumHabReason(Enum):
    UNKNOWN = (0x00, 'Unknown Reason')
    ENGINE_FAILURE = (0x30, 'Engine Failure')
    INVALID_ADDRESS = (0x22, 'Invalid Address: Access Denied')
    INVALID_ASSERTION = (0x0C, 'Invalid Assertion')
    INVALID_CERTIFICATE = (0x21, 'Invalid Certificate')
    INVALID_COMMAND = (0x06, 'Invalid Command: Malformed')
    INVALID_CSF = (0x11, 'Invalid CSF')
    INVALID_DCD = (0x27, 'Invalid DCD')
    INVALID_IVT = (0x05, 'Invalid IVT')
    INVALID_KEY = (0x1D, 'Invalid Key')
    INVALID_MAC = (0x32, 'Invalid MAC')
    INVALID_BLOB = (0x31, 'Invalid Blob')
    INVALID_INDEX = (0x0F, 'Invalid Index: Access Denied')
    FAILED_CALLBACK = (0x1E, 'Failed Callback Function')
    INVALID_SIGNATURE = (0x18, 'Invalid Signature')
    INVALID_DATA_SIZE = (0x17, 'Invalid Data Size')
    MEMORY_FAILURE = (0x2E, 'Memory Failure')
    CALL_OUT_OF_SEQUENCE = (0x28, 'Function Called Out Of Sequence')
    EXPIRED_POLL_COUNT = (0x2B, 'Expired Poll Count')
    EXHAUSTED_STORAGE_REGION = (0x2D, 'Exhausted Storage Region')
    UNSUPPORTED_ALGORITHM = (0x12, 'Unsupported Algorithm')
    UNSUPPORTED_COMMAND = (0x03, 'Unsupported Command')
    UNSUPPORTED_ENGINE = (0x0A, 'Unsupported Engine')
    UNSUPPORTED_CONF_ITEM = (0x24, 'Unsupported Configuration Item')
    UNSUPPORTED_KEY_OR_PARAM = (0x1B, 'Unsupported Key Type or Parameters')
    UNSUPPORTED_PROTOCOL = (0x14, 'Unsupported Protocol')
    UNSUITABLE_STATE = (0x09, 'Unsuitable State')


class EnumHabContext(Enum):
    HAB_FAB_TEST = (0xFF, 'Event logged in hab_fab_test()')
    # HAB_CTX_ANY = (0x00, 'Match any context in hab_rvt.report_event()')   it is in HAB4 API doc, is it new?
    HAB_RVT_ENTRY = (0xE1, 'Event logged in hab_rvt.entry()')
    RVT_CHECK_TARGET = (0x33, 'Event logged in hab_rvt.check_target()')
    RVT_AUTHENTICATE_IMG = (0x0A, 'Event logged in hab_rvt.authenticate_image()')
    RVT_RUN_DCD = (0xDD, 'Event logged in hab_rvt.run_dcd()')
    RVT_RUN_CSF = (0xCF, 'Event logged in hab_rvt.run_csf()')
    RVT_CSF_DCD_CMD = (0xC0, 'Event logged executing CSF or DCD command')
    RVT_ASSERT = (0xA0, 'Event logged in hab_rvt.assert()')
    RVT_EXIT = (0xEE, 'Event logged in hab_rvt.exit()')
    AUTH_DATA_BLOCK = (0xDB, 'Authenticated data block')

