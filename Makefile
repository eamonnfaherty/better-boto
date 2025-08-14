test:
	pip install -e .[dev]
	pytest --cov=betterboto --cov-report=xml --cov-fail-under=95
