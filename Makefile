#!make
include .env.local  # TODO: для production, здесь может потребоваться .env
export
# нужно проверить, не перекрывают ли переменные окружения .env
# для переменных docker-compose.yml


run:
	python -m src.main

lint:
	flake8 .
	mypy .

up.local:
	docker compose -f docker-compose.dev.yml --env-file .env.local up -d

down.local:
	docker compose -f docker-compose.dev.yml --env-file .env.local down

# таргет необходим, только на этапе отладки. Позже - убрать:
debug.film.service:
	python -m src.services.film