from __future__ import annotations

from backend.app.models.repair_proposal import (
    RepairProposal,
    RepairProposalStatus,
)
from backend.app.repositories.repair_proposal import RepairProposalRepository
from backend.app.schemas.repair import RepairResult


class RepairProposalNotFoundError(Exception):
    """
    Raised when an investigation has no stored repair proposal.
    """


class RepairProposalService:
    """
    Application service for Relay repair proposals.
    """

    def __init__(
        self,
        repository: RepairProposalRepository,
    ) -> None:
        self.repository = repository

    async def create(
        self,
        *,
        investigation_id: str,
        result: RepairResult,
    ) -> RepairProposal:
        """
        Validate and persist one Repair Agent proposal.
        """

        if not investigation_id.strip():
            raise ValueError("Investigation ID cannot be empty.")

        if not result.evidence_ids:
            raise ValueError(
                "A repair proposal must cite persisted evidence."
            )

        if result.risk_level in {"medium", "high"}:
            if not result.rollback_plan or not result.rollback_plan.strip():
                raise ValueError(
                    "Medium- and high-risk repairs require a rollback plan."
                )

        if result.artifact_type != "recommendation_only":
            if not result.artifact_content or not result.artifact_content.strip():
                raise ValueError(
                    "A generated repair artifact cannot be empty."
                )

        return await self.repository.create(
            investigation_id=investigation_id,
            result=result,
        )

    async def get_for_investigation(
        self,
        investigation_id: str,
    ) -> RepairProposal:
        """
        Retrieve the newest repair proposal for an investigation.
        """

        if not investigation_id.strip():
            raise ValueError("Investigation ID cannot be empty.")

        proposal = await self.repository.get_for_investigation(
            investigation_id
        )

        if proposal is None:
            raise RepairProposalNotFoundError(
                f"No repair proposal exists for investigation "
                f"'{investigation_id}'."
            )

        return proposal

    async def mark_under_review(
        self,
        proposal: RepairProposal,
    ) -> RepairProposal:
        """
        Mark a proposal as ready for Reviewer evaluation.
        """

        return await self.repository.update_status(
            proposal,
            RepairProposalStatus.UNDER_REVIEW,
        )

    async def update_status(
        self,
        proposal: RepairProposal,
        status: RepairProposalStatus,
    ) -> RepairProposal:
        """
        Persist an explicit repair proposal status change.
        """

        return await self.repository.update_status(
            proposal,
            status,
        )