"""Comment model for examples."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .post import Post
    from .user import User


class Comment(Base):
    """Comment model with relationships to User and Post."""

    content: Mapped[str] = mapped_column(Text, nullable=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"), nullable=False, index=True)

    # Relationships
    author: Mapped["User"] = relationship("User", back_populates="comments", lazy="select")
    post: Mapped["Post"] = relationship("Post", back_populates="comments", lazy="select")

    def __repr__(self) -> str:
        return f"<Comment(id={self.id}, author_id={self.author_id}, post_id={self.post_id})>"
