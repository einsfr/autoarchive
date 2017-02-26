import unittest
import os
import json
import copy

from application import Application, ConfigurationException
from args_parser import args_parser

BASE_DIR = os.path.dirname(__file__)


class TestConfiguration(unittest.TestCase):

    DUMMY_CONF = {
        'ffmpeg_path': os.path.join(BASE_DIR, 'conf_files', 'dummy_file'),
        'ffprobe_path': os.path.join(BASE_DIR, 'conf_files', 'dummy_file'),
        'temp_dir': os.path.join(BASE_DIR, 'conf_files', 'dummy_dir'),
        'out_dir': os.path.join(BASE_DIR, 'conf_files', 'dummy_dir'),
        'log_dir': os.path.join(BASE_DIR, 'conf_files', 'dummy_dir'),
    }

    def test_nonexistent_conf_file(self):
        with self.assertRaises(FileNotFoundError):
            app = Application(BASE_DIR, args_parser.parse_args(['-c', 'nonexistentpath.json', 'version']))

    def test_not_a_json_conf(self):
        with self.assertRaises(json.decoder.JSONDecodeError):
            app = Application(
                BASE_DIR, args_parser.parse_args(['-c', os.path.join('conf_files', 'notajsonconf.json'), 'version'])
            )

    def test_missing_conf_parameters(self):
        with self.assertRaises(ConfigurationException):
            app = Application(
                BASE_DIR, args_parser.parse_args(['-c', os.path.join('conf_files', 'dummy_file'), 'version']),
                {}
            )

    def test_ok(self):
        app = Application(
            BASE_DIR, args_parser.parse_args(['-c', os.path.join('conf_files', 'dummy_file'), 'version']),
            self.DUMMY_CONF
        )

    def test_not_a_file(self):
        conf = copy.copy(self.DUMMY_CONF)
        conf['ffmpeg_path'] = 'nonexistentfile'
        with self.assertRaises(ConfigurationException):
            app = Application(
                BASE_DIR, args_parser.parse_args(['-c', os.path.join('conf_files', 'dummy_file'), 'version']), conf
            )

        conf = copy.copy(self.DUMMY_CONF)
        conf['ffprobe_path'] = 'nonexistentfile'
        with self.assertRaises(ConfigurationException):
            app = Application(
                BASE_DIR, args_parser.parse_args(['-c', os.path.join('conf_files', 'dummy_file'), 'version']), conf
            )

    def test_not_a_dir(self):
        conf = copy.copy(self.DUMMY_CONF)
        conf['temp_dir'] = 'nonexistentdir'
        with self.assertRaises(ConfigurationException):
            app = Application(
                BASE_DIR, args_parser.parse_args(['-c', os.path.join('conf_files', 'dummy_file'), 'version']), conf
            )

        conf = copy.copy(self.DUMMY_CONF)
        conf['out_dir'] = 'nonexistentdir'
        with self.assertRaises(ConfigurationException):
            app = Application(
                BASE_DIR, args_parser.parse_args(['-c', os.path.join('conf_files', 'dummy_file'), 'version']), conf
            )

        conf = copy.copy(self.DUMMY_CONF)
        conf['log_dir'] = 'nonexistentdir'
        with self.assertRaises(ConfigurationException):
            app = Application(
                BASE_DIR, args_parser.parse_args(['-c', os.path.join('conf_files', 'dummy_file'), 'version']), conf
            )

