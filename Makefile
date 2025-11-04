.PHONY: init lint test run format

init:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	pre-commit install

format:
	black src tests
	isort src tests

lint:
	flake8 src tests
	mypy src

test:
	pytest --maxfail=1 --disable-warnings

run:
	python -m src.bot.main
