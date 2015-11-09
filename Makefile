.PHONY: clean test build

clean:
	doit clean -a

test: clean
	doit test

build:
	doit build
