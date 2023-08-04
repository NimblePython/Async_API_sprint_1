run:
	python -m src.main

lint:
	flake8 .
	mypy .