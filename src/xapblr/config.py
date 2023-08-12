from importlib.resources import files
from json import load, JSONDecodeError
from pathlib import Path
import sys

from .utils import get_xdg_config_home


class Config:
    def __init__(self):
        config_dir = get_xdg_config_home() / "xapblr"
        config_file = config_dir / "config.json"
        key_file = config_dir / "APIKEY"

        # Load default configuration
        with files("xapblr").joinpath("config.json").open() as f:
            self._config = load(f)

        try:
            with key_file.open() as f:
                self._config["api_key"] = load(f)
        except IOError as e:
            print(f"Could not read API key from {key_file}: {e}", file=sys.stderr)
        except JSONDecodeError as e:
            # Don't need to exit, we could get a valid config from config.json
            print(f"Malformed JSON in {key_file}: {e}", file=sys.stderr)

        try:
            with config_file.open() as f:
                cfg = load(f)
                self._config.update(cfg)
        except IOError as e:
            print(f"Could not read config from {key_file}: {e}", file=sys.stderr)
        except JSONDecodeError as e:
            sys.exit(f"Malformed JSON in {config_file}: {e}")

    def __getitem__(self, key):
        return self._config[key]
    def get(self, key, default=None):
        return self._config.get(key, default)


config = Config()
