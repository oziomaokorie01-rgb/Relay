from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, Enum, Float, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


def utc_now() -> datetime:
    """
    Return the current UTC time as a timezone-aware datetime.
    """

    return datetime.now(timezone.utc)


class ReviewDecision(str, enum.Enum):
    APPROVED = "approved"
    APPROVED_WITH_CONDITIONS = "approved_with_conditions"
    NEEDS_REVISION = "needs_revision"
    REJECTED = "rejected"


class Review(Base):
    """
    A persisted Reviewer decision for one repair proposal.
    """

    __tablename__ = "reviews"

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

    repair_proposal_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("repair_proposals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    decision: Mapped[ReviewDecision] = mapped_column(
        Enum(
            ReviewDecision,
            name="review_decision",
            native_enum=False,
        ),
        nullable=False,
        index=True,
    )

    evidence_coverage: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
    )

    schema_compatibility: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
    )

    downstream_risk: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
    )

    governance_compliance: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
    )

    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    conditions: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    missing_evidence: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    def __repr__(self) -> str:
        return (
            f"<Review id={self.id!r} "
            f"investigation_id={self.investigation_id!r} "
            f"decision={self.decision.value!r}>"
        )