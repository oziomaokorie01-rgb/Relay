from __future__ import annotations

import re

from pydantic import BaseModel, Field, field_validator, model_validator


class ArchivistResult(BaseModel):
    """
    Structured output produced by the Archivist Agent.

    This becomes the basis of a reusable Relay Memory after validation
    and persistence.
    """

    memory_key: str = Field(
        min_length=3,
        max_length=120,
    )

    title: str = Field(
        min_length=3,
        max_length=240,
    )

    summary: str = Field(
        min_length=10,
        max_length=5000,
    )

    incident_type: str = Field(
        min_length=3,
        max_length=80,
    )

    root_cause: str = Field(
        min_length=10,
        max_length=5000,
    )

    resolution: str = Field(
        min_length=10,
        max_length=10000,
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    keywords: list[str] = Field(
        min_length=1,
        max_length=30,
    )

    primary_asset_urn: str = Field(
        min_length=5,
        max_length=2000,
    )

    related_asset_urns: list[str] = Field(
        default_factory=list,
    )

    evidence_ids: list[str] = Field(
        min_length=1,
    )

    supersedes_memory_id: str | None = None

    @field_validator("memory_key")
    @classmethod
    def validate_memory_key(cls, value: str) -> str:
        """
        Require a stable lowercase slug suitable for memory versioning.
        """

        normalized = value.strip().lower()

        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", normalized):
            raise ValueError(
                "memory_key must contain lowercase letters, numbers, "
                "and single hyphens only."
            )

        return normalized

    @field_validator("keywords")
    @classmethod
    def normalize_keywords(cls, values: list[str]) -> list[str]:
        """
        Normalize and deduplicate searchable memory keywords.
        """

        normalized: list[str] = []

        for value in values:
            keyword = value.strip().lower()

            if keyword and keyword not in normalized:
                normalized.append(keyword)

        if not normalized:
            raise ValueError(
                "At least one non-empty keyword is required."
            )

        return normalized

    @model_validator(mode="after")
    def validate_asset_links(self) -> "ArchivistResult":
        """
        Ensure the primary asset is not duplicated in related assets.
        """

        self.related_asset_urns = list(
            dict.fromkeys(
                urn.strip()
                for urn in self.related_asset_urns
                if urn.strip() and urn.strip() != self.primary_asset_urn
            )
        )

        return self