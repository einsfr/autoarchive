""" Модуль с реализациями конвертеров

"""

from utils.module_import import get_class


def get_converter_class(conv_id: str):
    """ Возвращает класс, описывающий конвертер, по названию конвертера

    Args:
        conv_id: название конвертера

    Returns:
        Класс, описывающий конвертер
    """
    return get_class('converter', conv_id)
