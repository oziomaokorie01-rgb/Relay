from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


HumanApprovalDecision = Literal[
    "approve",
    "request_revision",
    "reject",
]


class HumanApprovalInput(BaseModel):
    """
    Human decision submitted after Reviewer validation.
    """

    decision: HumanApprovalDecision

    edited_title: str | None = Field(
        default=None,
        min_length=3,
        max_length=240,
    )

    edited_summary: str | None = Field(
        default=None,
        min_length=10,
        max_length=5000,
    )

    notes: str | None = Field(
        default=None,
        max_length=3000,
    )

    @model_validator(mode="after")
    def validate_decision_details(self) -> "HumanApprovalInput":
        if self.decision in {"request_revision", "reject"}:
            if not self.notes or not self.notes.strip():
                raise ValueError(
                    "Revision and rejection decisions require notes."
                )

        return self


class HumanApprovalResponse(BaseModel):
    """
    Immediate response after Relay accepts a human decision.
    """

    investigation_id: str
    decision: HumanApprovalDecision
    status: str
    message: str