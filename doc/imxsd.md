i.MX Serial Downloader
=====================

The `imxsd` is a tool to download and execute code on [i.MX](http://www.nxp.com/products/microcontrollers-and-processors/arm-processors/i.mx-applications-processors)
and Vybrid SoCs through the Serial Download Protocol (SDP). It also demonstrate the usage of `imx.sdp` module.

> For running `imxsd` tool without root privileges in Linux OS copy attached udev rules
[90-imx-sdp.rules](https://github.com/molejar/pyIMX/blob/master/udev/90-imx-sdp.rules)
into `/etc/udev/rules.d` directory and reload it with command: `sudo udevadm control --reload-rules`.

Usage
-----

For printing a general info of usage this tool execute `imxsd -?`.

```sh
 $ imxsd -?
 Usage: imxsd [OPTIONS] COMMAND [ARGS]...

   i.MX Serial Downloader, ver.: 0.1.0 Beta

   NOTE: Development version, be carefully with it usage !

 Options:
   -t, --target TEXT          Select target MX6SX, MX6UL, ... [optional]
   -d, --debug INTEGER RANGE  Debug level (0-off, 1-info, 2-debug)
   -v, --version              Show the version and exit.
   -?, --help                 Show this message and exit.

 Commands:
   info  Read i.MX device info
   jump  Jump to specified address and RUN
   read  Read raw data from i.MX memory
   rreg  Read value from i.MX register
   stat  Read status of i.MX device
   wcsf  Write CSF file into i.MX device
   wdcd  Write DCD blob into i.MX device
   wimg  Write image into i.MX device and RUN it
   wreg  Write value into i.MX register
```

##### generic options:
* **-t, --target** - Select specific target by chip name or directly put "VID:PID" number of the target  
* **-d, --debug** - Debug level (0-off, 1-info, 2-debug)

## Commands

#### $ imxsd info

Read detailed information's about the SoC and HAB Log from connected i.MX/Vybrid device

##### Example (IMX7D):

```sh
 $ imxsd info

 DEVICE: SE Blank ULT1 (0x15A2, 0x0076)

 ---------------------------------------------------------
 Connected Device Info
 ---------------------------------------------------------

 Device:        iMX7 Solo/Dual
 Silicon Rev:   1.2

 iROM Release:  01.00.05
 iROM Version:  0x11

 WDOG State:    Disabled

 SBMR1: 0x00000000
   BOOT_CFG_1  = 0x00
   BOOT_CFG_2  = 0x00
   BOOT_CFG_3  = 0x00
   BOOT_CFG_4  = 0x00

 SBMR2: 0x08000001
   BMOD        = 00	Boot from Fuses
   BT_FUSE_SEL = 0
   DIR_BT_DIS  = 0
   SEC_CONFIG  = 01

 PersistReg Val: 0x00000000
 ANALOG DIGPROG: 0x00720012

 HAB Log Info --------------------------------------------

 00. (0x10000000) -> BOOTMODE - Internal Fuse
 01. (0x22000000) -> Security Mode - Open
 02. (0x30000000) -> DIR_BT_DIS = 0
 03. (0x40000000) -> BT_FUSE_SEL = 0
 04. (0x73000000) -> MFG Mode USDHC
 05. (0x80000000) -> Device INIT Call
 06. (0x0000006B) -> Tick: 0x0000006B
 07. (0x8F040000) -> Device INIT Fail
                     Error Code: 0x040000
 08. (0x0000006B) -> Tick: 0x0000006B
 09. (0xD0000000) -> Serial Downloader Entry

 ---------------------------------------------------------
```

<br>

#### $ imxsd rreg [OPTIONS] ADDRESS

Read value of register or memory at specified address from connected i.MX/Vybrid device.

> The address value must be aligned to selected access size !

##### options:
* **-c, --count** - Count of registers from specified address (default: 1)
* **-s, --size** - Access size: 8, 16 or 32 (default: 32)
* **-f, --format** - Value print format: b) binary, d) dec, x) hex (default: x)
* **-?, --help** - Show help message and exit

##### Example (IMX7D):

```sh
 $ imxsd rreg 0x800000

 DEVICE: SE Blank ULT1 (0x15A2, 0x0076)

 REG32[0x00800000] = 0x441DE4DA
```

<br>

#### $ imxsd wreg [OPTIONS] ADDRESS VALUE

Write value into register or memory at specified address in connected i.MX/Vybrid device.

> The address value must be aligned to selected access size !

##### options:
* **-s, --size** - Access size: 8, 16 or 32 (default: 32)
* **-b, --bytes** - Count of Bytes (default: 4)
* **-?, --help** - Show help message and exit

##### Example (IMX7D):

```sh
 $ imxsd wreg 0x900000 0x55555555

 DEVICE: SE Blank ULT1 (0x15A2, 0x0076)

 - Done
```

<br>

#### $ imxsd read [OPTIONS] ADDRESS LENGTH

Read raw data from a specified address in connected i.MX/Vybrid device.

> The address value must be aligned to selected access size !

##### options:
* **-s, --size** - Access size: 8, 16 or 32 (default: 32)
* **-c, --compress** - Compress hexdump output
* **-f, --file** - Output file name with extension: *.srec, *.s19, *.ihex or *.bin
* **-?, --help** - Show help message and exit

##### Example (IMX7D):

```sh
 $ imxsd read 0x900000 200

  DEVICE: SE Blank ULT1 (0x15A2, 0x0076)

   ADDRESS | 00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F | 0123456789ABCDEF
  -----------------------------------------------------------------------------
  00900000 | 55 55 55 55 75 43 05 68 05 28 92 0C 01 A0 00 02 | UUUUuC.h.(......
  00900010 | 92 EF CF 63 FA 68 02 04 7F 7F 67 BF A7 33 53 DD | ...c.h....g..3S.
  00900020 | B4 90 87 3B E9 D4 BA FE 40 04 48 02 BB AE 76 C4 | ...;....@.H...v.
  00900030 | 30 45 C8 80 AA 09 64 B2 66 8D FC E7 B9 5D 5E ED | 0E....d.f....]^.
  00900040 | EF F1 D5 BD 6C 39 68 DB 68 BC 6C 05 30 15 80 01 | ....l9h.h.l.0...
  00900050 | 62 A3 30 95 15 89 8F 41 AE DD FF CF 9E 7D 3A AE | b.0....A.....}:.
  00900060 | F5 CB 2F D8 BD E7 C1 F7 04 04 10 00 FB 8B 84 AB | ../.............
  00900070 | 03 0A 04 44 97 63 08 93 15 CC B7 A5 6F DE F7 9D | ...D.c......o...
  00900080 | 2B 9B F7 57 42 2A FF 15 E6 CB 9E 7D 03 04 00 60 | +..WB*.....}...`
  00900090 | 65 10 00 C3 84 44 20 50 DF AA 35 7A A6 7D 1B E3 | e....D P..5z.}..
  009000A0 | 12 43 85 58 73 C6 03 A5 10 0C 01 00 9D 1F 64 2C | .C.Xs.........d,
  009000B0 | 8C 92 00 A4 4D 41 58 5B 40 AB 43 B3 4F 6F AF FF | ....MAX[@.C.Oo..
  009000C0 | FD F3 EF 3E F7 E9 64 73                         | ...>..ds
  -----------------------------------------------------------------------------
```

<br>

#### $ imxsd wimg [OPTIONS] FILE

Write image file into connected device. Supported extensions: *.imx, *.ihex, *.srec, *.s19 or *.bin

##### options:
* **-a, --addr** - Start address (required for *.bin file)
* **-o, --offset** - Offset of input data (default: 0)
* **-m, --ocram** - OCRAM address, required for DDR init
* **-i, --init** - Init DDR from *.imx image
* **-r, --run** - Run loaded *.imx image
* **-s, --skipdcd** - Skip DCD Header from *.imx image
* **-?, --help** - Show help message and exit

##### Example (IMX7D):

```sh
 $ imxsd wimg -s -r -i -m 0x910000 u-boot.imx

 DEVICE: SE Blank ULT1 (0x15A2, 0x0076)

 - Init DDR
 - Writing u-boot.imx, please wait !
 - Skip DCD content
 - Jump to ADDR: 0x877FF400 and RUN
 - Done
```

<br>

#### $ imxsd wdcd [OPTIONS] ADDRESS FILE

Write Device Configuration Data (DCD) as raw image *.bin or will extract it from *.imx image

##### options:
* **-o, --offset** - Offset of input data for raw image (default: 0)
* **-?, --help** - Show help message and exit

##### Example (IMX7D):

```sh
 $ imxsd wdcd 0x910000 u-boot.imx

 DEVICE: SE Blank ULT1 (0x15A2, 0x0076)

 - Writing DCD from u-boot.imx, please wait !
 - Done
```

<br>

#### $ imxsd wcsf [OPTIONS] ADDRESS FILE

Write Code Signing File (CSF) as raw image *.bin or will extract it from *.imx image

##### options:
* **-o, --offset** - Offset of input data for raw image (default: 0)
* **-?, --help** - Show help message and exit

##### Example (IMX7D):

```sh
 $ imxsd wcsf 0x910000 u-boot.imx

 DEVICE: SE Blank ULT1 (0x15A2, 0x0076)

 - Writing CSF from u-boot.imx, please wait !
 - Done
```

<br>

#### $ imxsd jump [OPTIONS] ADDRESS

Jump to specified address and RUN

##### options:
* **-?, --help** - Show help message and exit

##### Example (IMX7D):

```sh
 $ imxsd jump 0x877FF400

 DEVICE: SE Blank ULT1 (0x15A2, 0x0076)

 - Jump to ADDR: 0x877FF400 and RUN
```

<br>

#### $ imxsd stat [OPTIONS]

Read status value

##### options:
* **-?, --help** - Show help message and exit

##### Example (IMX7D):

```sh
 $ imxsd stat

 DEVICE: SE Blank ULT1 (0x15A2, 0x0076)

 - Status: 0xF0F0F0F0
```