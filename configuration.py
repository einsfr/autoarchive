import os
import json
import sys


class ConfigurationException(Exception):
    pass


def validate_configuration(json_content: dict) -> dict:

    def _required(pl: list) -> None:
        for p in pl:
            if p not in json_content:
                raise ConfigurationException('Required configuration parameter "{}" is missing.'.format(p))

    def _is_a_file(pl: list) -> None:
        for p in pl:
            json_content[p] = os.path.abspath(json_content[p])
            if not os.path.isfile(json_content[p]):
                raise ConfigurationException(
                    'Path in configuration parameter {} "{}" is not a file.'.format(p, json_content[p])
                )

    def _is_a_dir(pl: list) -> None:
        for p in pl:
            json_content[p] = os.path.abspath(json_content[p])
            if not os.path.isdir(json_content[p]):
                raise ConfigurationException(
                    'Path in configuration parameter {} "{}" is not a directory.'.format(p, json_content[p])
                )

    params = ['ffmpeg_path', 'ffprobe_path', 'temp_dir', 'out_dir', 'log_dir', ]

    _required(params)
    _is_a_file(['ffmpeg_path', 'ffprobe_path', ])
    _is_a_dir(['temp_dir', 'out_dir', 'log_dir', ])

    return dict([(k, json_content[k]) for k in params])


def get_configuration(path: str) -> dict:
    with open(path) as c_file:
        return validate_configuration(json.load(c_file))
