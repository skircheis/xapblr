from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional

from .base import Base


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
