import os
import json
import logging
import pprint

from rules_provider import validate_rules_set


class JsonRulesProvider:

    def get_rules(self, rules_set_path: str) -> dict:
        rules_set_path = os.path.abspath(rules_set_path)
        logging.info('Loading rules set: {}...'.format(rules_set_path))
        try:
            with open(rules_set_path) as rs_file:
                rules_set = json.load(rs_file)
        except FileNotFoundError:
            raise FileNotFoundError('Rules set files doesn\'t exist: {}'.format(rules_set_path))
        except ValueError as e:
            raise ValueError('Rules set file {} is not a valid JSON document: {}'.format(rules_set_path, str(e)))
        logging.info('Validating rules set...')
        logging.debug('Loaded rules set:\r\n{}'.format(pprint.pformat(rules_set)))
        validate_rules_set(rules_set)
        return rules_set
