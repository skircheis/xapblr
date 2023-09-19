from xapian import (
    Database,
    WritableDatabase,
    DatabaseError,
    DatabaseNotFoundError,
    DB_CREATE_OR_OPEN,
)
from .utils import get_data_dir


class BlogIndex:
    # Context manager wrapping a xapian (Writable)Database
    def __init__(self, url, mode="r"):
        self.url = url
        self.mode = mode
        self.db_path = get_data_dir() / url
        self.db = None

    def get_db(self):
        if self.db:
            try:
                # Test to see if the db has been closed
                self.db.reopen()
            except DatabaseError:
                # If so we need to reopen it by recreating the object and its file handles
                pass
            else:
                # Otherwise we're good
                return self.db

        self.db_path.mkdir(parents=True, exist_ok=True)
        db_path_str = str(self.db_path)
        if self.mode == "w":
            self.db = WritableDatabase(db_path_str, DB_CREATE_OR_OPEN)
        else:
            try:
                self.db = Database(db_path_str, DB_CREATE_OR_OPEN)
            except DatabaseNotFoundError:
                # if the database does not already exist, it must be created
                # writable
                self.db = WritableDatabase(db_path_str, DB_CREATE_OR_OPEN)
                self.db.close()
                self.db = Database(db_path_str, DB_CREATE_OR_OPEN)

        return self.db

    __enter__ = get_db

    def __exit__(self, type, value, traceback):
        self.db.close()
