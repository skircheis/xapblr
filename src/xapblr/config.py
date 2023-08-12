from importlib.resources import files
from json import load, JSONDecodeError
from pathlib import Path
from sys import exit, stderr

from .utils import get_xdg_config_home

# Copied from pydantic.utils
# https://github.com/pydantic/pydantic/blob/main/pydantic/_internal/_utils.py
def deep_update(mapping, *updating_mappings):
    updated_mapping = mapping.copy()
    for updating_mapping in updating_mappings:
        for k, v in updating_mapping.items():
            if k in updated_mapping and isinstance(updated_mapping[k], dict) and isinstance(v, dict):
                updated_mapping[k] = deep_update(updated_mapping[k], v)
            else:
                updated_mapping[k] = v
    return updated_mapping

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
                self._config = deep_update(self._config, cfg)
        except IOError as e:
            print(f"Could not read config from {key_file}: {e}", file=sys.stderr)
        except JSONDecodeError as e:
            sys.exit(f"Malformed JSON in {config_file}: {e}")

    def __getitem__(self, key):
        return self._config[key]
    def get(self, key, default=None):
        return self._config.get(key, default)

config = Config()
