i.MX Image Manager
=================

The `imxim` is a tool for manipulation with i.MX boot image (*.imx). 

Usage
-----

For printing a general info of usage this tool execute `imxim -?`.

```sh
Usage: imxim [OPTIONS] COMMAND [ARGS]...

  i.MX Boot Image Manager, ver.: 0.1.1 Beta

  NOTE: Development version, be carefully with it usage !

Options:
  -v, --version  Show the version and exit.
  -?, --help     Show this message and exit.

Commands:
  create    Create new i.MX6/7/8/RT boot image
  create2a  Create new i.MX6/7/RT boot image from attached files
  create2b  Create new i.MX8M boot image from attached files
  create3a  Create new i.MX8QXP boot image from attached files
  create3b  Create new i.MX8QM boot image from attached files
  srkgen    SRK Table and Fuses Generator
  dcdfc     DCD file converter (*.bin, *.txt)
  extract   Extract i.MX boot image content
  info      List i.MX boot image content
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
* **-t, --type** - Image type: auto, 67RT, 8M, 8QXP, 8QM (default: auto)
* **-e, --embedded** - Embed DCD into image description file (default: False)
* **-o, --offset** - Input file offset in bytes (default: 0)
* **-s, --step** - Parsing step in bytes (default: 256)
* **-?, --help**   - Show help message and exit

##### Example:

```sh
 $ imxim extract u-boot.imx

 Image successfully extracted
 Path: u-boot.imx.ex
```

<br>

#### $ imxim create [OPTIONS] INFILE OUTFILE

Create new i.MX6/7/8/RT boot image.

**INFILE** - The i.MX boot image description file (*.yml)<br>
**OUTFILE** - The name of created i.MX boot image (*.imx)<br>

##### options:
* **-?, --help** - Show help message and exit

##### Example of imx8qm-img.yml file:

```
# Device information's
TARGET:  mx8qm
PLUGIN:  yes
OFFSET:  0x400
ADDRESS: 0x80000
VERSION: 0x43

# Device Configuration Data
DCD:
  TYPE: TXT
  PATH: dcd.txt

# Collection of images
IMG:

  - TYPE: SCFW
    PATH: scfw.bin

  - TYPE: SCD
    PATH: scd.bin

  - TYPE: APP-A53
    ADDR: 0x10000000
    PATH: app_a53.bin

  - TYPE: CM4-0
    ADDR: 0x10000000
    PATH: app_cm4.bin
```

##### Example of usage:

```sh
 $ imxim create imx8qm-img.yml imx8qm-img.imx

 Image successfully created
 Path: imx8qm-img.imx
```

<br>

#### $ imxim create2a [OPTIONS] ADDRESS APPFILE OUTFILE

Create new i.MX6/7/RT boot image from attached files:

**ADDRESS** - Start address of image in target memory<br>
**APPFILE** - APP file (u-boot.bin or barebox.bin)<br>
**OUTFILE** - Output file name with extension *.imx<br>

##### options:
* **-d, --dcd** - DCD file (*.txt or *.bin)
* **-c, --csf** - CSF file (*.txt or *.bin)
* **-o, --offset** - IVT offset (default: 1024)
* **-v, --version** - Header Version (default: 0x41)
* **-p, --plugin** - Plugin Image if used
* **-?, --help** - Show help message and exit

##### Example:

```sh
 $ imxim create2a -d dcd.bin 0x877FF000 u-boot.bin u-boot.imx

 Image successfully created
 Path: u-boot.imx
```

<br>

#### $ imxim create2b [OPTIONS] ADDRESS APPFILE OUTFILE

Create new i.MX8M image from attached files:

> This command is not functional yet !


<br>

#### $ imxim create3a [OPTIONS] SCFW OUTFILE

Create new i.MX8QXP boot image from attached files:

**SCFW** - System Controller Firmware *.bin<br>
**OUTFILE** - Output file name with extension *.imx<br>

##### options:
* **-a, --app** - Application image "address|path;..."
* **-m, --cm4** - Cortex-M4 binary "address|core|path;...", core: 0/1
* **-d, --dcd** - DCD File (*.txt or *.bin)
* **-s, --scd** - SCD File (*.bin)
* **-c, --csf** - CSF File (*.txt or *.bin)
* **-o, --offset** - IVT offset (default: 1024)
* **-v, --version** - Header Version (default: 0x41)
* **-p, --plugin** - Plugin Image if used
* **-?, --help** - Show help message and exit

##### Example:

```sh
 $ imxim create3a scfw.bin scfw_8qxp.imx

 Image successfully created
 Path: scfw_8qxp.imx
```

<br>

#### $ imxim create3b [OPTIONS] SCFW OUTFILE

Create new i.MX8QM boot image from attached files:

**SCFW** - System Controller Firmware *.bin<br>
**OUTFILE** - Output file name with extension *.imx<br>

##### options:
* **-a, --app** - Application image "address|core|path;...", core: A53/A72
* **-m, --cm4** - Cortex-M4 binary "address|core|path;...", core: 0/1
* **-d, --dcd** - DCD File (*.txt or *.bin)
* **-s, --scd** - SCD File (*.bin)
* **-c, --csf** - CSF File (*.txt or *.bin)
* **-o, --offset** - IVT offset (default: 1024)
* **-v, --version** - Header Version (default: 0x41)
* **-?, --help** - Show help message and exit

##### Example:

```sh
 $ imxim create3b scfw.bin scfw_8qm.imx

 Image successfully created
 Path: scfw_8qm.imx
```

<br>

#### $ imxim srkgen [OPTIONS] [INFILES]

SRK Table and Fuses Generator.

**INFILES** - Input certificates with *.pem extension

##### options:
* **-t, --table** - Output file name of SRK table (default: srk_table.bin)
* **-f, --fuses** - Output file name of SRK fuses (default: srk_fuses.bin)
* **-v, --version** - HAB version (default: 0x40)
* **-?, --help** - Show help message and exit

##### Example:

```sh
 $ imxim srkgen -t srk_table.bin -f srk_fuses.bin SRK1_sha256_4096_65537_v3_ca_crt.pem 
 SRK2_sha256_4096_65537_v3_ca_crt.pem SRK3_sha256_4096_65537_v3_ca_crt.pem SRK4_sha256_4096_65537_v3_ca_crt.pem

 Generated successfully !
 SRK Table: srk_table.bin
 SRK Fuses: srk_fuses.bin
```

<br>

#### $ imxim dcdfc [OPTIONS] OUTFILE [INFILES]

Convert DCD binary blob (*.bin) into readable text file (*.txt) and vice versa.

**OUTFILE** - Output file name with extension *.bin or *.txt<br>
**INFILES** - Input file name with extension *.txt or *.bin<br>

>As input can be used more files which will be merged in one output file

##### options:
* **-o, --outfmt** - Output file format: txt or bin (default: bin)
* **-i, --infmt** - Input file format: txt or bin (default: txt)
* **-?, --help** - Show help message and exit

##### Example:

```sh
 $ imxim dcdfc -i bin -o txt dcd.txt dcd.bin

 Conversion was successful !
 Output: dcd.txt
```

<br>

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