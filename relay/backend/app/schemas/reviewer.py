from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


ReviewDecision = Literal[
    "approved",
    "approved_with_conditions",
    "needs_revision",
    "rejected",
]

ReviewCheckStatus = Literal[
    "pass",
    "warning",
    "fail",
]


class ReviewCheck(BaseModel):
    status: ReviewCheckStatus
    explanation: str = Field(
        min_length=10,
        max_length=2000,
    )


class ReviewerResult(BaseModel):
    """
    Structured output produced by the Reviewer Agent.
    """

    decision: ReviewDecision

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    evidence_coverage: ReviewCheck
    schema_compatibility: ReviewCheck
    downstream_risk: ReviewCheck
    governance_compliance: ReviewCheck

    conditions: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)

    final_summary: str = Field(
        min_length=10,
        max_length=3000,
    )

    @model_validator(mode="after")
    def validate_decision(self) -> "ReviewerResult":
        if self.decision == "approved_with_conditions":
            if not self.conditions:
                raise ValueError(
                    "Approved-with-conditions reviews require conditions."
                )

        if self.decision in {"needs_revision", "rejected"}:
            if not self.missing_evidence and not self.conditions:
                raise ValueError(
                    "Revision or rejection must explain what is missing."
                )

        return self