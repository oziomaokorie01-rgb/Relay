from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, Enum, Float, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.database.base import Base


def utc_now() -> datetime:
    """
    Return the current UTC time as a timezone-aware datetime.
    """

    return datetime.now(timezone.utc)


class EvidenceType(str, enum.Enum):
    SCHEMA_CHANGE = "schema_change"
    LINEAGE_DEPENDENCY = "lineage_dependency"
    FRESHNESS_FAILURE = "freshness_failure"
    QUALITY_FAILURE = "quality_failure"
    OWNERSHIP_SIGNAL = "ownership_signal"
    GOVERNANCE_RULE = "governance_rule"
    PREVIOUS_MEMORY = "previous_memory"
    QUERY_RESULT = "query_result"
    DOCUMENTATION = "documentation"
    MANUAL_CONTEXT = "manual_context"


class Evidence(Base):
    """
    A structured, traceable evidence item discovered during an investigation.
    """

    __tablename__ = "evidence"

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

    type: Mapped[EvidenceType] = mapped_column(
        Enum(
            EvidenceType,
            name="evidence_type",
            native_enum=False,
        ),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    source_asset_urn: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        index=True,
    )

    source_reference: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    payload: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    created_by_agent: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default="investigator",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    def __repr__(self) -> str:
        return (
            f"<Evidence id={self.id!r} "
            f"investigation_id={self.investigation_id!r} "
            f"type={self.type.value!r}>"
        )