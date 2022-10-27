all: help

.PHONY: help # Show this help
help:
	@echo "List of Makefile targets:"
	@grep '^.PHONY: .* #' Makefile | sed 's/\.PHONY: \(.*\) # \(.*\)/\1	\2/' | expand -t20

.PHONY: requirements # Install requirements
requirements: requirements.txt
	pip3 install -r requirements.txt

.PHONY: show # Show current installed version
show:
	pip3 show pysolarmanv5

.PHONY: black # Run black
black:
	python3 -m black pysolarmanv5/*.py

.PHONY: lint # Run lint
lint:
	python3 -m pylint pysolarmanv5/*.py -d C0103 -d C0302 -d C0330 -d C0413 -d R0902 -d R0911 -d R0912 -d R0913 -d R0914 -d R0915 -d W0613 -d W0703 -d W0707 || true

.PHONY: clean # Clean
clean: clean-build clean-pyc clean-docs

.PHONY: clean-build # Clean build
clean-build:
	rm -rf build/
	rm -rf dist/
	rm -rf .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

.PHONY: clean-pyc # Clean pyc
clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

.PHONY: clean-docs # Clean docs
clean-docs:
	rm -rf docs/_build

.PHONY: docs # Build docs
docs:	clean-docs
	sphinx-build docs docs/_build

.PHONY: docs-livehtml # Build docs and serve
docs-livehtml:
	sphinx-autobuild --open-browser docs docs/_build --watch pysolarmanv5/

.PHONY: build # Build
build: clean-build
	python3 -m build

.PHONY: install-dev # Install in editable mode
install-dev:
	python3 -m pip install -e .

.PHONY: install # Install
install:
	python3 -m pip install .

.PHONY: upload # Upload to PyPI
upload:
	python3 -m twine upload dist/*
