from datetime import datetime
from enum import StrEnum
from flask_login import UserMixin
from hashlib import sha256
from typing import List, Optional
from secrets import token_hex
from sqlalchemy import create_engine, select, Column, ForeignKey, String
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    Session,
)

from .utils import get_data_dir


class Blog(Base):
    __tablename__ = "blogs"
    id: Mapped[int] = mapped_column(primary_key=True)
    url: Mapped[str]
    added: Mapped[int]

    added_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    added_by: Mapped[Optional["User"]] = relationship()


class PasswordReset(Base):
    __tablename__ = "password_resets"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str]
    sent: Mapped[int]
    lifetime: Mapped[int]

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped["User"] = relationship()


class EmailChange(Base):
    __tablename__ = "email_changes"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str]
    sent: Mapped[int]
    lifetime: Mapped[int]

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped["User"] = relationship()
    new_email: Mapped[str]


class Database:
    def __init__(self, echo=False):
        # db_path needs to be absolute so we known the right number of slashes to use on the next line
        # see https://docs.sqlalchemy.org/en/13/core/engines.html#sqlite
        db_path = (get_data_dir() / "xapblr.sqlite3").resolve()
        self.engine = create_engine(f"sqlite:///{db_path}", echo=echo)
        if not db_path.exists():
            print(
                f"Database file {db_path} does not exist. Creating and populating... ",
                end="",
            )
            Base.metadata.create_all(self.engine)
            self.create_db()
            print("Done.")

    def session(self):
        return Session(self.engine)



db = Database()
