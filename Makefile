
.PHONY: clean-pyc

build: clean-pyc
	docker-compose build sgcc-alert-build

run: build clean-container
	docker-compose up -d sgcc-alert-run

ssh:
	docker-compose exec sgcc-alert-run /bin/bash

lint:
	python -m flake8 sgcc_alert/

type-hint:
	python -m mypy sgcc_alert/

test:
	python -m pytest -sv --disable-warnings -p no:cacheprovider tests/*

clean-pyc:
	# clean all pyc files
	find . -name '__pycache__' | xargs rm -rf | cat
	find . -name '*.pyc' | xargs rm -f | cat

clean-container:
	# stop and remove useless containers
	docker-compose down --remove-orphans
