pyIMX
=====

This repository collects a useful tools and python module targeted for [IMX Applications Processors](http://www.nxp.com/products/microcontrollers-and-processors/arm-based-portfolio/i.mx-applications-processors).

> This project is still in developing phase. Please, test it and report the issues.

Dependencies
------------

- [Python 3.x](https://www.python.org) - The interpreter
- [Click](http://click.pocoo.org/6) - Python package for creating beautiful command line interface.
- [PyWinUSB](https://github.com/rene-aguirre/pywinusb) - Python package that simplifies USB-HID communications on Windows OS.
- [PyUSB](https://walac.github.io/pyusb/) - Python package to access USB devices in Linux OS.
- [pyserial](https://github.com/pyserial/pyserial) - Python package for communication over Serial port in Linux and Windows OS.
- [pyYAML](http://pyyaml.org/wiki/PyYAML) - YAML parser and emitter for the Python programming language.
- [pyUBoot](https://github.com/molejar/pyUBoot) - Python package for for manipulating with U-Boot images and environment variables.

Installation
------------

To install the latest development version (master branch) execute in shell the following command:

``` bash
    $ pip3 install --pre -U https://github.com/molejar/pyIMX/archive/master.zip
```

NOTE: you may run into permissions issues running these commands.
You have a few options here:

1. Run with `sudo -H` to install pyIMX and dependencies globally
2. Specify the `--user` option to install local to your user
3. Run the command in a [virtualenv](https://virtualenv.pypa.io/en/latest/) local to a specific project working set.

You can also install from source by executing in shell the following commands:

``` bash
    $ git clone https://github.com/molejar/pyIMX.git
    $ cd pyIMX
    $ pip3 install .
```

Usage
-----

The example of IMX boot image manager API usage:

``` Python
    import imx

    # --------------------------------------------------------------------------------
    # Create new U-Boot IMX image
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
    # Extract DCD from existing U-Boot IMX image
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

Python IMX module is distributed with following command-line utilities (tools):
* [imxim](doc/imxim.md) - a tool for manipulation with `*.imx` boot image
* [imxsd](doc/imxsd.md) - a tool to download and execute code on i.MX/Vibrid SoCs through the Serial Download Protocol (SDP)
* [imxsb](doc/imxsb.md) - a tool for managed boot of IMX device caled as "IMX Smart-Boot"

TODO
----

* Add image security features (sign and encryption)
* Complete serial interface support in IMX serial downloader module
