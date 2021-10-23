# Copyright 2011-2021 Facundo Batista, Nicolás César
# All Rigths Reserved

"""Config management."""

import yaml


class Config(dict):
    """Configuration helper class.

    It starts empty, and then the config can be set at any time.
    """
    def load_file(self, filename):
        """Set the configuration from a YAML file."""
        with open(filename, "rt", encoding="utf8") as fh:
            cfg = yaml.safe_load(fh)
        self.update(cfg)


config = Config()

LANGUAGES = {
    'en': u'English',
    'es': u'Español',
}
