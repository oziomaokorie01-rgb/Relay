from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from backend.app.models.repair_proposal import (
    RepairArtifactType,
    RepairProposalStatus,
    RepairRiskLevel,
)


class RepairProposalResponse(BaseModel):
    """
    API representation of one persisted repair proposal.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str
    investigation_id: str
    summary: str

    artifact_type: RepairArtifactType
    artifact_content: str | None
    language: str | None

    risk_level: RepairRiskLevel
    expected_outcome: str
    rollback_plan: str | None

    affected_asset_urns: list[str]
    tests: list[dict[str, Any]]
    assumptions: list[str]
    evidence_ids: list[str]

    confidence: float
    status: RepairProposalStatus
    created_at: datetime