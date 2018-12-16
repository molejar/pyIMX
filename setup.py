#!/usr/bin/env python

# Copyright (c) 2017-2018 Martin Olejar
#
# SPDX-License-Identifier: BSD-3-Clause
# The BSD-3-Clause license for this file can be found in the LICENSE file included with this distribution
# or at https://spdx.org/licenses/BSD-3-Clause.html#licenseText

from setuptools import setup, find_packages
from imx import __version__, __license__, __author__, __contact__

setup(
    name='imx',
    version=__version__,
    license=__license__,
    author=__author__,
    author_email=__contact__,
    url='https://github.com/molejar/pyIMX',
    platforms="Windows, Linux",
    python_requires=">=3.5",
    packages=find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: POSIX :: Linux',
        'Operating System :: Microsoft :: Windows',
        'License :: OSI Approved :: BSD License',
        'Topic :: Scientific/Engineering',
        'Topic :: Software Development :: Embedded Systems',
        'Topic :: System :: Hardware',
        'Topic :: Utilities'
    ],
    description='Open Source library for easy development with i.MX platform',
    entry_points={
        'console_scripts': [
            'imxim = imx.img.__main__:main',
            'imxsd = imx.sdp.__main__:main',
        ],
    }
)
