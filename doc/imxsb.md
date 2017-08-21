IMX Smart Boot
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
  info  Get data file info
  run   Start Controlled Boot
```

## Commands

#### $ imxsb FILE info

Print a collection of all boot options from config file.

##### Example:

```sh
 $ imxsb imx7d.smx info

 ...
```

<br>

#### $ imxsb FILE run [option index]

Start boot process via selected option.

##### Example:

```sh
 $ imxsb imx7d.smx run 0

 ...
```

## SMX file

TBD