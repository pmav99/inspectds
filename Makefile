.PHONY: list

list:
	@LC_ALL=C $(MAKE) -pRrq -f $(lastword $(MAKEFILE_LIST)) : 2>/dev/null | awk -v RS= -F: '/^# File/,/^# Finished Make data base/ {if ($$1 !~ "^[#.]") {print $$1}}' | sort | grep -E -v -e '^[^[:alnum:]]' -e '^$@$$'

init:
	poetry install --with=dev -E grib --sync
	pre-commit install

style:
	pre-commit run black -a

lint:
	pre-commit run ruff -a

mypy:
	dmypy run inspectds

test:
	python -m pytest -vlx

cov:
	coverage erase
	python -m pytest --cov=inpsectds --cov-report term-missing --durations=10

deps:
	pre-commit run poetry-lock -a
	pre-commit run poetry-export -a

conda_lock:
	conda-lock lock --mamba --check-input-hash -p linux-64 -p osx-64 -f environment.yml --lockfile conda-lock.yml
	conda-lock render -p linux-64 --filename-template requirements/conda-lock-{platform} conda-lock.yml
	conda-lock render -p osx-64 --filename-template requirements/conda-lock-{platform} conda-lock.yml

poetry_lock:
	poetry lock --no-update
	poetry export -f requirements.txt --without-hashes -o requirements/requirements.txt
	poetry export -f requirements.txt --without-hashes -E grib -o requirements/requirements-grib.txt
	poetry export -f requirements.txt --without-hashes --with dev -E grib -o requirements/requirements-dev.txt

lock: conda_lock poetry_lock
