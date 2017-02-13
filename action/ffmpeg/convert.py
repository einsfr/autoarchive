import logging
import os
import pprint
import json
import jsonschema

from action import AbstractAction
from ffmpeg.ffprobe import FFprobeInfoCommand
from ffmpeg.ffmpeg import FFmpegConvertCommand
from ffmpeg import jinja_env
from ffmpeg.inter_prog_solver import FFprobeInterlacedProgressiveSolver


class FfmpegConvertAction(AbstractAction):

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

    def __init__(self, conf: dict, simulate: bool):
        super().__init__(conf, simulate)
        logging.debug('Creating FFmpegConvertCommand object...')
        self._ffmpeg_convert = FFmpegConvertCommand(conf['ffmpeg_path'], conf['temp_dir'], simulate)

    @classmethod
    def _validate_profile(cls, profile_dict: dict) -> None:
        logging.debug('Validating profile...')
        jsonschema.validate(profile_dict, cls.PROFILE_SCHEMA)

    def run(self, input_url: str, action_params: dict, out_dir_path: str) -> None:
        logging.debug('Using FFprobe to collect input file parameters...')
        ffprobe_info = FFprobeInfoCommand(self._conf['ffprobe_path'])
        input_params = ffprobe_info.exec(input_url, show_programs=False)
        logging.debug('Input parameters:\r\n{}'.format(pprint.pformat(input_params)))

        logging.debug('Searching for video and audio streams...')
        v_streams = {}
        a_streams = {}
        for s in input_params['streams']:
            if s['codec_type'] == 'video':
                v_streams[s['index']] = s
            elif s['codec_type'] == 'audio':
                a_streams[s['index']] = s
        v_streams_count = len(v_streams)
        a_streams_count = len(a_streams)
        logging.debug('Found {} video stream(s) and {} audio stream(s)'.format(v_streams_count, a_streams_count))
        logging.debug('Video stream index(es): {}, audio stream indexes: {}'.format(
            ', '.join([str(v) for v in v_streams.keys()]),
            ', '.join([str(a) for a in a_streams.keys()])))
        logging.debug('Trying to determine field mode of all video streams...')
        interlacing_modes = FFprobeInterlacedProgressiveSolver(self._conf).solve(input_url, len(v_streams))
        for k, v in interlacing_modes.items():
            v_streams[k]['field_mode'] = v

        profile_template_name = action_params['profile']
        logging.debug('Loading profile template {}'.format(profile_template_name))
        template = jinja_env.get_template(profile_template_name)
        logging.debug('Building profile template rendering context...')
        context = {
            'in_filename': os.path.splitext(os.path.split(input_url)[1])[0],
            'in_format': input_params['format'],
            'in_v_streams_count': v_streams_count,
            'in_v_streams': v_streams,
            'in_a_streams_count': a_streams_count,
            'in_a_streams': a_streams,
        }
        logging.debug('Rendering context:\r\n{}'.format(pprint.pformat(context)))
        profile_data = template.render(context)
        logging.debug('Rendered profile:\r\n{}'.format(profile_data))
        logging.debug('Profile rendering complete - loading...')
        try:
            profile_dict = json.loads(profile_data)
        except ValueError as e:
            raise ValueError('Profile {} is not a valid JSON document: {}'.format(profile_template_name, str(e)))
        self._validate_profile(profile_dict)
        logging.debug('Starting FFmpeg conversion...')
        self._ffmpeg_convert.exec(
            [(profile_dict['inputs'][0]['parameters'], input_url)],
            [(o['parameters'], os.path.join(out_dir_path, o['filename'])) for o in profile_dict['outputs']]
        )
