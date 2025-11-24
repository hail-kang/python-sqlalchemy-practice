"""Application model for examples."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .campaign import Campaign
    from .user import User


class ApplicationStatus:
    """Application status constants."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class Application(Base):
    """Application model representing a user's application to a campaign."""

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(20), default=ApplicationStatus.PENDING, nullable=False, index=True
    )
    message: Mapped[str | None] = mapped_column(Text)
    admin_note: Mapped[str | None] = mapped_column(Text)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="applications", lazy="select")
    campaign: Mapped["Campaign"] = relationship(
        "Campaign", back_populates="applications", lazy="select"
    )

    def __repr__(self) -> str:
        return (
            f"<Application(id={self.id}, user_id={self.user_id}, "
            f"campaign_id={self.campaign_id}, status='{self.status}')>"
        )
