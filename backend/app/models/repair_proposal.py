from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, Enum, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


def utc_now() -> datetime:
    """
    Return the current UTC time as a timezone-aware datetime.
    """

    return datetime.now(timezone.utc)


class RepairArtifactType(str, enum.Enum):
    SQL = "sql"
    DBT_MODEL = "dbt_model"
    DATA_QUALITY_TEST = "data_quality_test"
    CONFIGURATION = "configuration"
    PIPELINE_PATCH = "pipeline_patch"
    DOCUMENTATION = "documentation"
    RUNBOOK = "runbook"
    RECOMMENDATION_ONLY = "recommendation_only"


class RepairRiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RepairProposalStatus(str, enum.Enum):
    DRAFT = "draft"
    PROPOSED = "proposed"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    NEEDS_REVISION = "needs_revision"
    REJECTED = "rejected"


class RepairProposal(Base):
    """
    A structured repair recommendation generated for an investigation.
    """

    __tablename__ = "repair_proposals"

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

    summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    artifact_type: Mapped[RepairArtifactType] = mapped_column(
        Enum(
            RepairArtifactType,
            name="repair_artifact_type",
            native_enum=False,
        ),
        nullable=False,
    )

    artifact_content: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    language: Mapped[str | None] = mapped_column(
        String(40),
        nullable=True,
    )

    risk_level: Mapped[RepairRiskLevel] = mapped_column(
        Enum(
            RepairRiskLevel,
            name="repair_risk_level",
            native_enum=False,
        ),
        nullable=False,
    )

    expected_outcome: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    rollback_plan: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    affected_asset_urns: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    tests: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    assumptions: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    evidence_ids: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    confidence: Mapped[float] = mapped_column(
        nullable=False,
    )

    status: Mapped[RepairProposalStatus] = mapped_column(
        Enum(
            RepairProposalStatus,
            name="repair_proposal_status",
            native_enum=False,
        ),
        nullable=False,
        default=RepairProposalStatus.PROPOSED,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    def __repr__(self) -> str:
        return (
            f"<RepairProposal id={self.id!r} "
            f"investigation_id={self.investigation_id!r} "
            f"status={self.status.value!r}>"
        )