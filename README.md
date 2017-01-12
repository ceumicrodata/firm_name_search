## Build

Requirements:
- linux box (generates a version for windows as well!)
- [doit](http://pydoit.org/) (available as an Ubuntu package)

Run
```
doit build
```

which generates the files:
- `name-to-taxids-YYYY-MM-DD` for linux & mac
- `name-to-taxids-YYYY-MM-DD.cmd` for windows


## Install

Copy the generated `name-to-taxids-YYYY-MM-DD` file (`name-to-taxids-YYYY-MM-DD.cmd` version for windows) to somewhere on your PATH.


## Use

Requirements:
- Python2 and the tool must be available on the PATH
- a proprietary database index file (available only to members of CEU MicroData)

```
name-to-taxids-YYYY-MM-DD "firm name" input.csv output.csv
```

where "firm name" is the field name for firm name in `input.csv` and there is an index file in the current directory with name `complex_firms.sqlite`.

The tool provides command line help, so for further details run 

```
name-to-taxids-YYYY-MM-DD -h
```


## Use from Python programs

Put `git+https://github.com/ceumicrodata/firm_name_search.git` in the
`requirements.txt` file.

```python
from firm_name_search.name_to_taxid import FirmFinder

finder = FirmFinder(index_file_location)
for firm_name in ...:
    match = finder.find_firm(firm_name)
    # process match
```

`FirmFinder.find_firm()` expects a single unicode firm name parameter which it will resolve to a match object with at least these attributes:
- `org_score`
- `text_score`
- `found_name`
- `tax_id`

----

If you are curious how the tool works without explicitly calling python, see https://www.python.org/dev/peps/pep-0441/ and its links.
