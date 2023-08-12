from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from .config import config
from .models.base import Base
from .utils import get_data_dir


class Database:
    def __init__(self, echo=False):
        # db_path needs to be absolute so we known the right number of slashes to use on the next line
        # see https://docs.sqlalchemy.org/en/13/core/engines.html#sqlite
        db_path = (get_data_dir() / "xapblr.sqlite3").resolve()
        self.engine = create_engine(f"sqlite:///{db_path}", echo=echo)
        Base.metadata.create_all(self.engine)

    def session(self):
        return Session(self.engine)

def get_db():
    return Database(echo=config.get("debug", False))
