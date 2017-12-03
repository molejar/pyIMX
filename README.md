pyIMX
=====

This repository collects a useful tools and python module targeted for [i.MX Applications Processors](http://www.nxp.com/products/microcontrollers-and-processors/arm-based-portfolio/i.mx-applications-processors).

> This project is still in developing phase. Please, test it and report the issues.

Dependencies
------------

- [Python 3.x](https://www.python.org) - The interpreter
- [Click](http://click.pocoo.org/6) - Python package for creating beautiful command line interface.
- [PyWinUSB](https://github.com/rene-aguirre/pywinusb) - Python package that simplifies USB-HID communications on Windows OS.
- [PyUSB](https://walac.github.io/pyusb/) - Python package to access USB devices in Linux OS.
- [pyserial](https://github.com/pyserial/pyserial) - Python package for communication over Serial port in Linux and Windows OS.
- [pyYAML](http://pyyaml.org/wiki/PyYAML) - YAML parser and emitter for the Python programming language.
- [Jinja2](https://pypi.python.org/pypi/Jinja2) - A small but fast and easy to use stand-alone template engine.
- [pyUBoot](https://github.com/molejar/pyUBoot) - Python package for manipulation with U-Boot images and environment variables.
- [pyFDT](https://github.com/molejar/pyFDT) - Python package for manipulation with Device Tree images.

Installation
------------

To install the latest version from master branch execute in shell following commands:

``` bash
    $ pip3 install -r https://raw.githubusercontent.com/molejar/pyIMX/master/requirements.txt
    $ pip3 install -U https://github.com/molejar/pyIMX/archive/master.zip
```

In case of development, install it from cloned sources:

``` bash
    $ git clone https://github.com/molejar/pyIMX.git
    $ cd pyIMX
    $ pip3 install -r requirements.txt
    $ pip3 install -U -e .
```

**NOTE:** You may run into a permissions issues running these commands. Here are a few options how to fix it:

1. Run with `sudo` to install pyIMX and dependencies globally
2. Specify the `--user` option to install locally into your home directory (export "~/.local/bin" into PATH variable if haven't).
3. Run the command in a [virtualenv](https://virtualenv.pypa.io/en/latest/) local to a specific project working set.


Usage
-----

The example of i.MX boot image manager API usage:

``` Python
    import imx

    # --------------------------------------------------------------------------------
    # Create new U-Boot i.MX image
    # --------------------------------------------------------------------------------

    # Create DCD segnent instance
    dcd = imx.SegDCD()

    # Create Write Data command and append values with addresses
    cmd = imx.CmdWriteData(4, imx.EnumWriteOps.WRITE_VALUE)
    cmd.append(0x30340004, 0x4F400005)
    cmd.append(0x30391000, 0x00000002)
    cmd.append(0x307A0000, 0x01040001)
    ...

    # Append commands into DCD segment
    dcd.append(cmd)
    dcd.append(imx.CmdCheckData(4, imx.EnumCheckOps.ANY_CLEAR, 0x307900C4, 0x00000001))

    # Open U-Boot raw image
    with open('u-boot.img', 'rb') as f:
        app = f.read()

    # Create IMX U-Boot image with DCD segment
    img = imx.BootImage(0x877FF000, app, dcd)

    # Print image info
    print(img)

    # Save IMX U-Boot image
    with open('u-boot.imx', 'wb') as f:
        f.write(img.export())

    # --------------------------------------------------------------------------------
    # Extract DCD from existing U-Boot i.MX image
    # --------------------------------------------------------------------------------

    # Create IMX image instance
    img = imx.Image()

    # Open U-Boot IMX image
    with open('u-boot.imx', 'rb') as f:
        data = f.read()

    # Parse U-Boot IMX image
    img.parse(data)

    # Extract DCD from U-Boot IMX image
    dcd = img.dcd

    # Print extracted DCD info
    print(dcd)

    # Save extracted DCD content as raw image
    with open('dcd.img', 'wb') as f:
        f.write(dcd.export())

    # Save extracted DCD content as readable text file
    with open('dcd.txt', 'w') as f:
        f.write(dcd.store())
```

The example of IMX serial downloader API usage:

``` Python
    import imx

    # scan for connected USB devs
    devs = imx.SerialDownloader.scan_usb()

    if devs:
        # Create Flasher instance
        flasher = imx.SerialDownloader()

        # Connect IMX Device
        flasher.open_usb(devs[0])

        # Read data from IMX Device (i.MX7D OCRAM)
        data = flasher.read(0x910000, 100, 8)

        # Write boot image data into IMX Device (i.MX7D OCRAM)
        flasher.write_file(0x910000, data)

        ...

        # Disconnect IMX Device
        flasher.close()
```

Python i.MX module is distributed with following command-line utilities (tools):
* [imxim](doc/imxim.md) - a tool for manipulation with `*.imx` boot image
* [imxsd](doc/imxsd.md) - a tool to download and execute code on i.MX/Vibrid SoCs through the Serial Download Protocol (SDP)
* [imxsb](doc/imxsb.md) - a tool for managed boot of i.MX device caled as "i.MX Smart-Boot"

TODO
----

* Add image security features (sign and encryption)
* Complete serial interface support in i.MX serial downloader module
