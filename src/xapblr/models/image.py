from typing import List, Optional
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from enum import StrEnum, auto

from .base import Base


class ImageState(StrEnum):
    AVAILABLE = auto()
    ASSIGNED = auto()
    CAPTIONED = auto()


class Image(Base):
    __tablename__ = "images"

    id: Mapped[int] = mapped_column(primary_key=True)
    media_key: Mapped[str] = mapped_column(unique=True)
    url: Mapped[str]
    state: Mapped[ImageState]
    created: Mapped[int]
    assigned: Mapped[Optional[int]]
    agent: Mapped[Optional[str]]
    captioned: Mapped[Optional[int]]
    caption: Mapped[Optional[str]]

    posts: Mapped[List["ImageInPost"]] = relationship(back_populates="image")


class ImageInPost(Base):
    __tablename__ = "images_in_posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    image_id: Mapped[int] = mapped_column(ForeignKey("images.id"))
    image: Mapped["Image"] = relationship(back_populates="posts")
    post_id: Mapped[int]
    blog: Mapped[str]

    __table_args__ = (
        UniqueConstraint("image_id", "post_id", "blog", name="_uniqueness"),
    )

    def __repr__(self):
        return f"ImageInPost({self.blog}, {self.post_id}, {self.image_id})"
