import unittest
import os
import copy

import configuration

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
            configuration.get_configuration('nonexistentpath.json')

    def test_not_a_json_conf(self):
        with self.assertRaises(ValueError):
            configuration.get_configuration(os.path.join(BASE_DIR, 'conf_files', 'notajsonconf.json'))

    def test_missing_conf_parameters(self):
        with self.assertRaises(configuration.ConfigurationException):
            configuration.validate_configuration(dict())

    def test_ok(self):
        configuration.validate_configuration(self.DUMMY_CONF)

    def test_not_a_file(self):
        conf = copy.copy(self.DUMMY_CONF)
        conf['ffmpeg_path'] = 'nonexistentfile'
        with self.assertRaises(configuration.ConfigurationException):
            configuration.validate_configuration(conf)

        conf = copy.copy(self.DUMMY_CONF)
        conf['ffprobe_path'] = 'nonexistentfile'
        with self.assertRaises(configuration.ConfigurationException):
            configuration.validate_configuration(conf)

    def test_not_a_dir(self):
        conf = copy.copy(self.DUMMY_CONF)
        conf['temp_dir'] = 'nonexistentdir'
        with self.assertRaises(configuration.ConfigurationException):
            configuration.validate_configuration(conf)

        conf = copy.copy(self.DUMMY_CONF)
        conf['out_dir'] = 'nonexistentdir'
        with self.assertRaises(configuration.ConfigurationException):
            configuration.validate_configuration(conf)

        conf = copy.copy(self.DUMMY_CONF)
        conf['log_dir'] = 'nonexistentdir'
        with self.assertRaises(configuration.ConfigurationException):
            configuration.validate_configuration(conf)
