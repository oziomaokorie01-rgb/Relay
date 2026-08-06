from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from.app.models.memory_reuse_event import MemoryReuseType


class MemoryReuseEventResponse(BaseModel):
    """
    API representation of one verified-memory inheritance event.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str
    memory_id: str
    investigation_id: str

    similarity_score: float | None
    reuse_type: MemoryReuseType
    agent_explanation: str
    accepted: bool

    estimated_steps_skipped: int
    estimated_time_saved_minutes: int

    created_at: datetime