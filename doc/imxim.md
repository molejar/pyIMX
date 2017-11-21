i.MX Image Manager
=================

The `imxim` is a tool to for manipulation with `*.imx` image.

Usage
-----

For printing a general info of usage this tool execute `imxim -?`.

```sh
 $ Usage: imxim [OPTIONS] COMMAND [ARGS]...

 IMX Image Manager, ver.: 0.0.4

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
**APPFILE** - APP file (u-boot.bin or barebox.bin)<br>
**OUTFILE** - Output file name with extension *.imx<br>

##### options:
* **-d, --dcd** - DCD file (*.txt or *.bin)
* **-c, --csf** - CSF file (*.txt or *.bin)
* **-o, --offset** - IVT offset (default: 1024)
* **-p, --plugin** - Plugin Image if used
* **-?, --help** - Show help message and exit

##### Example:

```sh
 $ imxim create -d dcd.bin 0x877FF000 u-boot.bin u-boot.imx

 Image successfully created
 Path: u-boot.imx

```

<br>

#### $ imxim dcdtxt [OPTIONS] INFILE OUTFILE

Convert DCD: BIN file to TXT file

**INFILE** - Input file name with extension *.bin<br>
**OUTFILE** - Output file name with extension *.txt<br>

##### options:
* **-?, --help** - Show help message and exit

##### Example:

```sh
 $ imxim dcdtxt dcd.bin dcd.txt

 DCD successfully converted
 Path: dcd.txt

```

<br>

#### $ imxim dcdbin [OPTIONS] INFILE OUTFILE

Convert DCD: TXT file to BIN file

**INFILE** - Input file name with extension *.txt<br>
**OUTFILE** - Output file name with extension *.bin<br>

##### options:
* **-v, --version** - DCD Version (default: 0x41)
* **-?, --help** - Show help message and exit

##### Example:

```sh
 $ imxim dcdbin -v 0x42 dcd.txt dcd.bin

 DCD successfully converted
 Path: dcd.bin

```


## DCD file

The segment with device configuration data (DCD) can be specified in readable text format with following syntax:

```
# Comment line must staring with '#'
command0 arg0 arg1 ...
command1 arg0 arg1 ...
...
# Long commands can be slit into more lines with '\' char
commandN arg0 arg1 arg2 \
arg3 arg4 arg5 arg6
```


#### Supported commands
* **WriteValue** *BYTES ADDRESS VALUE*
* **ClearBitMask** *BYTES ADDRESS MASK*
* **SetBitMask** *BYTES ADDRESS MASK*
* **CheckAllClear** *BYTES ADDRESS MASK [COUNT]*
* **CheckAllSet** *BYTES ADDRESS MASK [COUNT]*
* **CheckAnyClear** *BYTES ADDRESS MASK [COUNT]*
* **CheckAnySet** *BYTES ADDRESS MASK [COUNT]*
* **Unlock** *ENGINE [VALUE0, VALUE1, ...]*
* **Nop**

#### Description of arguments
* *BYTES* - The size of access into memory cell or register. Supported are three options: 1, 2 and 4 bytes.
* *ADDRESS* - The absolute address off memory cell or register inside SoC linear address space.
* *VALUE* - The value in supported format.
* *MASK* - The value of bit-mask.
* *COUNT* - The number of repeated checks. This argument is optional.
* *ENGINE* - The type of engine which will be unlocked in string format. Supported are this options: 'ANY', 'SCC', 'RTIC', 'SAHARA', 'CSU', 'SRTC', 'DCP', 'CAAM', 'SNVS', 'OCOTP', 'DTCP', 'ROM', 'HDCP', 'SW'

> Arguments: *ADDRESS*, *VALUE* and *MASK* can be specified in decimal (654...), binary (0b01101...) or hex (0x105...) format.

##### Example:
```
# IMX DCD Content
WriteValue 4 0x30340004 0x4F400005
WriteValue 4 0x30391000 0x00000002
WriteValue 4 0x307A0000 0x01040001
WriteValue 4 0x307A01A0 0x80400003
... 

CheckAnyClear 4 0x307900C4 0x00000001
... 

```