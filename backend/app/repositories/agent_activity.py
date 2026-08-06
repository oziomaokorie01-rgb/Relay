from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from.app.models.agent_activity import (
    ActivityStatus,
    AgentActivity,
    AgentName,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AgentActivityRepository:
    """
    Persistence layer for Relay investigation activity events.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
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
        activity = AgentActivity(
            investigation_id=investigation_id,
            agent_name=agent_name,
            event_type=event_type,
            status=status,
            message=message,
            structured_payload=structured_payload or {},
            started_at=started_at or utc_now(),
            completed_at=completed_at,
            duration_ms=duration_ms,
        )

        self.session.add(activity)
        await self.session.commit()
        await self.session.refresh(activity)

        return activity

    async def list_for_investigation(
        self,
        investigation_id: str,
    ) -> list[AgentActivity]:
        statement = (
            select(AgentActivity)
            .where(
                AgentActivity.investigation_id == investigation_id
            )
            .order_by(AgentActivity.started_at.asc())
        )

        result = await self.session.execute(statement)

        return list(result.scalars().all())