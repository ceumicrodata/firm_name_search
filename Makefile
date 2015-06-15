.PHONY: clean test

clean:
	git clean -X -f
	rm -rf build build.zip

test: clean
	in-virtualenv python -m unittest discover -p '*test*.py'

build: clean
	pip install . -t build
	cp __main__.py build
	cd build; find -name \*.py | zip -@ ../build.zip
	(echo '#!/usr/bin/env python'; cat build.zip) > name-to-taxids.zip
	chmod +x name-to-taxids.zip
	mv name-to-taxids.zip name-to-taxids-`date +%Y%m%d`.pyz
