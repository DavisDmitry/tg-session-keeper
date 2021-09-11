format:
	poetry run isort .
	poetry run black .

lint:
	poetry run isort --check --diff .
	poetry run black --check --diff .
