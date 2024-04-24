all: help

.PHONY: help # Show this help
help:
	@echo "List of Makefile targets:"
	@grep '^.PHONY: .* #' Makefile | sed 's/\.PHONY: \(.*\) # \(.*\)/\1	\2/' | expand -t20

.PHONY: requirements # Install requirements
requirements:
	venv/bin/pip3 install .

.PHONY: requirements-dev # Install requirements-dev
requirements-dev:
	venv/bin/pip3 install .[dev]

.PHONY: show # Show current installed version
show:
	venv/bin/pip3 show pysolarmanv5

.PHONY: black # Run black
black:
	venv/bin/python3 -m black pysolarmanv5/*.py utils/*.py

.PHONY: lint # Run lint
lint:
	venv/bin/python3 -m pylint **/*.py || true

.PHONY: test # Run pytest
test:
	venv/bin/pytest

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

.PHONY: docs-requirements # Install docs requirements
docs-requirements: docs/requirements.txt
	venv/bin/pip3 install -r docs/requirements.txt

.PHONY: docs # Build docs
docs:	clean-docs
	venv/bin/sphinx-build docs docs/_build

.PHONY: docs-livehtml # Build docs and serve
docs-livehtml:
	venv/bin/sphinx-autobuild --open-browser docs docs/_build --watch pysolarmanv5/

.PHONY: build # Build
build: clean-build
	venv/bin/python3 -m build

.PHONY: install-dev # Install in editable mode
install-dev:
	venv/bin/python3 -m pip install -e .

.PHONY: install # Install
install:
	venv/bin/python3 -m pip install .

.PHONY: upload # Upload to PyPI
upload:
	venv/bin/python3 -m twine upload dist/*

.PHONY: venv-create # Create venv in venv/
venv-create:
	python3 -m venv venv

.PHONY: venv-shell # Launch venv Python shell
venv-shell:
	venv/bin/python3
