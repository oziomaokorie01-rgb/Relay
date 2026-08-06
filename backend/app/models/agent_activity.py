from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from.app.database.base import Base


def utc_now() -> datetime:
    """
    Return the current UTC time as a timezone-aware datetime.
    """

    return datetime.now(timezone.utc)


class AgentName(str, enum.Enum):
    SYSTEM = "system"
    INVESTIGATOR = "investigator"
    REPAIR = "repair"
    REVIEWER = "reviewer"
    ARCHIVIST = "archivist"
    HUMAN = "human"


class ActivityStatus(str, enum.Enum):
    QUEUED = "queued"
    STARTED = "started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    WARNING = "warning"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentActivity(Base):
    """
    Immutable audit record describing one action within an investigation.
    """

    __tablename__ = "agent_activity"

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

    agent_name: Mapped[AgentName] = mapped_column(
        Enum(
            AgentName,
            name="agent_name",
            native_enum=False,
        ),
        nullable=False,
        default=AgentName.SYSTEM,
        index=True,
    )

    event_type: Mapped[str] = mapped_column(
        String(60),
        nullable=False,
        index=True,
    )

    status: Mapped[ActivityStatus] = mapped_column(
        Enum(
            ActivityStatus,
            name="activity_status",
            native_enum=False,
        ),
        nullable=False,
        default=ActivityStatus.STARTED,
    )

    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    structured_payload: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    duration_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    def __repr__(self) -> str:
        return (
            f"<AgentActivity id={self.id!r} "
            f"investigation_id={self.investigation_id!r} "
            f"agent={self.agent_name.value!r} "
            f"event_type={self.event_type!r}>"
        )