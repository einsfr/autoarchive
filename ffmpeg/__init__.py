import os

from jinja2 import Environment, FileSystemLoader

from autoarchive import BASE_DIR

jinja_env = Environment(
    loader=FileSystemLoader(os.path.join(BASE_DIR, 'ff_profiles')),
    autoescape=False
)
