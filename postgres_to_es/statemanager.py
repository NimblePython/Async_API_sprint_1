"""Модуль для осуществления функций записи и чтения состояний из/в хранилища."""
import abc
import json
import logging
from typing import Any


class BaseStorage(abc.ABC):
    """Абстрактное хранилище состояния.

    Позволяет сохранять и получать состояние.
    Способ хранения состояния может варьироваться в зависимости
    от итоговой реализации. Например, можно хранить информацию
    в базе данных или в распределённом файловом хранилище.
    """

    @abc.abstractmethod
    def save_state(self, state: dict[str, Any]) -> None:
        """Сохранить состояние в хранилище.

        Args:
            state: Словарь со всеми парами ключ:значение, которые необходимо сохранить
        """

    @abc.abstractmethod
    def retrieve_state(self) -> dict[str, Any]:
        """Абстрактный метод - Получить состояние из хранилища."""


class JsonFileStorage(BaseStorage):
    """Реализация хранилища, использующего локальный файл.

    Формат хранения: JSON

    Args:
        BaseStorage: Хранилище
    """

    def __init__(self, file_path: str) -> None:
        """Конструктор в котором инициализируется путь к файлу хранилища.

        Args:
            file_path: Путь к файлу
        """
        self.file_path = file_path

    def save_state(self, state: dict[str, Any]) -> None:
        """Сохранить состояние в хранилище.

        Args:
            state: Словарь со всеми парами ключ:значение, которые необходимо сохранить
        """
        with open(self.file_path, 'w') as sf:
            json.dump(state, sf)

    def retrieve_state(self) -> dict[str, Any]:
        """Получить состояние из файла.

        Returns:
            Возвращает пары Ключ:Значение в виде словаря
        """
        res = {}
        try:
            with open(self.file_path, 'r') as sf:
                res = json.load(sf)
        except FileNotFoundError:
            logging.error('Файл не найден')
        except json.JSONDecodeError:
            logging.error('Ошибка декодирования JSON')

        return res


class State:
    """Класс для работы с состояниями."""

    def __init__(self, storage: BaseStorage) -> None:
        """Конструктор. Устанавливает хранилище.

        Args:
            storage: Хранилище с которым будет работать система контроля состояний
        """
        self.storage = storage

    def set_state(self, key: str, new_value: Any) -> None:
        """Установить состояние для определённого ключа.

        Args:
            key: Ключ
            new_value: Значение
        """
        conditions = self.storage.retrieve_state()
        old_value = None
        if self.get_state(key):
            old_value = conditions[key]
        else:
            logging.warning('Несуществующий ключ: %s в set_state(). Ключ будет создан.' % key)

        conditions[key] = new_value
        try:
            self.storage.save_state(conditions)
        except Exception as err:
            logging.exception('Значение %s в ключе %s не сохранено' % (new_value, key))
            # Возвращаем старое значение ключу, так как не удалось сохранить
            if old_value:
                conditions[key] = old_value
                logging.info('Актуальным значением ключа осталось: %s' % old_value)

    def get_state(self, key: str) -> Any:
        """Получить состояние по определённому ключу.

        Args:
            key: Ключ

        Returns:
            Возвращает значение записанное по ключу.
        """
        conditions = self.storage.retrieve_state()
        if key not in conditions.keys():
            return None
        return conditions[key]
