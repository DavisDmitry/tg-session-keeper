format:
	poetry run isort .
	poetry run black .

lint:
	poetry run mypy session_keeper
	poetry run isort --check --diff .
	poetry run black --check --diff .
	poetry run pylint session_keeper
