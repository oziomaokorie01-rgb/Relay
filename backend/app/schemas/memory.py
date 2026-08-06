from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from backend.app.models.memory import MemoryVerificationStatus


class MemoryResponse(BaseModel):
    """
    API representation of one Relay organizational memory.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str
    memory_key: str
    version: int
    originating_investigation_id: str
    primary_asset_urn: str

    title: str
    summary: str
    incident_type: str
    root_cause: str
    resolution: str

    confidence: float
    verification_status: MemoryVerificationStatus

    keywords: list[str]
    related_asset_urns: list[str]
    evidence_ids: list[str]

    supersedes_memory_id: str | None

    created_at: datetime
    updated_at: datetime
    verified_at: datetime | None


class InvestigationArchiveResponse(BaseModel):
    """
    Response returned after the Archivist completes memory creation.
    """

    investigation_id: str
    investigation_status: str
    memory: MemoryResponse