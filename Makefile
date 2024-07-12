SHELL := /bin/bash

.PHONY: all deploy

all: requirements.txt
	test -d .venv || python -m venv .venv
	source .venv/Scripts/activate && pip install -r requirements.txt
	touch .venv

develop:
	source .venv/Scripts/activate && \
	export FLASK_APP=weather_app && \
	export FLASK_ENV=development && \
	flask run

deploy:
	source .venv/Scripts/activate && \
	waitress-serve --listen 0.0.0.0:5000 weather_app:app

test:
	source .venv/Scripts/activate && \
	pytest tests
