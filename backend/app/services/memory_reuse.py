from __future__ import annotations

import re

from.app.models.investigation import Investigation
from.app.models.memory import RelayMemory
from.app.models.memory_reuse_event import (
    MemoryReuseEvent,
    MemoryReuseType,
)
from.app.repositories.memory_reuse_event import (
    MemoryReuseEventRepository,
)


class MemoryReuseService:
    """
    Application service for scoring and recording verified-memory reuse.
    """

    def __init__(
        self,
        repository: MemoryReuseEventRepository,
    ) -> None:
        self.repository = repository

    async def record(
        self,
        *,
        memory: RelayMemory,
        investigation: Investigation,
        similarity_score: float,
        reuse_type: MemoryReuseType,
        agent_explanation: str,
        accepted: bool,
        estimated_steps_skipped: int = 0,
        estimated_time_saved_minutes: int = 0,
    ) -> MemoryReuseEvent:
        """
        Validate and persist one memory inheritance event.
        """

        if not 0.0 <= similarity_score <= 1.0:
            raise ValueError(
                "Memory similarity score must be between 0 and 1."
            )

        if not agent_explanation.strip():
            raise ValueError(
                "Memory reuse requires an agent explanation."
            )

        if estimated_steps_skipped < 0:
            raise ValueError(
                "Estimated steps skipped cannot be negative."
            )

        if estimated_time_saved_minutes < 0:
            raise ValueError(
                "Estimated time saved cannot be negative."
            )

        if (
            memory.originating_investigation_id
            == investigation.id
        ):
            raise ValueError(
                "An investigation cannot inherit its own memory."
            )

        return await self.repository.create(
            memory_id=memory.id,
            investigation_id=investigation.id,
            similarity_score=similarity_score,
            reuse_type=reuse_type,
            agent_explanation=agent_explanation.strip(),
            accepted=accepted,
            estimated_steps_skipped=estimated_steps_skipped,
            estimated_time_saved_minutes=estimated_time_saved_minutes,
        )

    async def list_for_memory(
        self,
        memory_id: str,
    ) -> list[MemoryReuseEvent]:
        """
        Return the complete reuse history for one Relay memory.
        """

        if not memory_id.strip():
            raise ValueError("Memory ID cannot be empty.")

        return await self.repository.list_for_memory(
            memory_id
        )

    async def list_for_investigation(
        self,
        investigation_id: str,
    ) -> list[MemoryReuseEvent]:
        """
        Return all memories inherited by one investigation.
        """

        if not investigation_id.strip():
            raise ValueError("Investigation ID cannot be empty.")

        return await self.repository.list_for_investigation(
            investigation_id
        )

    def calculate_similarity(
        self,
        *,
        memory: RelayMemory,
        investigation: Investigation,
        related_asset_urns: list[str],
    ) -> float:
        """
        Calculate deterministic memory similarity for the MVP.

        Formula:

        0.35 × primary asset match
        0.20 × related asset overlap
        0.15 × incident-type match
        0.15 × keyword overlap
        0.15 × text similarity
        """

        primary_asset_match = (
            1.0
            if memory.primary_asset_urn == investigation.asset_urn
            else 0.0
        )

        memory_related_assets = set(
            memory.related_asset_urns
        )
        investigation_related_assets = set(
            related_asset_urns
        )

        related_asset_overlap = self._set_overlap(
            memory_related_assets,
            investigation_related_assets,
        )

        incident_type_match = self._incident_type_match(
            memory=memory,
            investigation=investigation,
        )

        investigation_tokens = self._tokenize(
            " ".join(
                [
                    investigation.title,
                    investigation.description,
                    investigation.root_cause_summary or "",
                ]
            )
        )

        memory_keyword_tokens = {
            token
            for keyword in memory.keywords
            for token in self._tokenize(keyword)
        }

        keyword_overlap = self._set_overlap(
            memory_keyword_tokens,
            investigation_tokens,
        )

        memory_text_tokens = self._tokenize(
            " ".join(
                [
                    memory.title,
                    memory.summary,
                    memory.root_cause,
                    memory.resolution,
                ]
            )
        )

        text_similarity = self._set_overlap(
            memory_text_tokens,
            investigation_tokens,
        )

        score = (
            0.35 * primary_asset_match
            + 0.20 * related_asset_overlap
            + 0.15 * incident_type_match
            + 0.15 * keyword_overlap
            + 0.15 * text_similarity
        )

        return round(min(max(score, 0.0), 1.0), 4)

    @staticmethod
    def _set_overlap(
        left: set[str],
        right: set[str],
    ) -> float:
        """
        Return Jaccard overlap between two sets.
        """

        if not left or not right:
            return 0.0

        intersection = len(left & right)
        union = len(left | right)

        if union == 0:
            return 0.0

        return intersection / union

    @staticmethod
    def _incident_type_match(
        *,
        memory: RelayMemory,
        investigation: Investigation,
    ) -> float:
        """
        Infer whether the investigation resembles the memory incident type.
        """

        investigation_text = (
            f"{investigation.title} "
            f"{investigation.description} "
            f"{investigation.root_cause_summary or ''}"
        ).lower()

        incident_terms = memory.incident_type.replace(
            "_",
            " ",
        ).split()

        if not incident_terms:
            return 0.0

        matched_terms = sum(
            1
            for term in incident_terms
            if term in investigation_text
        )

        return matched_terms / len(incident_terms)

    @staticmethod
    def _tokenize(value: str) -> set[str]:
        """
        Normalize text into searchable lowercase tokens.
        """

        return {
            token
            for token in re.findall(
                r"[a-z0-9_]+",
                value.lower(),
            )
            if len(token) > 2
        }