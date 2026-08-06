from __future__ import annotations

from datetime import datetime
from typing import Any

from backend.app.models.agent_activity import (
    ActivityStatus,
    AgentActivity,
    AgentName,
)
from backend.app.repositories.agent_activity import AgentActivityRepository


class AgentActivityService:
    """
    Application service for Relay's append-only investigation audit trail.
    """

    def __init__(
        self,
        repository: AgentActivityRepository,
    ) -> None:
        self.repository = repository

    async def record(
        self,
        *,
        investigation_id: str,
        agent_name: AgentName,
        event_type: str,
        status: ActivityStatus,
        message: str,
        structured_payload: dict[str, Any] | None = None,
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
        duration_ms: int | None = None,
    ) -> AgentActivity:
        """
        Append one immutable activity event to an investigation.
        """

        clean_event_type = event_type.strip()
        clean_message = message.strip()

        if not clean_event_type:
            raise ValueError("Activity event_type cannot be empty.")

        if not clean_message:
            raise ValueError("Activity message cannot be empty.")

        if duration_ms is not None and duration_ms < 0:
            raise ValueError("Activity duration_ms cannot be negative.")

        return await self.repository.create(
            investigation_id=investigation_id,
            agent_name=agent_name,
            event_type=clean_event_type,
            status=status,
            message=clean_message,
            structured_payload=structured_payload,
            started_at=started_at,
            completed_at=completed_at,
            duration_ms=duration_ms,
        )

    async def list_for_investigation(
        self,
        investigation_id: str,
    ) -> list[AgentActivity]:
        """
        Return the investigation audit trail in chronological order.
        """

        return await self.repository.list_for_investigation(
            investigation_id
        )