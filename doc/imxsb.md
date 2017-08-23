IMX Smart-Boot
==============

The `imxsb` is a tool for managed boot of embedded devices based on IMX application processors.

Usage
-----

For printing a general info of usage this tool execute `imxsb -?`.

```sh
Usage: imxsb [OPTIONS] FILE COMMAND [ARGS]...

  IMX Smart Boot, ver.: 0.0.2 Beta

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

 ...
```

<br>

#### $ imxsb FILE run [boot option]

> The first argument `FILE` is the boot description file with extension `*.smx`.

This command execute boot process via selected boot option from attached SMX file.

##### Example:

```sh
 $ imxsb imx7d.smx run 0

 ...
```

## SMX File Description

The SMX file is collecting all the information's of IMX boot process in one place: paths to images, DCD data, global variables, boot scripts and etc.
Thanks to YAML syntax is human-readable and easy modifiable. The content of SMX file is split into four sections: `HEAD`, `VARS`, `DATA` and `BODY`.

> Comments in SMX file start with the hash character `#` and extend to the end of the physical line. A comment may appear at the start of a line or
following whitespace characters.

#### HEAD Section:

This section contains the base information's about target device.

* **NAME** - The name of arget device or developing board (optional)
* **DESC** - The description of target device or developing board (optional)
* **CHIP** - Embedded IMX processor mark: VYBRID, MX6DQP, MX6SDL, MX6SL, MX6SX, MX6UL, MX6ULL, MX6SLL, MX7SD (required)

Example of head section:

```
HEAD:
    NAME: MCIMX7SABRE
    DESC: Development Board Sabre SD for IMX7D
    CHIP: MX7SD
```


#### VARS Section:

Collects all variables used in `DATA` section. The syntax for defining a variable is following:

```
VARS:
    &<variable_name> <variable_value>
    ...
```

More details you can found in YAML documentation.


#### DATA Section:

Collects all data and paths to images used in scripts from `BODY` section.


#### BODY Section:

Collects all boot options as small scripts based on following commands:

* **WREG** *BYTES ADDRESS VALUE*
* **WDCD** *DCD_DATA [ADDRESS]*
* **WIMG** *IMG_DATA [ADDRESS]*
* **SDCD**
* **JRUN** *ADDRESS or IMX_IMAGE*

Description of arguments

* *BYTES* - The size of access into memory cell or register. Supported are three options: 1, 2 and 4 bytes.
* *ADDRESS* - The absolute address off memory cell or register inside SoC linear address space.
* *VALUE* - The value in supported format.
* *DCD_DATA* -
* *IMG_DATA* -
* *IMX_IMAGE* -

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
        #WIMG MFG_INITRAMFS
        # Start Boot
        JRUN UBOOT_IMX_FILE
```


## SMX File Example

```
HEAD:
  NAME: MCIMX7SABRE
  DESC: Development Board Sabre SD for IMX7D
  CHIP: MX7SD

VARS:
    &OCRAM_ADDR 0x00910000

DATA:
    DCD_TXT:
        DESC: Device Configuration Data
        ADDR: *OCRAM_ADDR
        TYPE: DCD
        DATA: |
            # DDR init
            WriteValue    4 0x30340004 0x4F400005
            WriteValue    4 0x30391000 0x00000002
            WriteValue    4 0x307A0000 0x01040001
            WriteValue    4 0x307A01A0 0x80400003
            WriteValue    4 0x307A01A4 0x00100020
            WriteValue    4 0x307A01A8 0x80100004
            WriteValue    4 0x307A0064 0x00400046
            WriteValue    4 0x307A0490 0x00000001
            WriteValue    4 0x307A00D0 0x00020083
            WriteValue    4 0x307A00D4 0x00690000
            WriteValue    4 0x307A00DC 0x09300004
            WriteValue    4 0x307A00E0 0x04080000
            WriteValue    4 0x307A00E4 0x00100004
            WriteValue    4 0x307A00F4 0x0000033F
            WriteValue    4 0x307A0100 0x09081109
            WriteValue    4 0x307A0104 0x0007020D
            WriteValue    4 0x307A0108 0x03040407
            WriteValue    4 0x307A010C 0x00002006
            WriteValue    4 0x307A0110 0x04020205
            WriteValue    4 0x307A0114 0x03030202
            WriteValue    4 0x307A0120 0x00000803
            WriteValue    4 0x307A0180 0x00800020
            WriteValue    4 0x307A0184 0x02000100
            WriteValue    4 0x307A0190 0x02098204
            WriteValue    4 0x307A0194 0x00030303
            WriteValue    4 0x307A0200 0x00000016
            WriteValue    4 0x307A0204 0x00171717
            WriteValue    4 0x307A0214 0x04040404
            WriteValue    4 0x307A0218 0x0F040404
            WriteValue    4 0x307A0240 0x06000604
            WriteValue    4 0x307A0244 0x00000001
            WriteValue    4 0x30391000 0x00000000
            WriteValue    4 0x30790000 0x17420F40
            WriteValue    4 0x30790004 0x10210100
            WriteValue    4 0x30790010 0x00060807
            WriteValue    4 0x307900B0 0x1010007E
            WriteValue    4 0x3079009C 0x00000D6E
            WriteValue    4 0x30790020 0x08080808
            WriteValue    4 0x30790030 0x08080808
            WriteValue    4 0x30790050 0x01000010
            WriteValue    4 0x30790050 0x00000010
            WriteValue    4 0x307900C0 0x0E407304
            WriteValue    4 0x307900C0 0x0E447304
            WriteValue    4 0x307900C0 0x0E447306
            CheckAnyClear 4 0x307900C4 0x00000001
            WriteValue    4 0x307900C0 0x0E447304
            WriteValue    4 0x307900C0 0x0E407304
            WriteValue    4 0x30384130 0x00000000
            WriteValue    4 0x30340020 0x00000178
            WriteValue    4 0x30384130 0x00000002
            WriteValue    4 0x30790018 0x0000000F
            CheckAnyClear 4 0x307A0004 0x00000001

    UBOOT_IMX_FILE:
        DESC: U-Boot Image
        TYPE: IMX
        FILE: imx7d/imx7d_u-boot.imx
        # Environment variables insert mode (disabled, merge or replace)
        MODE: merge
        # Environment variables start mark in u-boot image
        MARK: bootdelay=
        # Environment variables
        EVAL: |
            bootdelay = 9
            console = ttymxc1

    KERNEL_IMAGE:
        DESC: Kernel Image
        ADDR: 0x80800000
        FILE: imx7d/imx7d_zImage

    KERNEL_DTB_FILE:
        DESC: Device Tree Blob
        ADDR: 0x83000000
        FILE: imx7d/imx7d_sdb.dtb

    MFG_INITRAMFS:
        DESC: RAMDisk Image
        ADDR: 0x83800000
        FILE: initramfs.u-boot

    UBOOT_SCRIPT:
        DESC: U-Boot Script
        ADDR: 0x80800000
        TYPE: SCRIPT
        DATA: |
            echo '>> Run NetBoot Script ...'
            setenv autoload 'no'
            dhcp
            # ----------------------------------
            # configurable data
            # ----------------------------------
            setenv serverip 192.168.1.162
            setenv hostname 'imx7dsb'
            setenv netdev  'eth0'
            setenv nfsroot '/srv/nfs/imx7d'
            setenv imgfile '/imx7d/zImage'
            setenv fdtfile '/imx7d/imx7d-sdb.dtb'
            # ----------------------------------
            # chip specific data
            # ----------------------------------
            setenv fdtaddr 0x83000000
            setenv imgaddr 0x80800000
            # ----------------------------------
            # network boot scripts
            # ----------------------------------
            setenv imgload 'tftp ${imgaddr} ${imgfile}'
            setenv fdtload 'tftp ${fdtaddr} ${fdtfile}'
            setenv netargs 'setenv bootargs console=${console},${baudrate} root=/dev/nfs rw nfsroot=${serverip}:${nfsroot},v3,tcp ip=dhcp'
            setenv netboot 'echo Booting from net ...; run netargs; run imgload; run fdtload; bootz ${imgaddr} - ${fdtaddr};'
            # ----------------------------------
            # boot command
            # ----------------------------------
            run netboot

BODY:
    # Script 0
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
        #WIMG MFG_INITRAMFS
        # Start Boot
        JRUN UBOOT_IMX_FILE

    # Script 1
    - NAME: Network Boot 0
      DESC: Mount RootFS via NFS
      CMDS: |
        # Init DDR
        WDCD DCD_TXT
        # Load U-Boot Image
        WIMG UBOOT_IMX
        SDCD
        # Load U-Boot Script
        WIMG UBOOT_SCRIPT
        # Load Kernel Image
        WIMG KERNEL_IMAGE
        # Load Device Tree Blob
        WIMG KERNEL_DTB_FILE
        # Start Boot
        JRUN UBOOT_IMX_FILE

    # Script 2
    - NAME: Network Boot 1
      DESC: Load kernel and DTB over TFTP and mount RootFS via NFS
      CMDS: |
        # Init DDR
        WDCD DCD_TXT
        # Load U-Boot Image
        WIMG UBOOT_IMX
        SDCD
        # Load U-Boot Script
        WIMG UBOOT_SCRIPT
        # Start Boot
        JRUN UBOOT_IMX_FILE
```