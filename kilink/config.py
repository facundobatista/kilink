# -*- coding: utf8 -*-

"""Config management."""

import yaml


class Config(dict):
    """Configuration helper class.

    It starts empty, and then the config can be set at any time.
    """
    def load_file(self, filename):
        """Set the configuration from a YAML file."""
        with open(filename, "rt") as fh:
            cfg = yaml.load(fh.read())
        self.update(cfg)

config = Config()

LANGUAGES = {
    'en': 'English',
    'es': 'Español',
}
