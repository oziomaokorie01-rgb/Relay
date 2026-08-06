from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


EvidenceType = Literal[
    "schema_change",
    "lineage_dependency",
    "freshness_failure",
    "quality_failure",
    "ownership_signal",
    "governance_rule",
    "previous_memory",
    "query_result",
    "documentation",
    "manual_context",
]


class InvestigatorEvidence(BaseModel):
    """
    One structured evidence item produced by the Investigator Agent.
    """

    type: EvidenceType
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=10, max_length=2000)
    source_asset_urn: str | None = None
    source_reference: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)


class InheritedMemoryReference(BaseModel):
    """
    Describes how a verified Relay memory influenced an investigation.
    """

    memory_id: str
    relevance: float = Field(ge=0.0, le=1.0)
    usage: str = Field(min_length=3, max_length=1000)


class InvestigatorResult(BaseModel):
    """
    Validated output produced by the Investigator Agent.
    """

    problem_summary: str = Field(min_length=10, max_length=2000)
    suspected_root_cause: str = Field(min_length=10, max_length=3000)
    confidence: float = Field(ge=0.0, le=1.0)

    affected_assets: list[str] = Field(default_factory=list)
    evidence: list[InvestigatorEvidence] = Field(min_length=1)
    inherited_memories: list[InheritedMemoryReference] = Field(
        default_factory=list
    )
    unresolved_questions: list[str] = Field(default_factory=list)
    reasoning_summary: str = Field(min_length=10, max_length=3000)

    @model_validator(mode="after")
    def validate_evidence_references(self) -> "InvestigatorResult":
        """
        Ensure the result contains meaningful asset references.
        """

        if not self.affected_assets:
            raise ValueError(
                "InvestigatorResult must include at least one affected asset."
            )

        evidence_with_source = [
            item
            for item in self.evidence
            if item.source_asset_urn or item.source_reference
        ]

        if not evidence_with_source:
            raise ValueError(
                "At least one evidence item must include a source reference."
            )

        return self