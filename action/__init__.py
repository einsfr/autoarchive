from utils.module_import import get_class


def get_action_class(action_id: str):
    return get_class('action', action_id)
