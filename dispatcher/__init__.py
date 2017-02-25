""" Модуль с реализациями диспетчеров, обрабатывающих наборы правил

"""

from utils.module_import import get_class


def get_dispatcher_class(disp_id: str):
    """ Возвращает класс, описывающий диспетчер, по названию диспетчера

    Args:
        disp_id: название диспетчера

    Returns:
        Класс, описывающий диспетчер
    """
    return get_class('dispatcher', disp_id)


class PolicyViolationException(RuntimeError):
    """ Запускается при обнаружении нарушения политики обработки набора правил

    Появляется, например, когда используется политика обработки `error`, а для какого-то входного файла не находится
    ни одного соответствующего ему действия.
    """
    pass


class UnknownPolicyException(ValueError):
    """ Запускается при попытке использования политики, неизвестной диспетчеру

    """
    def __init__(self, policy_name: str, *args,  **kwargs):
        super().__init__('Unknown policy: {}'.format(policy_name), *args, **kwargs)


class ActionRunException(RuntimeError):
    """ Запускается при возникновении ошибки при выполнении действия

    """
    pass
