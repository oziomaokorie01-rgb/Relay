from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.repair_proposal import (
    RepairArtifactType,
    RepairProposal,
    RepairProposalStatus,
    RepairRiskLevel,
)
from app.schemas.repair import RepairResult


class RepairProposalRepository:
    """
    Persistence layer for Relay repair proposals.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        investigation_id: str,
        result: RepairResult,
    ) -> RepairProposal:
        """
        Persist one validated Repair Agent result.
        """

        proposal = RepairProposal(
            investigation_id=investigation_id,
            summary=result.proposal_summary,
            artifact_type=RepairArtifactType(result.artifact_type),
            artifact_content=result.artifact_content,
            language=result.language,
            risk_level=RepairRiskLevel(result.risk_level),
            expected_outcome=result.expected_outcome,
            rollback_plan=result.rollback_plan,
            affected_asset_urns=result.affected_assets,
            tests=[
                test.model_dump(mode="json")
                for test in result.tests
            ],
            assumptions=result.assumptions,
            evidence_ids=result.evidence_ids,
            confidence=result.confidence,
            status=RepairProposalStatus.PROPOSED,
        )

        self.session.add(proposal)
        await self.session.commit()
        await self.session.refresh(proposal)

        return proposal

    async def get_for_investigation(
        self,
        investigation_id: str,
    ) -> RepairProposal | None:
        """
        Return the newest repair proposal for one investigation.
        """

        statement = (
            select(RepairProposal)
            .where(
                RepairProposal.investigation_id == investigation_id
            )
            .order_by(RepairProposal.created_at.desc())
            .limit(1)
        )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()

    async def update_status(
        self,
        proposal: RepairProposal,
        status: RepairProposalStatus,
    ) -> RepairProposal:
        """
        Persist a repair proposal status change.
        """

        proposal.status = status

        await self.session.commit()
        await self.session.refresh(proposal)

        return proposal