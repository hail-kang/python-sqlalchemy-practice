"""Post model for examples."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .comment import Comment
    from .user import User


class Post(Base):
    """Post model with relationships to User and Comments."""

    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    is_published: Mapped[bool] = mapped_column(default=False, nullable=False)
    view_count: Mapped[int] = mapped_column(default=0, nullable=False)

    # Relationships
    author: Mapped["User"] = relationship("User", back_populates="posts", lazy="select")
    comments: Mapped[list["Comment"]] = relationship(
        "Comment", back_populates="post", cascade="all, delete-orphan", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<Post(id={self.id}, title='{self.title}', author_id={self.author_id})>"
