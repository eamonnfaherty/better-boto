.PHONY: install test

install:
	pip install -r requirements.txt

test:
	pytest --cov=betterboto --cov-report=term-missing --cov-fail-under=95
