# Copyright 2011-2021 Facundo Batista, Nicolás César
# All Rigths Reserved

"""Config management."""

import os
import yaml

from sqlalchemy import create_engine

ENVIRONMENT_KEY = "environment"
PROD_ENVIRONMENT_VALUE = "prod"
UNITTESTING_ENVIRONMENT_VALUE = "unittesting"

DB_ENGINE_INSTANCE_KEY = "db_engine_instance"


class Config(dict):
    """Configuration helper class.

    It starts empty, and then the config can be set at any time.
    """

    def load_file(self, filename):
        """Set the configuration from a YAML file."""
        with open(filename, "rt", encoding="utf8") as fh:
            cfg = yaml.safe_load(fh)
        self.update(cfg)

    def load_config(self, environment=PROD_ENVIRONMENT_VALUE):
        """Load the config."""
        if environment == PROD_ENVIRONMENT_VALUE:
            self.load_file("/home/kilink/project/production/configs/production.yaml")
            db_engine = self._prod_database_engine()

        elif environment == UNITTESTING_ENVIRONMENT_VALUE:
            self.load_file("configs/development.yaml")
            db_engine = self._unittesting_database_engine()

        else:
            # defaults to dev environment
            self.load_file("configs/development.yaml")
            db_engine = self._dev_database_engine()

        self.update({ENVIRONMENT_KEY: environment, DB_ENGINE_INSTANCE_KEY: db_engine})

    def _prod_database_engine(self):
        auth_config = self.get("db_auth_config")
        auth_file = os.path.abspath(os.path.join(os.path.dirname(__file__), auth_config))
        with open(auth_file) as fh:
            vals = [x.strip() for x in fh.readlines()]
        auth_data = dict(zip(("user", "pass"), vals))
        engine_data = self.get("db_engine").format(**auth_data)

        return create_engine(engine_data)

    def _dev_database_engine(self):
        return create_engine(self.get("db_engine"), echo=True)

    def _unittesting_database_engine(self):
        return create_engine("sqlite://")


config = Config()

LANGUAGES = {
    'en': u'English',
    'es': u'Español',
}
