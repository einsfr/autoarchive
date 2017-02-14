from utils.module_import import get_class


def get_dispatcher_class(disp_id: str):
    return get_class('dispatcher', disp_id)


class PolicyViolationException(RuntimeError):
    pass


class ActionRunException(RuntimeError):
    pass
