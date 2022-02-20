format:
	poetry run isort .
	poetry run black .

lint:
	poetry run mypy session_keeper tests
	poetry run isort --check --diff .
	poetry run black --check --diff .
	poetry run pylint session_keeper tests
	poetry run darglint session_keeper

test:
	poetry run pytest --cov=session_keeper --cov-report=term-missing
