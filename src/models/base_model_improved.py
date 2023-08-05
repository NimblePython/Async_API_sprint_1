"""Модуль, где задаётся модель Pydantic, использующая для сериализации и десериализации orjson."""
import orjson
from pydantic import BaseModel


def orjson_dumps(value_to_dump, *, default):
    """Конвертировать в передаваемое значение в json-строку.

    "*" - обозначает конец позиционных аргументов (PEP 3102)

    Чтобы сериализовать подкласс или произвольные типы, задайте default как callable, который
    возвращает поддерживаемый тип.

    Parameters:
        value_to_dump: значение, которое нужно конвертировать
        default: функция, lambda или экземпляр callable класса


    Returns:
        json_str: строка в формате json
    """
    # orjson.dumps возвращает bytes, а pydantic требует unicode, поэтому декодируем
    return orjson.dumps(value_to_dump, default=default).decode()


class BaseModelImproved(BaseModel):
    """Модель данных c улучшенной работой с json."""

    class Config(object):
        """Класс конфигурации модели Pydantic."""

        # Заменяем стандартную работу с json на более быструю
        json_loads = orjson.loads
        json_dumps = orjson_dumps
