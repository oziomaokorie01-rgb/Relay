from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


RepairArtifactType = Literal[
    "sql",
    "dbt_model",
    "data_quality_test",
    "configuration",
    "pipeline_patch",
    "documentation",
    "runbook",
    "recommendation_only",
]

RepairRiskLevel = Literal[
    "low",
    "medium",
    "high",
]


class RepairTest(BaseModel):
    """
    One validation test recommended alongside a repair proposal.
    """

    name: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=10, max_length=2000)
    artifact: str = Field(min_length=1, max_length=10000)


class RepairResult(BaseModel):
    """
    Validated structured output produced by the Repair Agent.
    """

    proposal_summary: str = Field(
        min_length=10,
        max_length=3000,
    )

    artifact_type: RepairArtifactType

    artifact_content: str | None = Field(
        default=None,
        max_length=30000,
    )

    language: str | None = Field(
        default=None,
        max_length=40,
    )

    affected_assets: list[str] = Field(
        min_length=1,
    )

    risk_level: RepairRiskLevel

    expected_outcome: str = Field(
        min_length=10,
        max_length=3000,
    )

    rollback_plan: str | None = Field(
        default=None,
        max_length=3000,
    )

    tests: list[RepairTest] = Field(
        default_factory=list,
    )

    assumptions: list[str] = Field(
        default_factory=list,
    )

    evidence_ids: list[str] = Field(
        min_length=1,
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    @model_validator(mode="after")
    def validate_repair(self) -> "RepairResult":
        """
        Enforce Relay's repair safety rules.
        """

        if self.artifact_type != "recommendation_only":
            if not self.artifact_content or not self.artifact_content.strip():
                raise ValueError(
                    "A generated repair artifact cannot be empty."
                )

        if self.risk_level in {"medium", "high"}:
            if not self.rollback_plan or not self.rollback_plan.strip():
                raise ValueError(
                    "Medium- and high-risk repairs require a rollback plan."
                )

        if self.artifact_type == "sql" and self.language != "sql":
            raise ValueError(
                "SQL repair artifacts must declare language='sql'."
            )

        return self