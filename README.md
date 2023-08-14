# Проектная работа 4 спринта - сервисы на FastPAI

# Запустить сервис

В терминале ОС введите команду 
```bash 
make up
```

# Описание

Подробное описание API доступно по адресу: http://0.0.0.0:8000/api/openapi#/ (необходим запущенный сервис)

В версии 1 реализованы следующие эндпоинты:

**Информация о фильме**
/api/v1/films/{film_id}

**Информация о персоналиях**
/api/v1/persons/{person_id}

**Информация о фильмографии актера, режисера или сценариста**
/api/v1/persons/{person_id}/film/

**Информация о жанре**
/api/v1/genres/{genre_id}

**Информация о всех жанрах**
/api/v1/genres/

**Полнотекстный поиск по персналиям с пагинатором**
/api/v1/persons/search?query=john&page_number=1&page_size=10

 DONE: Ссылка на этот репозиторий: (https://github.com/NimblePython/Async_API_sprint_1)

 DONE: Приглашение BlueDeep отправлено

# Отладка сервиса текущего проекта

## Предварительные условия

1. docker compose
2. python 3.11
3. poetry

для локальной отладки проекта запустите db, elastic, redis в отладочном docker compose:
```bash
docker compose -f docker-compose.dev.yml up -d
```

и запустите отладку сервиса получения данных о фильме из elasticsearch:

```
python -m src.main
```

при этом в переменные окружения должно быть экспортировано содержимое файла .env.local
(это можно сделать средствами IDE)

Либо запустить
```
make debug.film.service
```
перед непосредственным запуском дебага make экспортирует содержимое из .env.local

(сейчас это происходит без необходимости использовать аргумент команды make, позже (скорее всего) по умолчанию будет экспортироваться файл .env, а для того чтобы использовать env.local нужно будет использовать аргумент)

## Что делать, если env-файл уже был добавлен в стейджинг до того, как его добавили в .gitignore?
Убрать его из стейджинга:
```
git rm .env.local --cached
git commit -m "feature/git не отcлеживает .env.local"
```

## Тестирование API
Чтобы убедиться в работе сервисов достаточно запустить в приложении Postman тесты из файлов:
- ```ETLTests.postman_collection.json```
- ```FastAPI.postman_collection.json```

**Внимание!** Замените uuid запросов на актуальные uuid из своей БД

**Чтобы узнать id сущностей**, выполните запрос:

Для фильмов ```psql -U myuser -d mydb -c "SELECT * FROM content.filmworks;" ```

Для персон ```psql -U myuser -d mydb -c "SELECT * FROM content.persons;" ```

Для жанров ```psql -U myuser -d mydb -c "SELECT * FROM content.genres;" ```

## Работа с ETL
**Общее описание работы**
1. Обновление данных происходит из БД Postgres в БД ElasticSearch посредством отслеживания ключей состояния
2. Ключи состояния регистрируют дату-время последней успешно записанной сущности в ElasticSearch
3. Ключи состояния хранятся в файле ```conditions.txt``` в читаемом виде

**Если надо, чтобы ETL обновил все данные (по-новой)**
1. Если удалить файл conditions.txt (или любую пару ключ-значение из него), то ETL запустит обновление данных (целиком или по удаленному ключу)
2. Чтобы обновить данные на чисто (без артефактов от предыдущей работы) следует удалить целиком индекс в ElasticSearch. 
Для удаления индекса можно воспользоваться тестами Postman, а всего индексов 3: ```movies```, ```persons```, ```genres```

