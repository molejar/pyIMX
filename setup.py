#!/usr/bin/env python

# Copyright (c) 2017 Martin Olejar, martin.olejar@gmail.com
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
# Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import sys
from setuptools import setup, find_packages

sys.path.insert(0, './src')
import imx

requirements = ['click>=6.0', 'pyserial>=3.0', 'PyYAML>=3.10', 'Jinja2>=2.6', 'uboot>=0.0.7']

if sys.platform.startswith('linux'):
    requirements.append('pyusb>=1.0.0b2')
elif sys.platform.startswith('win'):
    requirements.append('pywinusb>=0.4.0')
else:
    raise Exception('Not supported platform !')

setup(
    name='imx',
    version=imx.__version__,
    license='MIT',
    author='Martin Olejar',
    author_email='martin.olejar@gmail.com',
    url='https://github.com/molejar/pyIMX',
    platforms="Windows, Linux",
    python_requires=">=3.1",
    install_requires=requirements,
    packages=find_packages('src'),
    include_package_data = True,
    package_dir={'':'src'},
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: POSIX :: Linux',
        'Operating System :: Microsoft :: Windows',
        'License :: OSI Approved :: MIT License',
        'Topic :: Scientific/Engineering',
        'Topic :: Software Development :: Embedded Systems',
        'Topic :: System :: Hardware',
        'Topic :: Utilities'
    ],
    description='Open Source library for easy development with i.MX platform',
    #scripts=['src/imxim.py', 'src/imxsb.py', 'src/imxsd.py'],
    py_modules=['imxim', 'imxsb', 'imxsd'],
    entry_points={
        'console_scripts': [
            'imxim = imxim:main',
            'imxsb = imxsb:main',
            'imxsd = imxsd:main'
        ],
    }
)
