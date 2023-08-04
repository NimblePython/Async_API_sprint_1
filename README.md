# Проектная работа 4 спринта

**Важное сообщение для тимлида:** для ускорения проверки проекта укажите ссылку на приватный репозиторий с командной работой в файле readme и отправьте свежее приглашение на аккаунт [BlueDeep](https://github.com/BigDeepBlue).

 DONE: Ссылка на этот репозиторий: [ТУТ] (https://github.com/NimblePython/Async_API_sprint_1)

 DONE: Приглашение BlueDeep отправлено

В папке **tasks** ваша команда найдёт задачи, которые необходимо выполнить в первом спринте второго модуля.  Обратите внимание на задачи **00_create_repo** и **01_create_basis**. Они расцениваются как блокирующие для командной работы, поэтому их необходимо выполнить как можно раньше.

Мы оценили задачи в стори поинтах, значения которых брались из [последовательности Фибоначчи](https://ru.wikipedia.org/wiki/Числа_Фибоначчи) (1,2,3,5,8,…).

Вы можете разбить имеющиеся задачи на более маленькие, например, распределять между участниками команды не большие куски задания, а маленькие подзадачи. В таком случае не забудьте зафиксировать изменения в issues в репозитории.

**От каждого разработчика ожидается выполнение минимум 40% от общего числа стори поинтов в спринте.**


## Линтеры, кроме wemake

### 1. flake8 = "^6.0.0"

e1: ставится вместе с wemake

### 2. autopep8 = "^2.0.2"
y1: установил:
autopep8 is the best choice for wemake-python-styleguide users.
Is officially supported in way that all code written inside wemake-python-styleguide is tested to be valid autopep8 code. But, not the other way around.

### 3. isort = "^5.12.0"
e2. Ставится вместе с wemake: isort is a great tool to sort your imports. We already use it to validate that your imports are correct. We recommend to use isort and officially and support it in a way that all valid wemake-python-styleguide code is valid isort code. But, not the other way around.

### 4. flake8-isort = "^6.0.0"
v1.
Пока не установил:
Из документации не ясно - не дублирует ли isort

### 5. flake8-blind-except = "^0.2.1"
d1.
Не установлен: отлавливает "голые" except'ы - этот функционал есть в wemake (B001, E722) 

### 6. flake8-broken-line = "^1.0.0"
e3. Ставится вместе с wemake'ом:
N400: Found backslash that is used for line breaking

Подобный violation wemake'а:
WPS337 Found multiline conditions

### 7. flake8-bugbear = "^23.7.10"
e4. Встроенный плагин wemake
B001 - B008

### 8. flake8-builtins = "^2.1.0"
d2. Не установлен, дублирует wemake:
WPS125 Found builtin shadowing

### 9. flake8-class-attributes-order = "^0.1.3"
v2. Не установил: решили настроить wemake.
Есть разница в предлагаемой очередности методов класса (в том чилсе wemake считает, что вообще не нужно использовать static-методы и не рекомендует использовать private)

WPS338 Found incorrect order of methods in a class
We follow the same ordering:
1. __init_subclass__
2. __new__
3. __init__
4. __call__
5. __await__
6. public and magic methods
7. protected methods
8. private methods (we discourage using them)

flake8-class-attribute-order:
1. __new__
2. __init__
3. __post_init__
4. other magic method
5. @property
6. @staticmethod
7. @classmethod
8. other methods
9. private @property
10. private @staticmethod
11. private @classmethod
12. other private methods

### 10. flake8-cognitive-complexity = "^0.1.0"
d3. Не установил. Т.к. ССR001 дублирует виолейшены wemake
WPS231

WPS231 Found function with too much cognitive complexity: 36 > 12

### 11. flake8-commas = "^2.1.0"
e5. Идёт вместе с wemake

### 12. flake8-comprehensions = "^3.14.0"
e6. Идёт вместе с wemake

### 13. flake8-debugger = "^4.1.2"
e7. """Extension for flake8 that finds usage of the debugger."""
Идёт вместе с wemake: 	
T100

### 14. flake8-eradicate = "^1.5.0"
e7. Идёт вместе с wemake. E800
plugin to find commented out (or so called "dead") code.

### 15. flake8-functions = "^0.0.8"
v3. Пока не установил. Т.к. есть пересечения с wemake
CFQ001 - function length (default max length is 100)
vs
WPS213 Found too many expressions: 63 > 9
(Не совсем то же самое, плюс wemake здесь строже, если использовать настройки по умолчанию)

CFQ002 - function arguments number (default max arguments amount is 6)
vs
WPS211 Found too many arguments: 17 > 5
6 против 5 допустимых аргуметов функции (можно настроить, если нужно)

CFQ003 - function is not pure.
Вот это интересно. Функция является not pure - если при одних и тех же аргументах она может вернуть разные значения.

Не знаю, есть ли подобная проверка в wemake
конкретно CFQ003. Но я сходу не смог подобрать пример, на который бы ругался хотя бы один линтер.

CFQ004 - function returns number (default max returns amount is 3)

Пример: CFQ004 Function "foo" has 4 returns that exceeds max allowed 3

wemake здесь менее строг:
WPS212 Found too many return statements: 7 > 5

### 16. flake8-mutable = "^1.2.0"
d4. дублирует wemake:
B006 Do not use mutable data structures for argument defaults.  They are created during function definition time. All calls to the function reuse this one instance of that data structure, persisting changes between them.

### 17. flake8-print = "^5.0.0"
d5. Дублирует wemake:
WPS421 Found wrong function call: pprint
WPS421 Found wrong function call: print

### 18. flake8-pytest = "^1.4"
у2.
запускает flake8 со всеми плагинами над тестами.
установил

Удалил.

Рушит линтеры на файлах с кодировкой utf-8
я выяснил над какими файлами он рушится:
```
<_io.TextIOWrapper name='src\\api\\v1\\films.py' mode='r' encoding='cp1251'>
'charmap' codec can't decode byte 0x98 in position 1049: character maps to <undefined> <_io.TextIOWrapper name='src\\api\\v1\\films.py' mode='r' encoding='cp1251'>
'charmap' codec can't decode byte 0x98 in position 261: character maps to <undefined> <_io.TextIOWrapper name='src\\core\\config.py' mode='r' encoding='cp1251'>
'charmap' codec can't decode byte 0x98 in position 45: character maps to <undefined> <_io.TextIOWrapper name='src\\models\\film.py' mode='r' encoding='cp1251'>
<_io.TextIOWrapper name='src\\services\\film.py' mode='r' encoding='cp1251'>
'charmap' codec can't decode byte 0x98 in position 3311: character maps to <undefined> <_io.TextIOWrapper name='src\\services\\film.py' mode='r' encoding='cp1251'>
```

### 19. flake8-pytest-style = "^1.7.2"
у3.
установил

### 20. flake8-quotes = "^3.3.2"
e9. присутствует в wemake

### 21. flake8-string-format = "^0.3.0"
e10. присутствует в wemake

### 22. flake8-variables-names = "^0.0.6"
d6. дублирует wemake
WPS110 Found wrong variable name: foo

### 23. flake8-docstrings = "^1.7.0"
e11. Присутствует в wemake

Всего предложено плагинов 23 (считаем flake 8).
11 - входят в состав wemake
6 - дублируют wemake
3 - установил
3 - есть вопросы


flake8-pytest = "^1.4"
flake8-pytest-style = "^1.7.2"
mypy = "^1.4.1"

[tool.poetry.group.dev.dependencies]
wemake-python-styleguide = "^0.18.0"
flake8 = "^6.1.0"
isort = "^5.12.0"