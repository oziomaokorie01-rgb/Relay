from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.human_approval import (
    HumanApproval,
    HumanApprovalDecision,
)
from backend.app.schemas.approval import HumanApprovalInput


class HumanApprovalRepository:
    """
    Persistence layer for explicit human investigation decisions.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        investigation_id: str,
        review_id: str,
        approval: HumanApprovalInput,
        approved_by: str = "hackathon-user",
    ) -> HumanApproval:
        """
        Persist one human approval, revision request, or rejection.
        """

        record = HumanApproval(
            investigation_id=investigation_id,
            review_id=review_id,
            decision=HumanApprovalDecision(approval.decision),
            edited_title=approval.edited_title,
            edited_summary=approval.edited_summary,
            notes=approval.notes,
            approved_by=approved_by,
        )

        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)

        return record

    async def get_latest_for_investigation(
        self,
        investigation_id: str,
    ) -> HumanApproval | None:
        """
        Return the newest human decision for an investigation.
        """

        statement = (
            select(HumanApproval)
            .where(
                HumanApproval.investigation_id == investigation_id
            )
            .order_by(HumanApproval.created_at.desc())
            .limit(1)
        )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()