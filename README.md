pyIMX
=====

[![Build Status](https://travis-ci.org/molejar/pyIMX.svg?branch=master)](https://travis-ci.org/molejar/pyIMX)
[![Coverage Status](https://coveralls.io/repos/github/molejar/pyIMX/badge.svg?branch=master)](https://coveralls.io/github/molejar/pyIMX?branch=master)
[![PyPI Status](https://img.shields.io/pypi/v/imx.svg)](https://pypi.python.org/pypi/imx)
[![Python Version](https://img.shields.io/pypi/pyversions/imx.svg)](https://www.python.org)

This repository collects a useful tools and python module targeted for [i.MX Applications Processors](https://www.nxp.com/products/processors-and-microcontrollers/arm-based-processors-and-mcus/i.mx-applications-processors).

**What is implemented:**

* DCD (Device Configuration Data) API
* Boot Image v2 (i.MX6 and i.MX7) API
* Boot Image v3 (i.MX8QM-A0 and i.MX8QXP-A0) API
* SDP (Serial Download Protocol) API - only USB interface
* HAB-Log parser (only i.MX6 and i.MX7 yet)

**Embedded tools:**

* [imxim](https://github.com/molejar/pyIMX/blob/master/doc/imxim.md) - a tool for manipulation with `*.imx` boot image
* [imxsd](https://github.com/molejar/pyIMX/blob/master/doc/imxsd.md) - a tool to download and execute code on i.MX/Vibrid SoCs through the Serial Download Protocol (SDP)

> This project is still in developing phase. Please, test it and report founded issues.

Dependencies
------------

- [Python](https://www.python.org) - Python 3.x interpreter
- [Click](http://click.pocoo.org/6) - Python package for creating beautiful command line interface.
- [pyYAML](http://pyyaml.org/wiki/PyYAML) - YAML parser and emitter for the Python programming language.
- [PyUSB](https://walac.github.io/pyusb/) - Python package to access USB devices in Linux OS.
- [PyWinUSB](https://github.com/rene-aguirre/pywinusb) - Python package that simplifies USB-HID communications on 
Windows OS.

Installation
------------

``` bash
    $ pip install imx
```

To install the latest version from master branch execute in shell following commands:

``` bash
    $ pip install -r https://raw.githubusercontent.com/molejar/pyIMX/master/requirements.txt
    $ pip install -U https://github.com/molejar/pyIMX/archive/master.zip
```

In case of development, install pyIMX from sources:

``` bash
    $ git clone https://github.com/molejar/pyIMX.git
    $ cd pyIMX
    $ pip install -r requirements.txt
    $ pip install -U -e .
```

You may run into a permissions issues running these commands. Here are a few options how to fix it:

1. Run with `sudo` to install pyIMX and dependencies globally
2. Specify the `--user` option to install locally into your home directory (export "~/.local/bin" into PATH variable if haven't).
3. Run the command in a [virtualenv](https://virtualenv.pypa.io/en/latest/) local to a specific project working set.

Usage
-----

In following example is demonstrated the simplicity of usage i.MX boot image API covered by `imx.img` module:

``` Python
    import imx

    # --------------------------------------------------------------------------------
    # Create new U-Boot i.MX6/7 image
    # --------------------------------------------------------------------------------

    # Create DCD segnent instance
    dcd = imx.img.SegDCD()

    # Create Write Data command and append values with addresses
    cmd = imx.img.CmdWriteData(4, imx.img.EnumWriteOps.WRITE_VALUE)
    cmd.append(0x30340004, 0x4F400005)
    cmd.append(0x30391000, 0x00000002)
    cmd.append(0x307A0000, 0x01040001)
    ...

    # Append commands into DCD segment
    dcd.append(cmd)
    dcd.append(imx.img.CmdCheckData(4, imx.img.EnumCheckOps.ANY_CLEAR, 0x307900C4, 0x00000001))

    # Open U-Boot raw image
    with open('u-boot.img', 'rb') as f:
        app = f.read()

    # Create IMX U-Boot image with DCD segment
    image = imx.img.BootImg2(0x877FF000, app, dcd)

    # Print image info
    print(image)

    # Save IMX U-Boot image
    with open('u-boot.imx', 'wb') as f:
        f.write(image.export())

    # --------------------------------------------------------------------------------
    # Extract DCD from existing U-Boot i.MX6/7 image
    # --------------------------------------------------------------------------------

    # Open U-Boot IMX image
    with open('u-boot.imx', 'rb') as f:
        data = f.read()

    # Parse U-Boot IMX image
    image = imx.img.BootImg2.parse(data)

    # Extract DCD from U-Boot IMX image
    dcd = image.dcd

    # Print extracted DCD info
    print(dcd)

    # Save extracted DCD content as raw image
    with open('dcd.img', 'wb') as f:
        f.write(dcd.export())

    # Save extracted DCD content as readable text file
    with open('dcd.txt', 'w') as f:
        f.write(dcd.store())
```

Second example demonstrate usage of i.MX serial downloader protocol API covered by `imx.sdp` module:

``` Python
    import imx

    # scan for connected USB devs
    devs = imx.sdp.scan_usb()

    if devs:
        i = 0
        for dev in devs:
            print("{}) {}".format(i, dev.usbd.info))
            i += 1

        # Connect to first i.MX device
        flasher = devs[0]
        flasher.open()

        # Read data from IMX Device (i.MX7D OCRAM)
        data = flasher.read(0x910000, 100, 8)

        # Write boot image data into IMX Device (i.MX7D OCRAM)
        flasher.write_file(0x910000, data)

        ...

        # Disconnect IMX Device
        flasher.close()
```

> For running `imx.sdp` module without root privileges in Linux OS copy attached udev rules
[90-imx-sdp.rules](https://github.com/molejar/pyIMX/blob/master/udev/90-imx-sdp.rules)
into `/etc/udev/rules.d` directory and reload it with command: `sudo udevadm control --reload-rules`.

TODO
----

* Add serial interface support for `imx.sdp` module
* Add image security features (sign and encryption)
* Add eFuses read, write and validation functionality
* Add HAB-log parser for i.MX-RT and i.MX8 devices
* Add support for QSPI Flash image
