pyIMX
=====

This repository collects a useful tools and python modules targeted for [IMX Applications Processors](http://www.nxp.com/products/microcontrollers-and-processors/arm-processors/i.mx-applications-processors).

> This project is still in alpha phase. Please, test it and report the issues.

Dependencies
------------

- [Python 3.x](https://www.python.org) - The interpreter
- [Click](http://click.pocoo.org/6) - Python package for creating beautiful command line interface.
- [PyWinUSB](https://github.com/rene-aguirre/pywinusb) - Python package that simplifies USB-HID communications on Windows OS.
- [PyUSB](https://walac.github.io/pyusb/) - Python package to access USB devices in Linux OS.
- [pyserial](https://github.com/pyserial/pyserial) - Python package for communication over Serial port in Linux and Windows OS.

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

The API for IMX boot image manager:

``` Python
    import imx


```

The API for IMX serial downloader:

``` Python
    import imx

    # scan for connected USB devs
    devs = imx.SerialDownloader.scanUSB()

    if devs:
        # Create Flasher instance
        flasher = imx.SerialDownloader()

        # Connect IMX Device
        flasher.connectUSB(devs[0])

        # Read data from IMX Device (i.MX7D OCRAM)
        data = flasher.read(0x910000, 100, 8)

        # Write boot image data into IMX Device (i.MX7D OCRAM)
        flasher.writeFile(0x910000, data)

        ...
```

Python IMX module is distributed with two command-line utilities (tools):
* [imxim](https://github.com/molejar/pyIMX/blob/master/doc/imxim.md) - a tool for manipulation with `*.imx` boot image
* [imxsd](https://github.com/molejar/pyIMX/blob/master/doc/imxsd.md) - a tool to download and execute code on i.MX/Vibrid SoCs through the Serial Download Protocol (SDP)

TODO
----

* Add image security features (sign and encryption) into `imxim` tool
* Finish serial interface support in IMX serial downloader module
