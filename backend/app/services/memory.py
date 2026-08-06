from __future__ import annotations

from.app.models.memory import (
    MemoryVerificationStatus,
    RelayMemory,
)
from.app.repositories.memory import MemoryRepository
from.app.schemas.archivist import ArchivistResult


class MemoryNotFoundError(Exception):
    """
    Raised when a requested Relay memory does not exist.
    """


class MemoryService:
    """
    Application service for verified Relay organizational memories.
    """

    def __init__(
        self,
        repository: MemoryRepository,
    ) -> None:
        self.repository = repository

    async def create_verified(
        self,
        *,
        investigation_id: str,
        result: ArchivistResult,
    ) -> RelayMemory:
        """
        Validate and persist one verified organizational memory.
        """

        if not investigation_id.strip():
            raise ValueError("Investigation ID cannot be empty.")

        if not result.evidence_ids:
            raise ValueError(
                "A verified memory must reference supporting evidence."
            )

        if not result.primary_asset_urn.strip():
            raise ValueError(
                "A verified memory must identify its primary DataHub asset."
            )

        if not 0.0 <= result.confidence <= 1.0:
            raise ValueError(
                "Memory confidence must be between 0 and 1."
            )

        if not result.root_cause.strip():
            raise ValueError(
                "A verified memory must include a root cause."
            )

        if not result.resolution.strip():
            raise ValueError(
                "A verified memory must include a resolution."
            )

        return await self.repository.create(
            investigation_id=investigation_id,
            result=result,
        )

    async def get_by_id(
        self,
        memory_id: str,
    ) -> RelayMemory:
        """
        Retrieve one memory or raise a domain-specific error.
        """

        if not memory_id.strip():
            raise ValueError("Memory ID cannot be empty.")

        memory = await self.repository.get_by_id(memory_id)

        if memory is None:
            raise MemoryNotFoundError(
                f"Relay memory '{memory_id}' was not found."
            )

        return memory

    async def list_verified(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[RelayMemory]:
        """
        Return verified memories ordered from newest to oldest.
        """

        safe_limit = min(max(limit, 1), 100)
        safe_offset = max(offset, 0)

        return await self.repository.list_verified(
            limit=safe_limit,
            offset=safe_offset,
        )

    async def list_for_asset(
        self,
        asset_urn: str,
        *,
        limit: int = 50,
    ) -> list[RelayMemory]:
        """
        Return verified memories associated with a DataHub asset.
        """

        if not asset_urn.strip():
            raise ValueError("Asset URN cannot be empty.")

        safe_limit = min(max(limit, 1), 100)

        return await self.repository.list_for_asset(
            asset_urn.strip(),
            limit=safe_limit,
        )

    async def search_verified(
        self,
        query: str,
        *,
        limit: int = 20,
    ) -> list[RelayMemory]:
        """
        Search verified organizational memories.
        """

        safe_limit = min(max(limit, 1), 100)

        return await self.repository.search_verified(
            query.strip(),
            limit=safe_limit,
        )

    async def require_verified(
        self,
        memory_id: str,
    ) -> RelayMemory:
        """
        Retrieve a memory only when it is currently verified.
        """

        memory = await self.get_by_id(memory_id)

        if (
            memory.verification_status
            != MemoryVerificationStatus.VERIFIED
        ):
            raise ValueError(
                "Only verified Relay memories may be inherited."
            )

        return memory