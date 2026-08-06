from __future__ import annotations

from app.models.evidence import Evidence
from app.repositories.evidence import EvidenceRepository
from app.schemas.investigator import InvestigatorEvidence


class EvidenceService:
    """
    Application service for validated investigation evidence.
    """

    def __init__(
        self,
        repository: EvidenceRepository,
    ) -> None:
        self.repository = repository

    async def create_many(
        self,
        *,
        investigation_id: str,
        items: list[InvestigatorEvidence],
        created_by_agent: str = "investigator",
    ) -> list[Evidence]:
        """
        Validate and persist a group of evidence records.
        """

        if not investigation_id.strip():
            raise ValueError("Investigation ID cannot be empty.")

        if not items:
            raise ValueError(
                "At least one evidence item is required."
            )

        clean_agent_name = created_by_agent.strip()

        if not clean_agent_name:
            raise ValueError(
                "Evidence must identify the creating agent."
            )

        for item in items:
            if not item.source_asset_urn and not item.source_reference:
                raise ValueError(
                    f"Evidence '{item.title}' must include a source."
                )

            if not 0.0 <= item.confidence <= 1.0:
                raise ValueError(
                    f"Evidence '{item.title}' has invalid confidence."
                )

        return await self.repository.create_many(
            investigation_id=investigation_id,
            items=items,
            created_by_agent=clean_agent_name,
        )

    async def list_for_investigation(
        self,
        investigation_id: str,
    ) -> list[Evidence]:
        """
        Return all stored evidence for one investigation.
        """

        if not investigation_id.strip():
            raise ValueError("Investigation ID cannot be empty.")

        return await self.repository.list_for_investigation(
            investigation_id
        )