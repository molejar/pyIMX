pyIMX
=====

This repository collects a useful tools and python modules targeted for [IMX Applications Processors]().

Dependencies
------------

- [Python 3](https://www.python.org) - The interpreter
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

TODO: Add description

