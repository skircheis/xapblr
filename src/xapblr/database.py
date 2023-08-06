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


class Base(DeclarativeBase):
    pass


class Blog(Base):
    __tablename__ = "blogs"
    id: Mapped[int] = mapped_column(primary_key=True)
    url: Mapped[str]
    added: Mapped[int]

    added_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    added_by: Mapped[Optional["User"]] = relationship()


class User(Base, UserMixin):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30))
    email: Mapped[str]
    password: Mapped[str]
    salt: Mapped[str]
    registered: Mapped[int]
    last_seen: Mapped[Optional[int]]
    max_invites: Mapped[int]

    privilege_id: Mapped[int] = mapped_column(ForeignKey("privileges.id"))
    privilege: Mapped["Privilege"] = relationship()

    status_id: Mapped[int] = mapped_column(ForeignKey("statuses.id"))
    status: Mapped["Status"] = relationship()

    invite_id: Mapped[Optional[int]] = mapped_column(ForeignKey("invites.id"))
    invite: Mapped[Optional["Invite"]] = relationship(foreign_keys=[invite_id])

    application_id: Mapped[Optional[int]] = mapped_column(ForeignKey("applications.id"))
    application: Mapped[Optional["Application"]] = relationship(
        "Application", foreign_keys=[application_id]
    )

    def __init__(self, **kwargs):
        Base.__init__(**kwargs)
        self.salt = token_hex()
        self.password = self.salt_hash_and_digest(kwargs["password"])

    def salt_hash_and_digest(self, password):
        salted = f"{password}!{self.salt}"
        return sha256(salted.encode("utf8")).hexdigest()

    def get_id(self):
        return str(self.id)

    def get(id):
        id = int(id)
        with db.session() as s:
            q = select(User).where(User.id == id)
            try:
                return s.scalars(q).__next__()
            except StopIteration:
                return None


StatusE = StrEnum(
    "StatusE",
    [
        "ACTIVE",
        "BANNED",
        "APPLICATION_SUBMITTED",
        "APPLICATION_CONFIRMED",
    ],
)

PrivilegeE = StrEnum("Privilege", ["ROOT", "ADMIN", "USER"])


class Privilege(Base):
    __tablename__ = "privileges"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]


class Status(Base):
    __tablename__ = "statuses"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]


class Invite(Base):
    __tablename__ = "invites"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str]
    sent: Mapped[int]
    lifetime: Mapped[int]
    email: Mapped[str]

    inviter_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    inviter: Mapped["User"] = relationship(foreign_keys=[inviter_id])

    invitee_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    invitee: Mapped[Optional["User"]] = relationship(foreign_keys=[invitee_id])


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


class Application(Base):
    __tablename__ = "applications"
    id: Mapped[int] = mapped_column(primary_key=True)
    submitted: Mapped[int]

    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    user: Mapped[Optional["User"]] = relationship(foreign_keys=[user_id])
    body: Mapped[str]


def now():
    return datetime.now().timestamp()


def now_int():
    return int(now())


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

    def create_db(self):
        statuses = {k: Status(name=k) for k in StatusE}
        privileges = {k: Privilege(name=k) for k in PrivilegeE}
        default_account = User(
            name="admin",
            password="password",
            email="admin@xapblr.io",
            registered=now_int(),
            last_seen=None,
            max_invites=0,
            status=statuses[StatusE.ACTIVE],
            privilege=privileges[PrivilegeE.ROOT],
        )

        with Session(self.engine) as s:
            Base.metadata.create_all(self.engine)
            s.add_all(statuses.values())
            s.add_all(privileges.values())
            s.add(default_account)
            s.commit()


db = Database()
