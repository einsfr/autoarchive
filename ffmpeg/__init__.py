import os
import logging

from jinja2 import Environment, FileSystemLoader

from autoarchive import BASE_DIR

logging.info('FFmpeg is a trademark of Fabrice Bellard <http://www.bellard.org/>, originator of the FFmpeg project.')

jinja_env = Environment(
    loader=FileSystemLoader(os.path.join(BASE_DIR, 'ff_profiles')),
    autoescape=False
)
