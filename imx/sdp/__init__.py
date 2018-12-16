# Copyright (c) 2017-2018 Martin Olejar
#
# SPDX-License-Identifier: BSD-3-Clause
# The BSD-3-Clause license for this file can be found in the LICENSE file included with this distribution
# or at https://spdx.org/licenses/BSD-3-Clause.html#licenseText

from .sdp import SdpBase, SdpMX8, SdpMX67, SdpMXRT, SdpGenericError, SdpCommandError, SdpConnectionError, \
                 SdpDataError, SdpSecureError, SdpTimeoutError

__all__ = [
    # Classes
    'SdpMX8',
    'SdpMXRT',
    'SdpMX67',
    # Errors
    'SdpGenericError',
    'SdpCommandError',
    'SdpConnectionError',
    'SdpDataError',
    'SdpSecureError',
    'SdpTimeoutError',
    # methods
    'scan_usb',
    'get_devices_name'
]


def get_devices_name():
    """
    :return:
    """
    names = []

    for sdc in (SdpMXRT, SdpMX67, SdpMX8):
        names += sdc.DEVICES.keys()

    return names


def scan_usb(dev_name=None):
    """ IMX SD: Scan commected USB devices
    :param: dev_name The device name (MX6DQP, MX6SDL, ...) or USB device VID:PID value
    :rtype : list
    """
    fls = []

    for sdc in (SdpMXRT, SdpMX67, SdpMX8):
        fls += sdc.scan_usb(dev_name)

    return fls
