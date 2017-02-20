import logging
import os
import json
import jsonschema

from dispatcher import ActionRunException
from action import OutDirCreatingAction
from ffmpeg.ffmpeg import FFmpegConvertCommand
from ffmpeg import jinja_env
from ffmpeg import exceptions as ffmpeg_exceptions
from ffmpeg.metadata_collector import FFprobeMetadataCollector
from ffmpeg import get_ffmpeg_factory


class FfmpegConvertAction(OutDirCreatingAction):

    PROFILE_SCHEMA = {
        'title': 'Profile',
        'type': 'object',
        'properties': {
            'inputs': {
                'title': 'Profile inputs list',
                'type': 'array',
                'items': {
                    'title': 'Profile input',
                    'type': 'object',
                    'properties': {
                        'parameters': {
                            'title': 'Profile input\'s parameters',
                            'type': 'array',
                            'items': {
                                'title': 'Profile input\'s parameter',
                                'type': 'string'
                            }
                        }
                    },
                    'required': ['parameters', ]
                },
                'minItems': 1
            },
            'outputs': {
                'title': 'Profile outputs list',
                'type': 'array',
                'items': {
                    'title': 'Profile output',
                    'type': 'object',
                    'properties': {
                        'parameters': {
                            'title': 'Profile output\'s parameters',
                            'type': 'array',
                            'items': {
                                'title': 'Profile output\'s parameter',
                                'type': 'string'
                            }
                        },
                        'filename': {
                            'title': 'Profile output\'s filename',
                            'type': 'string'
                        }
                    },
                    'required': ['parameters', 'filename', ]
                },
                'minItems': 1
            }
        },
        'required': ['inputs', 'outputs']
    }

    def __init__(self):
        super().__init__()
        _factory = get_ffmpeg_factory()
        logging.debug('Fetching FFmpegConvertCommand object...')
        self._ffmpeg_convert = _factory.get_ffmpeg_command(FFmpegConvertCommand)
        logging.debug('Fetching FFprobeMetadataCollector object...')
        self._ffprobe_meta_collector = _factory.get_ffprobe_metadata_collector(FFprobeMetadataCollector)

    @classmethod
    def _validate_profile(cls, profile_dict: dict) -> None:
        logging.debug('Validating profile...')
        jsonschema.validate(profile_dict, cls.PROFILE_SCHEMA)

    def run(self, input_url: str, action_params: dict, out_dir_path: str) -> None:
        super().run(input_url, action_params, out_dir_path)
        profile_template_name = action_params['profile']
        logging.debug('Loading profile template {}'.format(profile_template_name))
        template = jinja_env.get_template(profile_template_name)
        logging.debug('Building profile template rendering context...')
        context = {
            'input': self._ffprobe_meta_collector.get_metadata(input_url)
        }
        profile_data = template.render(context)
        logging.debug('Rendered profile:\r\n{}'.format(profile_data))
        logging.debug('Profile rendering complete - loading...')
        try:
            profile_dict = json.loads(profile_data)
        except ValueError as e:
            raise ValueError('Profile {} is not a valid JSON document: {}'.format(profile_template_name, str(e)))
        self._validate_profile(profile_dict)
        logging.debug('Starting FFmpeg conversion...')
        try:
            self._ffmpeg_convert.exec(
                [(profile_dict['inputs'][0]['parameters'], input_url)],
                [(o['parameters'], os.path.join(out_dir_path, o['filename'])) for o in profile_dict['outputs']]
            )
        except (ffmpeg_exceptions.FFmpegInputNotFoundException, ffmpeg_exceptions.FFmpegOutputAlreadyExistsException,
                ffmpeg_exceptions.FFmpegProcessException) as e:
            raise ActionRunException from e
