from jinja2 import Environment
import logging


class AbstractProfileDataProvider:

    def get_profile_data(self, profile_name: str, **kwargs):
        raise NotImplementedError


class JinjaProfileDataProvider(AbstractProfileDataProvider):

    def __init__(self, template_loader):
        self._jinja_env = Environment(loader=template_loader, autoescape=False)

    def get_profile_data(self, profile_name: str, **kwargs):
        logging.debug('Loading profile template {}'.format(profile_name))
        template = self._jinja_env.get_template(profile_name)
        profile_data = template.render(kwargs['context'])
        logging.debug('Rendered profile:\r\n{}'.format(profile_data))

        return profile_data
