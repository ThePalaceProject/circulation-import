HONY: config install lint mypy full-lint test build publish clean all ci
.DEFAULT_GOAL := all

all: install lint mypy test build
ci: all

VIRTUAL_ENV = .venv
BIN = .venv/bin/
POETRY_VERSION = 1.0.10
PIP_VERSION = 20.2.2

PROJECT = circulation-import
PACKAGE = circulation_import
TAG ?= latest
DEV ?= 1

config:
	${BIN}poetry config virtualenvs.in-project true
	${BIN}poetry config repositories.pypi "${PYPI_URL}"
	${BIN}poetry config virtualenvs.create `if [ "${DEV}" = "0" ]; then echo false; else echo true; fi`
	mkdir -p ~/.config/pypoetry/ | true
	echo "[http-basic]" > ~/.config/pypoetry/auth.toml
	echo "[http-basic.pypi]" >> ~/.config/pypoetry/auth.toml
	echo "username = \"${PYPI_USER}\"" >> ~/.config/pypoetry/auth.toml
	echo "password = \"${PYPI_PASSWORD}\"" >> ~/.config/pypoetry/auth.toml

prepare:
	if [ "${DEV}" = "1" ]; then virtualenv ${VIRTUAL_ENV}; fi
	python3 -m pip install pip==${PIP_VERSION}
	python3 -m pip install poetry==${POETRY_VERSION}

install:
	make prepare
	make config
	${BIN}poetry install -v `if [ "${DEV}" = "0" ]; then echo "--no-dev --no-interaction --no-ansi"; fi`

lint:
	${BIN}isort src tests
	${BIN}flake8 --max-line-length=140 src tests

mypy:
	${BIN}mypy src tests || true

full-lint:
	make lint
	${BIN}pylint src tests || poetry run pylint-exit $$?
	make mypy

test:
	${BIN}nosetests -v --with-timer --with-coverage tests --cover-package $(PACKAGE)

build:
	${BIN}poetry build

publish:
	make prepare
	make config
	${BIN}poetry publish --build -r pypi

clean:
	rm -rf build dist
