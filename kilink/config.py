# -*- coding: utf8 -*-

"""Config management."""

import os.path
import yaml
from jinja2 import Template


class Config(dict):
    """Configuration helper class.

    It starts empty, and then the config can be set at any time.

    """
    # Copy or symlink your settings file in this location:
    filename = "configs/active.yaml"

    def __init__(self, filename=None, *args, **kwargs):
        """
        Initialize a config object. Will read the file given as first
        argument or "configs/active.yaml" by default.
        Any other keyword argument will be stored in the instance.

        """
        if filename is not None:
            self.filename = filename
        # cache stuff
        self._files_seen = {}
        super(Config, self).__init__(*args, **kwargs)

    def load(self, filename=None, store=True, reload=True, interpolate=True):
        """
        Calls load_file with the given arguments.

        """
        return self.load_file(filename or self.filename,
                              store=store, reload=reload,
                              interpolate=interpolate)

    @staticmethod
    def expand_path(path):
        """
        Returns the expanded version of a path containing ~ or shell
        variables; e.g.: `~/foo/bar` or `$FOO/bar`.

        """
        return os.path.expanduser(os.path.expandvars(path))

    def load_file(self, filename, store=True, reload=False, interpolate=True):
        """
        Get the configuration from a YAML file, possibly extending
        others.

        Variable interpolation is on by default, to disable it use
        interpolate=False. The result is stored in the instance, to
        prevent this, use store=False. The data of each yaml file in
        the extension chain is also cached in the instance use
        reload=True to force reading from disk.

        """
        path = self.expand_path(filename)
        if reload or path not in self._files_seen:
            with open(path, "rt") as fh:
                cfg = yaml.load(fh.read())

            extends = cfg.pop('extends', None)
            if extends:
                base_path = self.expand_path(extends)
                base_root = os.path.dirname(filename)
                base_cfg = self.load_file(os.path.join(base_root, base_path),
                                          store=False, reload=reload,
                                          interpolate=False)
                base_cfg.update(cfg)
                cfg = base_cfg

            if interpolate:
                # Note that if we are here, we have already walked the
                # entire extension chain.
                cfg = self.interpolate(cfg)

            self._files_seen[path] = cfg
        else:
            cfg = self._files_seen[path]

        if store:
            self.update(cfg)

        return cfg

    @staticmethod
    def interpolate(cfg):
        """
        Variable interpolation allows values to refer themselves using
        Jinja syntax. e.g:

            db_name: kilink
            db_engine: sqlite:///tmp/{{ db_name }}.db

        This is done by dumping the config to an intermediate template,
        then parsing it with Jinja, using the config as context.

        """
        return yaml.load(Template(yaml.dump(cfg)).render(**cfg))

config = Config()

LANGUAGES = {
    'en': u'English',
    'es': u'Español',
}
