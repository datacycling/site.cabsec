.PHONY: help clean lint format test pre-commit test  flow export

name := site.cabsec

install_stamp := .install.stamp
poetry := $(shell command -v poetry 2> /dev/null)
npm := $(shell command -v npm 2> /dev/null)

import_packages := orgpedia_cabsec
sources := flow/genSite_/src flow/genSVG_/src 

.DEFAULT_GOAL := help


help:
	@echo "Please use 'make <target>' where <target> is one of"
	@echo ""
	@echo "  install     install packages and prepare software environment"
	@echo ""
	@echo "  import      import data required for processing data flow"
	@echo "  flow        execute the tasks in the data flow"
	@echo "  export      export the data generated by the data flow"
	@echo ""
	@echo "  clean       remove all temporary files"
	@echo "  lint        run the code linters"
	@echo "  format      reformat code"
	@echo "  test        run all the tests"
	@echo ""
	@echo "Check the Makefile to know exactly what each target is doing."

install: $(install_stamp)
$(install_stamp): pyproject.toml poetry.lock package-lock.json
	@if [ -z $(poetry) ]; then echo "Poetry not found. See https://python-poetry.org/docs/"; exit 2; fi
	@if [ -z $(npm) ]; then echo "Node not found. See https://nodejs.org/en/"; exit 2; fi

	$(poetry) install
	$(npm) ci
	touch $(install_stamp)

import: $(data_packages)
	$(poetry) run python -m op import -d import $(data_packages)

flow:
	cd flow/genSite_ && make;
	cd flow/genSVG_ && make;

export:
	$(poetry) run python -m op exportSite -d export flow/genSite_


check:
	$(poetry) run python -m op checkSite export



clean:
	find . -type d -name "__pycache__" | xargs rm -rf {};
	rm -rf $(install_stamp) .coverage .mypy_cache


lint: $(install_stamp)
	$(poetry) run isort $(sources)
	$(poetry) run black $(sources)
	$(poetry) run flake8 $(sources)


format: $(install_stamp)
	$(poetry) run isort $(sources)
	$(poetry) run black $(sources)


test: $(install_stamp)
	$(poetry) run pytest 
