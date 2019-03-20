# Copyright (c) 2017-2018 Martin Olejar
#
# SPDX-License-Identifier: BSD-3-Clause
# The BSD-3-Clause license for this file can be found in the LICENSE file included with this distribution
# or at https://spdx.org/licenses/BSD-3-Clause.html#licenseText

from .enums import EnumDevType, EnumHabStatus, EnumHabReason, EnumHabContext
from .parser import parse_hab_log

__all__ = [
    'EnumDevType',
    'EnumHabStatus',
    'EnumHabReason',
    'EnumHabContext',
    'parse_hab_log',
    'status_info'
]


def status_info(value):
    import struct

    msg = "Status OK\n"
    status, reason, context, _ = struct.pack("<I", value)
    if status != EnumHabStatus.OK:
        msg = "{}; Reason: {} ({})".format(EnumHabStatus.desc(status), EnumHabReason.desc(reason),
                                           EnumHabContext.desc(context))
    return msg
