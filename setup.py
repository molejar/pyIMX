#!/usr/bin/env python

# Copyright (c) 2017-2018 Martin Olejar
#
# SPDX-License-Identifier: BSD-3-Clause
# The BSD-3-Clause license for this file can be found in the LICENSE file included with this distribution
# or at https://spdx.org/licenses/BSD-3-Clause.html#licenseText

from os import path
from setuptools import setup, find_packages
from imx import __version__, __license__, __author__, __contact__


def long_description():
    try:
        import pypandoc

        readme_path = path.join(path.dirname(__file__), 'README.md')
        return pypandoc.convert(readme_path, 'rst').replace('\r', '')
    except (IOError, ImportError):
        return (
            "More on: https://github.com/molejar/pyIMX"
        )


setup(
    name='imx',
    version=__version__,
    license=__license__,
    author=__author__,
    author_email=__contact__,
    url='https://github.com/molejar/pyIMX',
    description='Open Source library for easy development with i.MX platform',
    long_description=long_description(),
    platforms="Windows, Linux",
    python_requires=">=3.5",
    setup_requires=[
        'setuptools>=40.0'
    ],
    install_requires=[
        'click>=6.0',
        'PyYAML>=3.10',
        'pyusb>=1.0.0b2;platform_system!="Windows"',
        'pywinusb>=0.4.0;platform_system=="Windows"'
    ],
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
    packages=find_packages('.'),
    entry_points={
        'console_scripts': [
            'imxim = imx.img.__main__:main',
            'imxsd = imx.sdp.__main__:main',
        ],
    }
)
