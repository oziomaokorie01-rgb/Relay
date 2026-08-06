from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from backend.app.models.agent_activity import (
    ActivityStatus,
    AgentName,
)


class AgentActivityResponse(BaseModel):
    """
    API representation of one investigation audit event.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str
    investigation_id: str
    agent_name: AgentName
    event_type: str
    status: ActivityStatus
    message: str
    structured_payload: dict[str, Any]
    started_at: datetime
    completed_at: datetime | None
    duration_ms: int | None