from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.evidence import Evidence, EvidenceType
from backend.app.schemas.investigator import InvestigatorEvidence


class EvidenceRepository:
    """
    Persistence layer for investigation evidence.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_many(
        self,
        *,
        investigation_id: str,
        items: list[InvestigatorEvidence],
        created_by_agent: str = "investigator",
    ) -> list[Evidence]:
        """
        Persist multiple evidence records in one transaction.
        """

        records = [
            Evidence(
                investigation_id=investigation_id,
                type=EvidenceType(item.type),
                title=item.title,
                description=item.description,
                source_asset_urn=item.source_asset_urn,
                source_reference=item.source_reference,
                confidence=item.confidence,
                payload={},
                created_by_agent=created_by_agent,
            )
            for item in items
        ]

        self.session.add_all(records)
        await self.session.commit()

        for record in records:
            await self.session.refresh(record)

        return records

    async def list_for_investigation(
        self,
        investigation_id: str,
    ) -> list[Evidence]:
        """
        Return all evidence for an investigation in creation order.
        """

        statement = (
            select(Evidence)
            .where(Evidence.investigation_id == investigation_id)
            .order_by(Evidence.created_at.asc())
        )

        result = await self.session.execute(statement)

        return list(result.scalars().all())