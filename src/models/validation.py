# -*- coding: utf-8 -*-
"""Модуль валидации данных.

Реализованы функции вне классов моделей для достижения принципа DRY.
TODO: Необходимо подумать над упрощением алгоритма и сведения двух функций в одну
"""
import logging
import uuid


def check_uuid(checked_value: str) -> bool:
    """Проверка соответствия параметра формату UUID.

    Функция отлавливает исключение ValueError и выдает сообщение в logger

    Args:
        checked_value: Проверяемое значение

    Returns:
        Возвращает истину при соответствии или ложь
    """
    try:
        uuid.UUID(checked_value)
    except ValueError as err:
        logging.info('Input should be a valid UUID, unable to parse string as a UUID.')
        return False
    return True


def serialize_uuid(uuid_obj):
    """Функция сериализации UUID в текст. Нужна для JSON библиотеки.

    JSON библиотека по умолчанию не справляется с этой задачей.

    Args:
        uuid_obj: UUID для перевода в строку

    Returns:
        Строка c UUID

    Raises:
        TypeError: Если ошибка в формате UUID
    """
    if isinstance(uuid_obj, uuid.UUID):
        return str(uuid_obj)
    raise TypeError('Object of type {0} is not JSON serializable'.format(type(uuid_obj)))
