from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from backend.app.models.evidence import EvidenceType


class EvidenceResponse(BaseModel):
    """
    API representation of one persisted investigation evidence record.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str
    investigation_id: str
    type: EvidenceType
    title: str
    description: str
    source_asset_urn: str | None
    source_reference: str | None
    confidence: float
    payload: dict[str, Any]
    created_by_agent: str
    created_at: datetime