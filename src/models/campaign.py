"""Campaign model for examples."""

from typing import TYPE_CHECKING

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .application import Application


class Campaign(Base):
    """Campaign model that users can apply to."""

    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False, index=True)
    max_participants: Mapped[int | None] = mapped_column(default=None)

    # Relationships
    applications: Mapped[list["Application"]] = relationship(
        "Application", back_populates="campaign", cascade="all, delete-orphan", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<Campaign(id={self.id}, title='{self.title}', is_active={self.is_active})>"
