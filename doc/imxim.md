IMX Image Manager
=================

The `imxim` is a tool to for manipulation with `*.imx` image.

Usage
-----

For printing a general info of usage this tool execute `imxim -?`.

```sh
 $ Usage: imxim [OPTIONS] COMMAND [ARGS]...

 IMX Image Manager, ver.: 0.0.1

 Options:
  -v, --version  Show the version and exit.
  -?, --help     Show this message and exit.

 Commands:
  info     List image content
  create   Create new image from attached files
  extract  Extract image content
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

 Start:  0x877FF000
 Length: 372736 Bytes
 Plugin: NO

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

<br>

#### $ imxim extract [OPTIONS] FILE

Extract the IMX image content into a directory "file_name.ex"

##### options:
* **-o, --offset** - IVT offset (default: 1024)
* **-f, --format** - DCD and CSF section output format: txt or bin (default: bin)
* **-?, --help**   - Show help message and exit

##### Example:

```sh
 $ imxim extract -f txt u-boot.imx

 Image successfully extracted
 Path: u-boot.imx.ex

```

<br>

#### $ imxim create [OPTIONS] ADDRESS DCDFILE APPFILE OUTFILE

Create new IMX image from attached files:

**ADDRESS** - Start address of image in target memory<br>
**DCDFILE** - DCD file in TXT or BIN format<br>
**APPFILE** - APP file (u-boot.bin or barebox.bin)<br>
**OUTFILE** - Output file name with extension *.imx<br>

##### options:
* **-c, --csf** - CSF file
* **-o, --offset** - IVT offset (default: 1024)
* **-p, --plugin** - Plugin image (default: False)
* **-?, --help** - Show help message and exit

##### Example:

```sh
 $ imxim create 0x877FF000 dcd.bin u-boot.bin u-boot.imx

 Image successfully created
 Path: u-boot.imx

```

## DCD File

#### Write Commands
* **WriteValue BYTES ADDRESS VALUE**
* **ClearBitMask BYTES ADDRESS VALUE**
* **SetBitMask BYTES ADDRESS VALUE**

#### Check Commands
* **CheckAllClear BYTES ADDRESS MASK [COUNT]**
* **CheckAllSet BYTES ADDRESS MASK [COUNT]**
* **CheckAnyClear BYTES ADDRESS MASK [COUNT]**
* **CheckAnySet BYTES ADDRESS MASK [COUNT]**

#### Other Commands
* **Nop**
* **Unlock ENGINE VALUE [VALUE]**