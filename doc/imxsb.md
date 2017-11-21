i.MX Smart-Boot
==============

The `imxsb` is a tool for managed boot of embedded devices based on i.MX application processors. It fully replaces the 
[imx_loader](https://github.com/boundarydevices/imx_usb_loader) and adds features for an easy modification of binary 
sections in boot images like: 

* i.MX Device Configuration Data
* U-Boot Environment Variables
* Device Tree Data (not ready yet)

Later will be added support for on the fly sign and encryption of loaded boot images. 

Usage
-----

For printing a general info of usage this tool execute `imxsb -?`.

```sh
Usage: imxsb [OPTIONS] FILE COMMAND [ARGS]...

  IMX Smart Boot, ver.: 0.0.4 Beta

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

The SMX file is a standard text file which collect all information's about i.MX boot process: paths to images, DCD data, 
global variables, boot scripts and etc. Thanks to YAML syntax is human-readable and easy modifiable. Comments in SMX file 
start with the hash character `#` and extend to the end of the physical line. A comment may appear at the start of a line 
or following whitespace characters. The content of SMX file is split into four sections: `HEAD`, `VARS`, `DATA` and `BODY`.

#### HEAD Section:

This section contains the base information's about target device.

* **NAME** - The name of target device or developing board (optional)
* **DESC** - The description of target device or developing board (optional)
* **CHIP** - Embedded IMX processor mark: VYBRID, MX6DQP, MX6SDL, MX6SL, MX6SX, MX6UL, MX6ULL, MX6SLL, MX7SD, MX7ULP (required)

>Instead of processor mark can be used USB VID:PID of the device in string format: "0x15A2:0x0054". Useful for a new 
device which is not in list of supported devices.

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

Collects all data segments which can be loaded into the target via scripts in `BODY` section. Individual data segments 
can contain a different kind of data what specified the attribute `TYPE`. Supported are following data types:

* **DCD** - Device configuration data
* **FDT** - Flattened device tree data (*.dtb, *.dts)
* **IMX** - IMX boot image (*.imx)
* **URI** - U-Boot raw image (*.img, *.bin)
* **UEI** - U-Boot executable image (script, firmware, ...)
* **BIN** - Binary image or data (*.*)

If attribute `TYPE` is not defined the data segment will be processing as binary data (`TYPE: BIN`). Other attributes 
common for all data segments are:

* **DESC** - The description of data segment (optional)
* **ADDR** - The absolute address inside SoC OCT or DDR memory (optional)
* **DATA or FILE** - The data itself or path to image (required)

>Attribute `ADDR` is optional because can be specified as second argument in the command from `BODY` section. The address
value must be defined in some of this two places. If is defined on both then the value from the command will be taken. 


##### Device configuration data segment (DCD)

This data segment contains a data which generally initialize the SoC periphery for DDR memory. More details about DCD 
are in reference manual of selected IMX device. The data itself can be specified as binary file or text string/file. The 
text format of DCD data is described here: [imxim](imxim.md)

Example of *DCD* data segment in binary and text format:

```
DATA:
    DCD_BIN:
        DESC: Device Configuration Data
        ADDR: 0x00910000
        TYPE: DCD
        FILE: imx7d/dcd.bin
            
    DCD_TXT:
        DESC: Device Configuration Data
        ADDR: 0x00910000
        TYPE: DCD
        DATA: |
            # DDR init
            WriteValue    4 0x30340004 0x4F400005
            WriteValue    4 0x30391000 0x00000002
            WriteValue    4 0x307A0000 0x01040001
            ...
```

##### Flattened device tree data segment (FDT)

>Not implemented yet

##### IMX boot image data segment (IMX)

This data segment represent a complete boot image for IMX device which at least consist of DCD and URI images. The data
for it can be specified as path to a standalone file or can be created from others segments. 

Optional attributes for IMX data segment based on standalone file (U-Boot IMX image):

* **MODE** - Environment variables insert mode: disabled, merge or replace (optional)
* **MARK** - Environment variables start mark in u-boot image (default: 'bootdelay=')
* **EVAL** - Environment variables itself

Example of *IMX* data segment:

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
            
    UBOOT_IMX:
        NAME: U-Boot Image
        TYPE: IMX
        DATA:
            STADDR: 0x877FF000
            OFFSET: 0x400
            DCDSEG: DCD_TXT
            APPSEG: UBOOT_RAW_FILE
```

>Included data segments must be defined before IMX data segment.

##### U-Boot raw image data segment (URI)

This data segment cover a raw U-Boot image without IVT, DCD and other parts which are included in IMX image. Therefore 
it can not be loaded into target directly but can be used for creation of IMX data segment. 

Optional attributes:

* **MODE** - Environment variables insert mode: disabled, merge or replace (optional)
* **MARK** - Environment variables start mark in u-boot image (default: 'bootdelay=')
* **EVAL** - Environment variables itself

Example of *URI* data segment:

```
DATA:
    UBOOT_RAW_FILE:
        DESC: U-Boot Raw Image
        TYPE: URI
        FILE: imx7d/u-boot.img
        # Environment variables insert mode (disabled, merge or replace)
        MODE: merge
        # Environment variables start mark in u-boot image
        MARK: bootcmd=
        # Environment variables
        EVAL: |
            bootdelay = 0
            bootcmd = echo Running bootscript ...; source 0x83100000
```

##### U-Boot executable image data segment (UEI)

This data segment cover a data which can be executed from U-Boot environment. Format of input data depends on image type
which is defined by `HEAD` attribute.

All HEAD attributes:

* **IMAGE_NAME** - Image name in 32 chars (default: "-")
* **IMAGE_TYPE** - Image type: "sdt", "firmware", "script", "multi" (default: "firmware")
* **ENTRY_ADDR** - Entry address value (default: 0x00000000)
* **LOAD_ADDR**  - Load address value (default: 0x00000000)
* **ARCH_TYPE**  - Architecture type: "alpha", "arm", "x86", ... (default: "arm")
* **OS_TYPE**    - OS type: "openbsd", "netbsd", "freebsd", "bsd4", "linux", ... (default: "linux")
* **COMPRESS**   - Compression type: "none", "gzip", "bzip2", "lzma", "lzo", "lz4" (default: "none")

Example of *UEI* data segment:

```
DATA:      
    UBOOT_FIRMWARE:
        DESC: U-Boot FW
        ADDR: 0x83100000
        TYPE: UEI
        FILE: imx7d/u-boot.bin
                 
    UBOOT_SCRIPT:
        DESC: NetBoot Script
        ADDR: 0x83100000
        TYPE: UEI
        HEAD:
            IMAGE_TYPE: script
        DATA: |
            echo '>> Network Boot ...'
            setenv autoload 'no'
            dhcp
            ...
```

##### Binary image data segment (BIN)

This data segment is covering all images which are loaded into target as binary blob, like: kernel, initramfs, ...

Example of *BIN* data segment:

```
DATA:
    KERNEL_IMAGE:
        DESC: Kernel Image
        ADDR: 0x80800000
        FILE: imx7d/zImage
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
