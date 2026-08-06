from __future__ import annotations

from backend.app.models.review import Review
from backend.app.repositories.review import ReviewRepository
from backend.app.schemas.reviewer import ReviewerResult


class ReviewNotFoundError(Exception):
    """
    Raised when an investigation has no stored review.
    """


class ReviewService:
    """
    Application service for persisted Reviewer decisions.
    """

    def __init__(
        self,
        repository: ReviewRepository,
    ) -> None:
        self.repository = repository

    async def create(
        self,
        *,
        investigation_id: str,
        repair_proposal_id: str,
        result: ReviewerResult,
        notes: str | None = None,
    ) -> Review:
        """
        Validate and persist one Reviewer result.
        """

        if not investigation_id.strip():
            raise ValueError("Investigation ID cannot be empty.")

        if not repair_proposal_id.strip():
            raise ValueError("Repair proposal ID cannot be empty.")

        if not 0.0 <= result.confidence <= 1.0:
            raise ValueError("Review confidence must be between 0 and 1.")

        if result.decision == "approved_with_conditions":
            if not result.conditions:
                raise ValueError(
                    "Approved-with-conditions reviews require conditions."
                )

        if result.decision in {"needs_revision", "rejected"}:
            if not result.conditions and not result.missing_evidence:
                raise ValueError(
                    "Revision or rejection must explain what is missing."
                )

        return await self.repository.create(
            investigation_id=investigation_id,
            repair_proposal_id=repair_proposal_id,
            result=result,
            notes=notes,
        )

    async def get_for_investigation(
        self,
        investigation_id: str,
    ) -> Review:
        """
        Retrieve the newest review for an investigation.
        """

        if not investigation_id.strip():
            raise ValueError("Investigation ID cannot be empty.")

        review = await self.repository.get_for_investigation(
            investigation_id
        )

        if review is None:
            raise ReviewNotFoundError(
                f"No review exists for investigation "
                f"'{investigation_id}'."
            )

        return review