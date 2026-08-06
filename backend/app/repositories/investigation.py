from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from.app.models.investigation import (
    Investigation,
    InvestigationStatus,
)
from.app.schemas.investigation import InvestigationCreate


def utc_now() -> datetime:
    """
    Return the current UTC time as a timezone-aware datetime.
    """

    return datetime.now(timezone.utc)


class InvestigationRepository:
    """
    Database access layer for Relay investigations.

    This class contains persistence logic only. Workflow validation and
    business decisions belong in the service and orchestration layers.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        data: InvestigationCreate,
    ) -> Investigation:
        investigation = Investigation(
            title=data.title,
            description=data.description,
            asset_urn=data.asset_urn,
            priority=data.priority,
        )

        self.session.add(investigation)
        await self.session.commit()
        await self.session.refresh(investigation)

        return investigation

    async def get_by_id(
        self,
        investigation_id: str,
    ) -> Investigation | None:
        return await self.session.get(
            Investigation,
            investigation_id,
        )

    async def list_all(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Investigation]:
        statement = (
            select(Investigation)
            .order_by(Investigation.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        result = await self.session.execute(statement)

        return list(result.scalars().all())

    async def update_status(
        self,
        investigation: Investigation,
        *,
        status: InvestigationStatus,
        current_agent: str | None,
        failure_message: str | None = None,
    ) -> Investigation:
        """
        Persist a workflow status transition.

        Transition validity must be checked before this method is called.
        """

        investigation.status = status
        investigation.current_agent = current_agent
        investigation.failure_message = failure_message
        investigation.updated_at = utc_now()

        if status == InvestigationStatus.COMPLETED:
            investigation.completed_at = utc_now()

        if status not in {
            InvestigationStatus.COMPLETED,
            InvestigationStatus.FAILED,
            InvestigationStatus.CANCELLED,
        }:
            investigation.completed_at = None

        await self.session.commit()
        await self.session.refresh(investigation)

        return investigation

    async def update_context_snapshot(
        self,
        investigation: Investigation,
        context_snapshot: dict,
    ) -> Investigation:
        """
        Store the DataHub context captured for an investigation.
        """

        investigation.context_snapshot = context_snapshot
        investigation.updated_at = utc_now()

        await self.session.commit()
        await self.session.refresh(investigation)

        return investigation

    async def update_findings(
        self,
        investigation: Investigation,
        *,
        root_cause_summary: str | None,
        overall_confidence: float | None,
    ) -> Investigation:
        """
        Persist the current investigation findings.
        """

        investigation.root_cause_summary = root_cause_summary
        investigation.overall_confidence = overall_confidence
        investigation.updated_at = utc_now()

        await self.session.commit()
        await self.session.refresh(investigation)

        return investigation