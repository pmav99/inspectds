.PHONY: list

list:
	@LC_ALL=C $(MAKE) -pRrq -f $(lastword $(MAKEFILE_LIST)) : 2>/dev/null | awk -v RS= -F: '/^# File/,/^# Finished Make data base/ {if ($$1 !~ "^[#.]") {print $$1}}' | sort | grep -E -v -e '^[^[:alnum:]]' -e '^$@$$'

init:
	poetry install --with=dev -E all
	pre-commit install

style:
	pre-commit run black -a

lint:
	pre-commit run ruff -a

mypy:
	dmypy run inspectds

test:
	python -m pytest -vl --durations=10

deps:
	pre-commit run poetry-check -a
	pre-commit run poetry-export -a

conda_lock_ci:
	conda-lock lock --mamba --check-input-hash --platform linux-64 --platform osx-64 -f ci/py3.11.yml --lockfile ci/conda-lock-py3.11.yml
	conda-lock lock --mamba --check-input-hash --platform linux-64 --platform osx-64 -f ci/py3.12.yml --lockfile ci/conda-lock-py3.12.yml
	conda-lock lock --mamba --check-input-hash --platform linux-64 --platform osx-64 -f ci/py3.13.yml --lockfile ci/conda-lock-py3.13.yml
	conda-lock lock --mamba --check-input-hash --platform linux-64 --platform osx-64 -f ci/py3.14.yml --lockfile ci/conda-lock-py3.14.yml
	conda-lock render --platform linux-64 --filename-template ci/conda-lock-{platform}-py3.11 ci/conda-lock-py3.11.yml
	conda-lock render --platform linux-64 --filename-template ci/conda-lock-{platform}-py3.12 ci/conda-lock-py3.12.yml
	conda-lock render --platform linux-64 --filename-template ci/conda-lock-{platform}-py3.13 ci/conda-lock-py3.13.yml
	conda-lock render --platform linux-64 --filename-template ci/conda-lock-{platform}-py3.14 ci/conda-lock-py3.14.yml
	conda-lock render --platform osx-64 --filename-template ci/conda-lock-{platform}-py3.11 ci/conda-lock-py3.11.yml
	conda-lock render --platform osx-64 --filename-template ci/conda-lock-{platform}-py3.12 ci/conda-lock-py3.12.yml
	conda-lock render --platform osx-64 --filename-template ci/conda-lock-{platform}-py3.13 ci/conda-lock-py3.13.yml
	conda-lock render --platform osx-64 --filename-template ci/conda-lock-{platform}-py3.14 ci/conda-lock-py3.14.yml
	mv ci/conda-lock-linux-64-py3.11 ci/conda-lock-Linux-64-py3.11
	mv ci/conda-lock-linux-64-py3.12 ci/conda-lock-Linux-64-py3.12
	mv ci/conda-lock-linux-64-py3.13 ci/conda-lock-Linux-64-py3.13
	mv ci/conda-lock-linux-64-py3.14 ci/conda-lock-Linux-64-py3.14
	mv ci/conda-lock-osx-64-py3.11 ci/conda-lock-macOS-64-py3.11
	mv ci/conda-lock-osx-64-py3.12 ci/conda-lock-macOS-64-py3.12
	mv ci/conda-lock-osx-64-py3.13 ci/conda-lock-macOS-64-py3.13
	mv ci/conda-lock-osx-64-py3.14 ci/conda-lock-macOS-64-py3.14

conda_lock:
	conda-lock lock --mamba --check-input-hash -f pyproject.toml --lockfile conda-lock.yml
	conda-lock render -e grib --filename-template requirements/conda-lock-{platform} conda-lock.yml
	mv requirements/conda-lock-linux-64 requirements/conda-lock-Linux-64
	mv requirements/conda-lock-osx-64 requirements/conda-lock-macOS-64


poetry_lock:
	poetry lock
	poetry export -f requirements.txt --without-hashes -o requirements/requirements.txt
	poetry export -f requirements.txt --without-hashes -E all -o requirements/requirements-extras.txt
	poetry export -f requirements.txt --without-hashes --with dev -E all -o requirements/requirements-dev.txt

lock: conda_lock poetry_lock
