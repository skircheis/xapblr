from json import load
from os import environ
from pathlib import Path

from xapian import Database, WritableDatabase, DB_CREATE_OR_OPEN

def get_api_key():
    key_fname = "APIKEY"
    xdg_config_home = Path(environ["XDG_CONFIG_HOME"])
    key_file = xdg_config_home / "xapblr" / key_fname
    with key_file.open() as f:
        return load(f)

def get_db(blog, mode="r"):
    # returns a xapian database object for the specified blog
    # mode = 'r' for reading, 'w' for writing
    try:
        xdg_data_home = Path(environ["XDG_DATA_HOME"])
    except KeyError:
        xdg_data_home = Path(environ["HOME"]) / ".local/share"
    db_path = xdg_data_home / "xapblr" / blog
    db_path.mkdir(parents=True, exist_ok=True)
    db_path_str = str(db_path)
    if mode == "w":
        return WritableDatabase(db_path_str, DB_CREATE_OR_OPEN)
    else:
        return Database(db_path_str, DB_CREATE_OR_OPEN)

from datetime import datetime

try:
    import humanfriendly

    def format_timestamp(ts):
        now = datetime.now()
        ts = datetime.fromtimestamp(ts)
        return humanfriendly.format_timespan(now - ts) + " ago"

except ModuleNotFoundError:

    def format_timestamp(ts):
        # Format datetime according to current locale
        return datetime.frotsstamp(mtime).strftime("%c%")

