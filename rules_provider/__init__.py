from utils.module_import import get_class


def get_rules_provider_class(rp_id: str):
    return get_class('rules provider', rp_id)


def validate_rules_set(rules_set: dict):
    if type(rules_set) != dict:
        raise TypeError('Rules set must be a dictionary - {} given'.format(type(rules_set)))
    required_keys = ['policy', 'patterns', ]
    if any([k not in rules_set for k in required_keys]):
        raise KeyError('Rules set must have following keys: {}'.format(required_keys))
    patterns = rules_set['patterns']
    if type(patterns) != list:
        raise TypeError('Patterns must be a list - {} given'.format(type(patterns)))
    if len(patterns) == 0:
        raise ValueError('Patterns list can\'t be empty')
    for n, p in enumerate(patterns):
        if type(p) != list:
            raise TypeError('Each pattern must be a list - {} given in item {}'.format(type(p), n))
        if len(p) != 3:
            raise ValueError('Each pattern list must consist of 3 items - {} given'.format(len(p)))
        if type(p[0]) != str:
            raise TypeError(
                'Pattern list\'s first element must be a string (regular expression) - {} given'.format(
                    type(p[0])))
        if type(p[1]) != str:
            raise TypeError('Pattern list\'s second element must be a string (action id) - {} given'.format(
                type(p[1])))
        if type(p[2]) != dict:
            raise TypeError('Pattern list\'s third element must be a dictionary (action parameters) - {} given'.format(
                type(p[2])))
    policy = rules_set['policy']
    allowed_policies = ['skip', 'error', 'warning']
    if policy not in allowed_policies:
        raise ValueError('Unknown policy: {}. Allowed values: []'.format(policy, allowed_policies))
