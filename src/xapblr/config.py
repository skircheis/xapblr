from json import load, JSONDecodeError
from pathlib import Path
import sys

from .utils import get_xdg_config_home


class Config:
    def __init__(self):
        config_dir = get_xdg_config_home() / "xapblr"
        config_file = config_dir / "config.json"
        key_file = config_dir / "APIKEY"
        self._config = {}
        try:
            with key_file.open() as f:
                self._config["api_key"] = load(f)
        except IOError as e:
            print(stderr, f"Could not read API key from {key_file}: {e}")
        except JSONDecodeError as e:
            print(stderr, f"Malformed JSON in {key_file}: {e}")

        try:
            with config_file.open() as f:
                cfg = load(f)
                self._config.update(cfg)
        except IOError as e:
            print(stderr, f"Could not read API key from {key_file}: {e}")
        except JSONDecodeError as e:
            sys.exit(f"Malformed JSON in {config_file}: {e}")

    def __getitem__(self, key):
        return self._config[key]


config = Config()
