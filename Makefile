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

# необходимо указывать флаг --env-file, каждый раз при запуске локального docker-compose,
# т.к. yml файл выполняется каждый раз, и если не указать --env-file, compose попытается
# использоваmь для экспорта переменных файл умолчания .env. Поэтому логи контейнера с postgres
# будут предвосхищаться двумя строками о том, что переменные ${DB_USER} и ${DB_NAME_PG}
# не найдены и заполнены пустыми строками. При этом это не будет означать, что это же произошло
# при старте контейнеров (up -d), но может сбить с толку.
logs.pg.local:
	docker compose -f docker-compose.dev.yml --env-file .env.local logs postgres

logs.etl.local:
	docker compose -f docker-compose.dev.yml --env-file .env.local logs etl

rebuild.etl.local:
	docker compose -f docker-compose.dev.yml --env-file .env.local up -d --build etl
