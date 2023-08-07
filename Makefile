run:
	python -m src.main

lint:
	flake8 .
	mypy .

up.local:
	docker-compose -f docker-compose.dev.yml --env-file .env.local up -d