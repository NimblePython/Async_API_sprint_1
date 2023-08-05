"""Модуль, где задаётся модель Pydantic, использующая для сериализации и десериализации orjson."""
import orjson
from pydantic import BaseModel


def orjson_dumps(value_to_dump, *, default):
    """Конвертировать в передаваемое значение в json-строку.

    "*" - обозначает конец позиционных аргументов (PEP 3102)
    To serialize a subclass or arbitrary types, specify default as a callable
    that returns a supported type. specify default as a callable that returns a supported type.

    Parameters:
        value_to_dump: значение, которое нужно конвертировать
        default: default may be a function, lambda, or callable class instance


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
