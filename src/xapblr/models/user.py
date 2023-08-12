from enum import StrEnum
from flask_login import UserMixin
from hashlib import sha256
from secrets import token_hex

from sqlalchemy import ForeignKey, String, select
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional

from ..db import get_db
from .base import Base
from .invite import Invite
from .application import Application

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
        Base.__init__(self, **kwargs)
        self.salt = token_hex()
        self.password = self.salt_hash_and_digest(kwargs["password"])

    def salt_hash_and_digest(self, password):
        salted = f"{password}!{self.salt}"
        return sha256(salted.encode("utf8")).hexdigest()

    def get_id(self):
        return str(self.id)

    def get(id):
        id = int(id)
        db = get_db()
        with db.session() as s:
            q = select(User).where(User.id == id)
            try:
                return s.scalars(q).__next__()
            except StopIteration:
                return None
