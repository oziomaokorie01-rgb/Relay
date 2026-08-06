from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from.app.database.base import Base


def utc_now() -> datetime:
    """
    Return the current UTC time as a timezone-aware datetime.
    """

    return datetime.now(timezone.utc)


class HumanApprovalDecision(str, enum.Enum):
    APPROVE = "approve"
    REQUEST_REVISION = "request_revision"
    REJECT = "reject"


class HumanApproval(Base):
    """
    An explicit human decision made after Reviewer validation.
    """

    __tablename__ = "human_approvals"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    investigation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("investigations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    review_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("reviews.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    decision: Mapped[HumanApprovalDecision] = mapped_column(
        Enum(
            HumanApprovalDecision,
            name="human_approval_decision",
            native_enum=False,
        ),
        nullable=False,
        index=True,
    )

    edited_title: Mapped[str | None] = mapped_column(
        String(240),
        nullable=True,
    )

    edited_summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    approved_by: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
        default="hackathon-user",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    def __repr__(self) -> str:
        return (
            f"<HumanApproval id={self.id!r} "
            f"investigation_id={self.investigation_id!r} "
            f"decision={self.decision.value!r}>"
        )