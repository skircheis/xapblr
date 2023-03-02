from os import environ
from pathlib import Path

def get_data_dir():
    try:
        xdg_data_home = Path(environ["XDG_DATA_HOME"])
    except KeyError:
        xdg_data_home = Path(environ["HOME"]) / ".local/share"
    return xdg_data_home / "xapblr"


