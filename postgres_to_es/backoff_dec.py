"""Параметрический декоратор для осуществления паузы между повторными вызовами функции."""

import logging
import time
from functools import wraps


def backoff(start_sleep_time=0.1, factor=2, border_sleep_time=10):
    """Декоратор для паузы между вызовами одной и той же функции в случае ошибки.

    Использует наивный экспоненциальный рост времени повтора (factor)
    до граничного времени ожидания (border_sleep_time)

    Формула:
        t = start_sleep_time * 2^(n) if t < border_sleep_time
        t = border_sleep_time if t >= border_sleep_time

    Args:
        start_sleep_time: начальное время повтора
        factor: во сколько раз нужно увеличить время ожидания
        border_sleep_time: граничное время ожидания

    Returns:
        Функция-обёртка
    """
    def func_wrapper(func):
        @wraps(func)
        def inner(*args, **kwargs):
            logging.debug('Выполнение функции %s' % func.__name__)
            pwr = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except Exception as err:
                    logging.warning('Ошибка %s выполнения функции %s' % (err, func.__name__))
                    pwr += 1
                    pause = start_sleep_time * factor**pwr
                    if pause >= border_sleep_time:
                        pause = border_sleep_time
                    logging.debug('Пауза до следующего выполнения функции: %s сек' % pause)
                    time.sleep(pause)
        return inner
    return func_wrapper
