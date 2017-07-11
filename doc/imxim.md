IMX Image Manager
=================

The `imxim` is a tool to for manipulation with `*.imx` image.

Usage
-----

For printing a general info of usage this tool execute `imxim -?`.

```sh
    $ Usage: imxim [OPTIONS] COMMAND [ARGS]...
    $
    $ IMX Image Manager, ver.: 0.0.1
    $
    $ Options:
    $  -v, --version  Show the version and exit.
    $  -?, --help     Show this message and exit.
    $
    $ Commands:
    $  info     List image content
    $  create   Create new image from attached files
    $  extract  Extract image content
```

## Commands

#### $ imxim info

Print the IMX image content in readable format

##### Example:

```sh
$ imxim info u-boot.imx

############################################################
# IVT (Image Vector Table)
############################################################

 IVT: 0x877FF400
 BDT: 0x877FF420
 DCD: 0x877FF42C
 IMG: 0x87800000
 CSF: 0x87858000

############################################################
# BDT (Boot Data Table)
############################################################

 Start:  0x877FF800
 Length: 380928 Bytes
 Plugin: 0x00000000

############################################################
# DCD (Device Config Data)
############################################################

------------------------------------------------------------
Write Data Command (Ops: WRITE_VALUE, Bytes: 4)
------------------------------------------------------------
- ADDR: 0x30340004, VAL: 0x4F400005
- ADDR: 0x30391000, VAL: 0x00000002
- ADDR: 0x307A0000, VAL: 0x01040001
- ADDR: 0x307A01A0, VAL: 0x80400003
- ADDR: 0x307A01A4, VAL: 0x00100020
- ADDR: 0x307A01A8, VAL: 0x80100004
- ...
```

#### $ imxim extract [OPTIONS] FILE

Extract the IMX image content into a directory "file_name.ex"

##### options:
* **-t, --type** - Image storage type: nand, spi or sd (default: sd)
* **-?, --help** - Show help message and exit

##### Example:

```sh
$ imxim extract u-boot.imx

Image successfully extracted into dir: u-boot.imx.ex
```

#### $ imxim create [OPTIONS] ADDRESS INFILE OUTFILE

Create new IMX image from attached raw u-boot image and DCD and/or CSF

##### options:
* **-d, --dcd** - DCD File
* **-c, --csf** - CSF File
* **-t, --type** - Image storage type: nand, spi or sd (default: sd)
* **-?, --help** - Show help message and exit

##### Example:

```sh
$ imxim create ...

```