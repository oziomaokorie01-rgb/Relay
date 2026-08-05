from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


def utc_now() -> datetime:
    """
    Return the current UTC time as a timezone-aware datetime.
    """

    return datetime.now(timezone.utc)


class MemoryReuseType(str, enum.Enum):
    ROOT_CAUSE_PRECEDENT = "root_cause_precedent"
    REPAIR_PRECEDENT = "repair_precedent"
    TEST_PRECEDENT = "test_precedent"
    RELATED_INCIDENT = "related_incident"
    GENERAL_CONTEXT = "general_context"


class MemoryReuseEvent(Base):
    """
    Records how a verified Relay memory was used by a later investigation.
    """

    __tablename__ = "memory_reuse_events"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    memory_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("memories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    investigation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("investigations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    similarity_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    reuse_type: Mapped[MemoryReuseType] = mapped_column(
        String(40),
        nullable=False,
        default=MemoryReuseType.RELATED_INCIDENT,
    )

    agent_explanation: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    accepted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    estimated_steps_skipped: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    estimated_time_saved_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    def __repr__(self) -> str:
        return (
            f"<MemoryReuseEvent id={self.id!r} "
            f"memory_id={self.memory_id!r} "
            f"investigation_id={self.investigation_id!r} "
            f"accepted={self.accepted!r}>"
        )