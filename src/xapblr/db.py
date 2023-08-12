from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from .config import config
from .models.base import Base
from .utils import get_db_dir

class Database:
    def __init__(self, echo=False):
        db_path = (get_db_dir() / "xapblr.sqlite3").resolve()
        self.engine = create_engine(f"sqlite:///{db_path}", echo=echo)
        if not db_path.exists():
            print(
                f"Database file {db_path} does not exist. Creating and populating... ",
                end="",
            )
            Base.metadata.create_all(self.engine)
            print("Done.")

    def session(self):
        return Session(self.engine)

db = Database(echo=config.get("debug", False))
