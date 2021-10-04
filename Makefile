.PHONY: list
list:
	@LC_ALL=C $(MAKE) -pRrq -f $(lastword $(MAKEFILE_LIST)) : 2>/dev/null | awk -v RS= -F: '/^# File/,/^# Finished Make data base/ {if ($$1 !~ "^[#.]") {print $$1}}' | sort | egrep -v -e '^[^[:alnum:]]' -e '^$@$$'


conda_lock:
	conda-lock -f environment.yml --check-input-hash -p linux-64 --filename-template ci/conda-Linux-64.lock
	conda-lock -f environment.yml --check-input-hash -p osx-64   --filename-template ci/conda-Macos-64.lock

poetry_lock:
	poetry lock --no-update
	poetry export -f requirements.txt --without-hashes --only default -o ci/requirements.txt
	poetry export -f requirements.txt --without-hashes --only default -E grib -o ci/requirements-grib.txt
	poetry export -f requirements.txt --without-hashes --only default --only test -E grib -o ci/requirements-test.txt
	poetry export -f requirements.txt --without-hashes --only default --only dev --only test -E grib -o ci/requirements-dev.txt

lock: conda_lock poetry_lock
