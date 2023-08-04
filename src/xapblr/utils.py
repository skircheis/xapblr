from datetime import datetime
from json import load
from os import environ
from pathlib import Path
from re import sub

from xapian import Database, WritableDatabase, DatabaseNotFoundError, DB_CREATE_OR_OPEN

prefixes = {
    "content": "XC",
    "op": "XOP",
    "author": "A",
    "id": "Q",
    "tag": "K",
    "url": "U",
    "timestamp": "D",
    "link": "XL",
}

value_slots = {
    "timestamp": 0,
}


def get_api_key():
    key_fname = "APIKEY"
    xdg_config_home = Path(environ["XDG_CONFIG_HOME"])
    key_file = xdg_config_home / "xapblr" / key_fname
    with key_file.open() as f:
        return load(f)


def get_db_dir():
    try:
        xdg_data_home = Path(environ["XDG_DATA_HOME"])
    except KeyError:
        xdg_data_home = Path(environ["HOME"]) / ".local/share"
    return xdg_data_home / "xapblr"


def get_db(blog, mode="r"):
    # returns a xapian database object for the specified blog
    # mode = 'r' for reading, 'w' for writing
    db_path = get_db_dir() / blog
    db_path.mkdir(parents=True, exist_ok=True)
    db_path_str = str(db_path)
    if mode == "w":
        return WritableDatabase(db_path_str, DB_CREATE_OR_OPEN)
    else:
        try:
            return Database(db_path_str, DB_CREATE_OR_OPEN)
        except DatabaseNotFoundError:
            # if the database does not already exist, it must be created
            # writable
            db = WritableDatabase(db_path_str, DB_CREATE_OR_OPEN)
            db.close()
            return Database(db_path_str, DB_CREATE_OR_OPEN)


def get_author(post):
    try:
        return post["blog"]["name"]
    except KeyError:
        return post["broken_blog_name"]


def encode_tag(tag):
    # xapian will never put a space in a term but we can just urlencode
    # take the first 245 bytes since that's the max xapian term length
    return (prefixes["tag"] + urlencode(tag.lower()))[:245]


def fix_date_range(d):
    def _fix(m):
        return m[0].replace(" ", "_")

    return sub('date:(".*"|.*)?\\.\\.(".*"|.*)?', _fix, d)


try:
    import humanfriendly

    def format_timestamp(ts):
        now = datetime.now()
        ts = datetime.fromtimestamp(ts)
        if (ts - now).total_seconds() > 0:
            hf = humanfriendly.format_timespan(ts - now)
            return f"in {hf}"
        else:
            hf = humanfriendly.format_timespan(now - ts)
            return f"{hf} ago"

except ModuleNotFoundError:

    def format_timestamp(ts):
        # Format datetime according to current locale
        return datetime.fromtimestamp(ts).strftime("%c")
