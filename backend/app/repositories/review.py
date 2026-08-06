from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from.app.models.review import Review, ReviewDecision
from.app.schemas.reviewer import ReviewerResult


class ReviewRepository:
    """
    Persistence layer for Reviewer decisions.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        investigation_id: str,
        repair_proposal_id: str,
        result: ReviewerResult,
        notes: str | None = None,
    ) -> Review:
        """
        Persist one validated Reviewer result.
        """

        review = Review(
            investigation_id=investigation_id,
            repair_proposal_id=repair_proposal_id,
            decision=ReviewDecision(result.decision),
            evidence_coverage=result.evidence_coverage.model_dump(
                mode="json"
            ),
            schema_compatibility=result.schema_compatibility.model_dump(
                mode="json"
            ),
            downstream_risk=result.downstream_risk.model_dump(
                mode="json"
            ),
            governance_compliance=result.governance_compliance.model_dump(
                mode="json"
            ),
            confidence=result.confidence,
            conditions=result.conditions,
            missing_evidence=result.missing_evidence,
            notes=notes or result.final_summary,
        )

        self.session.add(review)
        await self.session.commit()
        await self.session.refresh(review)

        return review

    async def get_for_investigation(
        self,
        investigation_id: str,
    ) -> Review | None:
        """
        Return the newest review for one investigation.
        """

        statement = (
            select(Review)
            .where(Review.investigation_id == investigation_id)
            .order_by(Review.created_at.desc())
            .limit(1)
        )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()