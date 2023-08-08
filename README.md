# Проектная работа 4 спринта

**Важное сообщение для тимлида:** для ускорения проверки проекта укажите ссылку на приватный репозиторий с командной работой в файле readme и отправьте свежее приглашение на аккаунт [BlueDeep](https://github.com/BigDeepBlue).

 DONE: Ссылка на этот репозиторий: [ТУТ] (https://github.com/NimblePython/Async_API_sprint_1)

 DONE: Приглашение BlueDeep отправлено

В папке **tasks** ваша команда найдёт задачи, которые необходимо выполнить в первом спринте второго модуля.  Обратите внимание на задачи **00_create_repo** и **01_create_basis**. Они расцениваются как блокирующие для командной работы, поэтому их необходимо выполнить как можно раньше.

Мы оценили задачи в стори поинтах, значения которых брались из [последовательности Фибоначчи](https://ru.wikipedia.org/wiki/Числа_Фибоначчи) (1,2,3,5,8,…).

Вы можете разбить имеющиеся задачи на более маленькие, например, распределять между участниками команды не большие куски задания, а маленькие подзадачи. В таком случае не забудьте зафиксировать изменения в issues в репозитории.

**От каждого разработчика ожидается выполнение минимум 40% от общего числа стори поинтов в спринте.**

# Отладка сервиса текущего проекта

## предварительные условия

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
Work in progress!..