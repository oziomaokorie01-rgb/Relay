from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from.app.models.memory_reuse_event import (
    MemoryReuseEvent,
    MemoryReuseType,
)


class MemoryReuseEventRepository:
    """
    Persistence layer for verified-memory reuse events.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        memory_id: str,
        investigation_id: str,
        similarity_score: float,
        reuse_type: MemoryReuseType,
        agent_explanation: str,
        accepted: bool,
        estimated_steps_skipped: int = 0,
        estimated_time_saved_minutes: int = 0,
    ) -> MemoryReuseEvent:
        """
        Persist one memory inheritance event.
        """

        event = MemoryReuseEvent(
            memory_id=memory_id,
            investigation_id=investigation_id,
            similarity_score=similarity_score,
            reuse_type=reuse_type,
            agent_explanation=agent_explanation,
            accepted=accepted,
            estimated_steps_skipped=estimated_steps_skipped,
            estimated_time_saved_minutes=estimated_time_saved_minutes,
        )

        self.session.add(event)
        await self.session.commit()
        await self.session.refresh(event)

        return event

    async def list_for_memory(
        self,
        memory_id: str,
    ) -> list[MemoryReuseEvent]:
        """
        Return all reuse events for one memory.
        """

        statement = (
            select(MemoryReuseEvent)
            .where(MemoryReuseEvent.memory_id == memory_id)
            .order_by(MemoryReuseEvent.created_at.desc())
        )

        result = await self.session.execute(statement)

        return list(result.scalars().all())

    async def list_for_investigation(
        self,
        investigation_id: str,
    ) -> list[MemoryReuseEvent]:
        """
        Return all memories inherited by one investigation.
        """

        statement = (
            select(MemoryReuseEvent)
            .where(
                MemoryReuseEvent.investigation_id == investigation_id
            )
            .order_by(MemoryReuseEvent.created_at.asc())
        )

        result = await self.session.execute(statement)

        return list(result.scalars().all())