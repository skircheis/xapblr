from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional

from .base import Base


class Blog(Base):
    __tablename__ = "blogs"
    id: Mapped[int] = mapped_column(primary_key=True)
    url: Mapped[str]
    added: Mapped[int]

    added_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    added_by: Mapped[Optional["User"]] = relationship()
