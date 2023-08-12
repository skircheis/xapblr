from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class EmailChange(Base):
    __tablename__ = "email_changes"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str]
    sent: Mapped[int]
    lifetime: Mapped[int]

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped["User"] = relationship()
    new_email: Mapped[str]
