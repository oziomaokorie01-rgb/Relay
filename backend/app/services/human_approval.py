from __future__ import annotations

from app.models.human_approval import (
    HumanApproval,
    HumanApprovalDecision,
)
from app.repositories.human_approval import HumanApprovalRepository
from app.schemas.approval import HumanApprovalInput


class HumanApprovalNotFoundError(Exception):
    """
    Raised when an investigation has no recorded human decision.
    """


class HumanApprovalService:
    """
    Application service for explicit human review decisions.
    """

    def __init__(
        self,
        repository: HumanApprovalRepository,
    ) -> None:
        self.repository = repository

    async def create(
        self,
        *,
        investigation_id: str,
        review_id: str,
        approval: HumanApprovalInput,
        approved_by: str = "hackathon-user",
    ) -> HumanApproval:
        """
        Validate and persist one human decision.
        """

        if not investigation_id.strip():
            raise ValueError("Investigation ID cannot be empty.")

        if not review_id.strip():
            raise ValueError("Review ID cannot be empty.")

        if not approved_by.strip():
            raise ValueError("Approver identity cannot be empty.")

        if approval.decision in {"request_revision", "reject"}:
            if not approval.notes or not approval.notes.strip():
                raise ValueError(
                    "Revision and rejection decisions require notes."
                )

        return await self.repository.create(
            investigation_id=investigation_id,
            review_id=review_id,
            approval=approval,
            approved_by=approved_by.strip(),
        )

    async def get_latest_for_investigation(
        self,
        investigation_id: str,
    ) -> HumanApproval:
        """
        Retrieve the newest human decision for an investigation.
        """

        if not investigation_id.strip():
            raise ValueError("Investigation ID cannot be empty.")

        approval = await self.repository.get_latest_for_investigation(
            investigation_id
        )

        if approval is None:
            raise HumanApprovalNotFoundError(
                f"No human decision exists for investigation "
                f"'{investigation_id}'."
            )

        return approval

    async def require_approval(
        self,
        investigation_id: str,
    ) -> HumanApproval:
        """
        Return the latest decision only when it explicitly approves archiving.
        """

        approval = await self.get_latest_for_investigation(
            investigation_id
        )

        if approval.decision != HumanApprovalDecision.APPROVE:
            raise ValueError(
                "Verified memory requires an explicit human approval."
            )

        return approval