IMX Smart-Boot
==============

The `imxsb` is a tool for managed boot of embedded devices based on IMX application processors. It fully replaces the [imx_loader](https://github.com/boundarydevices/imx_usb_loader) and adding aditional features for easy modification or fixation of IMX DCD, U-Boot Enviroment Variables and Device Tree data.

Usage
-----

For printing a general info of usage this tool execute `imxsb -?`.

```sh
Usage: imxsb [OPTIONS] FILE COMMAND [ARGS]...

  IMX Smart Boot, ver.: 0.0.3 Beta

Options:
  -v, --version  Show the version and exit.
  -?, --help     Show this message and exit.

Commands:
  info  Get list of all boot options
  run   Run selected boot script
```

## Commands

#### $ imxsb FILE info

> The first argument `FILE` is the boot description file with extension `*.smx`.

This command print a list of all boot options from attached SMX file.

##### Example:

```sh
 $ imxsb imx7d.smx info

 0) InitRAMFS Boot (Boot from RAMDisk image)
 1) Network Boot 0 (Mount RootFS via NFS)
 2) Network Boot 1 (Load kernel and DTB over TFTP and mount RootFS via NFS)

```

<br>

#### $ imxsb FILE run [boot option]

> The first argument `FILE` is the boot description file with extension `*.smx`.

This command execute boot process via selected boot option from attached SMX file.

##### Example:

```sh
 $ imxsb imx7d.smx run

 0) InitRAMFS Boot (Boot from RAMDisk image)
 1) Network Boot 0 (Mount RootFS via NFS)
 2) Network Boot 1 (Load kernel and DTB over TFTP and mount RootFS via NFS)

 Run: 0

 1/7) Write Device Configuration Data
 2/7) Write U-Boot Image (imx7d_sbd/u-boot.imx)
 3/7) Skip DCD Segment in IMX image
 4/7) Write Kernel Image (imx7d_sbd/zImage)
 5/7) Write Device Tree Blob (imx7d_sbd/imx7d-sdb.dtb)
 6/7) Write RAMDisk Image (initramfs.bin)
 7/7) Start Boot ...
```

## SMX File

The SMX file is a standard text file which collect all information's about IMX boot process: paths to images, DCD data, global variables, boot scripts and etc.
Thanks to YAML syntax is human-readable and easy modifiable. Comments in SMX file start with the hash character `#` and extend to the end of the physical line.
A comment may appear at the start of a line or following whitespace characters. The content of SMX file is split into four sections: `HEAD`, `VARS`, `DATA` and `BODY`.

#### HEAD Section:

This section contains the base information's about target device.

* **NAME** - The name of target device or developing board (optional)
* **DESC** - The description of target device or developing board (optional)
* **CHIP** - Embedded IMX processor mark: VYBRID, MX6DQP, MX6SDL, MX6SL, MX6SX, MX6UL, MX6ULL, MX6SLL, MX7SD, MX7ULP (required)

>Instead of processor mark we can use directly USB VID:PID of the device in string format: "0x15A2:0x0054". Useful for a new device which is not in list of supported devices.

Example of head section:

```
HEAD:
    NAME: MCIMX7SABRE
    DESC: Development Board Sabre SD for IMX7D
    CHIP: MX7SD
```


#### VARS Section:

Collects all variables used in `DATA` and `BODY` section. 

The syntax for defining a variable is following:

```
VARS:
    #   <name>: <value>
    OCRAM_ADDR: '0x00910000'
```

The syntax for using a variable in `DATA` or `BODY` section is following:

```
DATA:
    DCD_TXT:
        DESC: Device Configuration Data
        ADDR: "{{ OCRAM_ADDR }}"
        TYPE: DCD
        FILE: imx7d_sbd/dcd_micron_1gb.txt
```

#### DATA Section:

Collects all data and paths to images used in scripts from `BODY` section.

Attributes used in all data segments:

* **DESC** - The description of data segment (optional)
* **ADDR** - The absolute address inside SoC OCT or DDR memory (optional)
* **TYPE** - The data type (optional)
* **DATA or FILE** - The data itself or path to image (required)

Optional attributes for IMX boot image and U-Boot raw image only:

* **MODE** - Environment variables insert mode: disabled, merge or replace (optional)
* **MARK** - Environment variables start mark in u-boot image (default: 'bootdelay=')
* **EVAL** - Environment variables itself

Supported data types:

* **IMX** - IMX boot image (*.imx)
* **DCD** - Device configuration data
* **FDT** - Flattened device tree data (*.dtb, *.dts)
* **UFW** - U-Boot firmware image (*.bin)
* **UST** - U-Boot script
* **BIN** - Binary data (used as default type if not specified)

Example of data segment:

```
DATA:
    UBOOT_IMX_FILE:
        DESC: U-Boot Image
        TYPE: IMX
        FILE: imx7d/u-boot.imx
        # Environment variables insert mode (disabled, merge or replace)
        MODE: merge
        # Environment variables start mark in u-boot image
        MARK: bootcmd=
        # Environment variables
        EVAL: |
            bootdelay = 0
            bootcmd = echo Running bootscript ...; source 0x83100000
```

#### BODY Section:

Collects all boot options as small scripts based on following commands:

* **WREG** *BYTES ADDRESS VALUE* - Write specified value into register at specified address.
* **WDCD** *DCD_DATA [ADDRESS]* - Write device configuration data into target device OC memory.
* **WIMG** *IMG_DATA [ADDRESS]* - Write image into target device OC or DDR memory
* **SDCD** - Skip DCD content from loaded U-Boot image.
* **JRUN** *ADDRESS or IMX_IMAGE* - Jump to specified address and run.

Description of arguments

* *BYTES* - The size of access into memory cell or register. Supported are three options: 1, 2 and 4 bytes.
* *ADDRESS* - The absolute address off memory cell or register inside SoC linear address space.
* *VALUE* - The value number in supported format (HEX, BIN, DEC or OCTA).
* *DCD_DATA* - The name of DCD segment from DATA section.
* *IMG_DATA* - The name of IMAGE segment from DATA section.

Example of boot script:

```
BODY:
    - NAME: InitRAMFS Boot
      DESC: Boot into MFG RAMDisk
      CMDS: |
        # Init DDR
        WDCD DCD_TXT
        # Load U-Boot Image
        WIMG UBOOT_IMX_FILE
        # Skip DCD Segment from loaded U-Boot image
        SDCD
        # Load Kernel Image
        WIMG KERNEL_IMAGE
        # Load Device Tree Blob
        WIMG KERNEL_DTB_FILE
        # Load RAMDisk Image
        WIMG INITRAMFS_IMG
        # Start Boot
        JRUN UBOOT_IMX_FILE
```

Here is an example of complete IMX Smart-Boot description file: [example.smx](example.smx)
