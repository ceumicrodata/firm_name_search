## Install

Building most probably requires a linux box, the generated file will run on all platforms with python2.

```
make build
```

Copy the generated `name-to-taxids-YYYY-MM-DD.pyz` to wherever you want, this file is the program file.
Note that for running the tool you will also need a database.
That database is not included, it is licensed to us.

## Usage

```
python name-to-taxids-YYYY-MM-DD.pyz "firm name" input.csv output.csv
```

where "firm name" is the csv header for firm name in `input.csv`.

----

If you are curious how the `.pyz` file works, see https://www.python.org/dev/peps/pep-0441/ and its links.
