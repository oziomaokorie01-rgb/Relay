from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, Enum, Float, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from.app.database.base import Base


def utc_now() -> datetime:
    """
    Return the current UTC time as a timezone-aware datetime.
    """

    return datetime.now(timezone.utc)


class InvestigationStatus(str, enum.Enum):
    DRAFT = "draft"
    QUEUED = "queued"
    GATHERING_CONTEXT = "gathering_context"
    INVESTIGATING = "investigating"
    REPAIRING = "repairing"
    REVIEWING = "reviewing"
    AWAITING_APPROVAL = "awaiting_approval"
    ARCHIVING = "archiving"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class InvestigationPriority(str, enum.Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class Investigation(Base):
    """
    Represents one reported data incident and its complete Relay workflow.
    """

    __tablename__ = "investigations"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    asset_urn: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        index=True,
    )

    priority: Mapped[InvestigationPriority] = mapped_column(
        Enum(
            InvestigationPriority,
            name="investigation_priority",
            native_enum=False,
        ),
        nullable=False,
        default=InvestigationPriority.NORMAL,
    )

    status: Mapped[InvestigationStatus] = mapped_column(
        Enum(
            InvestigationStatus,
            name="investigation_status",
            native_enum=False,
        ),
        nullable=False,
        default=InvestigationStatus.DRAFT,
        index=True,
    )

    current_agent: Mapped[str | None] = mapped_column(
        String(40),
        nullable=True,
    )

    context_snapshot: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    root_cause_summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    overall_confidence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    failure_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def __repr__(self) -> str:
        return (
            f"<Investigation id={self.id!r} "
            f"title={self.title!r} "
            f"status={self.status.value!r}>"
        )