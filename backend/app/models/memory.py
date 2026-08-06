from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.database.base import Base


def utc_now() -> datetime:
    """
    Return the current UTC time as a timezone-aware datetime.
    """

    return datetime.now(timezone.utc)


class MemoryVerificationStatus(str, enum.Enum):
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    VERIFIED = "verified"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"
    REJECTED = "rejected"


class RelayMemory(Base):
    """
    Reusable, verified operational knowledge created from an investigation.
    """

    __tablename__ = "memories"

    __table_args__ = (
        UniqueConstraint(
            "memory_key",
            "version",
            name="uq_memories_memory_key_version",
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    memory_key: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
        index=True,
    )

    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    originating_investigation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("investigations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    primary_asset_urn: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(240),
        nullable=False,
    )

    summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    incident_type: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
        index=True,
    )

    root_cause: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    resolution: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    verification_status: Mapped[MemoryVerificationStatus] = mapped_column(
        Enum(
            MemoryVerificationStatus,
            name="memory_verification_status",
            native_enum=False,
        ),
        nullable=False,
        default=MemoryVerificationStatus.VERIFIED,
        index=True,
    )

    keywords: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    related_asset_urns: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    evidence_ids: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    supersedes_memory_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("memories.id", ondelete="SET NULL"),
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

    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=utc_now,
    )

    def __repr__(self) -> str:
        return (
            f"<RelayMemory id={self.id!r} "
            f"memory_key={self.memory_key!r} "
            f"version={self.version!r} "
            f"status={self.verification_status.value!r}>"
        )