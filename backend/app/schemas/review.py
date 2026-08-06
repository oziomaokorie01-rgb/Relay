from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from backend.app.models.review import ReviewDecision


class ReviewResponse(BaseModel):
    """
    API representation of one persisted Reviewer decision.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str
    investigation_id: str
    repair_proposal_id: str
    decision: ReviewDecision

    evidence_coverage: dict[str, Any]
    schema_compatibility: dict[str, Any]
    downstream_risk: dict[str, Any]
    governance_compliance: dict[str, Any]

    confidence: float
    conditions: list[str]
    missing_evidence: list[str]
    notes: str | None
    created_at: datetime
