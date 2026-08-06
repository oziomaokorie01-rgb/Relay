from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.memory import (
    MemoryVerificationStatus,
    RelayMemory,
)
from app.schemas.archivist import ArchivistResult


class MemoryRepository:
    """
    Persistence layer for Relay organizational memories.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        investigation_id: str,
        result: ArchivistResult,
    ) -> RelayMemory:
        """
        Persist one verified Relay memory.

        The version number is calculated from existing memories sharing
        the same stable memory key.
        """

        version = await self._next_version(result.memory_key)

        memory = RelayMemory(
            memory_key=result.memory_key,
            version=version,
            originating_investigation_id=investigation_id,
            primary_asset_urn=result.primary_asset_urn,
            title=result.title,
            summary=result.summary,
            incident_type=result.incident_type,
            root_cause=result.root_cause,
            resolution=result.resolution,
            confidence=result.confidence,
            verification_status=MemoryVerificationStatus.VERIFIED,
            keywords=result.keywords,
            related_asset_urns=result.related_asset_urns,
            evidence_ids=result.evidence_ids,
            supersedes_memory_id=result.supersedes_memory_id,
        )

        self.session.add(memory)
        await self.session.commit()
        await self.session.refresh(memory)

        return memory

    async def get_by_id(
        self,
        memory_id: str,
    ) -> RelayMemory | None:
        """
        Retrieve one memory by its unique ID.
        """

        return await self.session.get(
            RelayMemory,
            memory_id,
        )

    async def list_verified(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[RelayMemory]:
        """
        Return verified memories ordered from newest to oldest.
        """

        statement = (
            select(RelayMemory)
            .where(
                RelayMemory.verification_status
                == MemoryVerificationStatus.VERIFIED
            )
            .order_by(RelayMemory.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        result = await self.session.execute(statement)

        return list(result.scalars().all())

    async def list_for_asset(
        self,
        asset_urn: str,
        *,
        limit: int = 50,
    ) -> list[RelayMemory]:
        """
        Return verified memories directly or indirectly related to an asset.
        """

        statement = (
            select(RelayMemory)
            .where(
                RelayMemory.verification_status
                == MemoryVerificationStatus.VERIFIED,
                or_(
                    RelayMemory.primary_asset_urn == asset_urn,
                    RelayMemory.related_asset_urns.contains([asset_urn]),
                ),
            )
            .order_by(RelayMemory.created_at.desc())
            .limit(limit)
        )

        result = await self.session.execute(statement)

        return list(result.scalars().all())

    async def search_verified(
        self,
        query: str,
        *,
        limit: int = 20,
    ) -> list[RelayMemory]:
        """
        Search verified memories using simple deterministic text matching.

        This supports the MVP without introducing a vector database.
        """

        normalized_query = query.strip().lower()

        if not normalized_query:
            return await self.list_verified(limit=limit)

        pattern = f"%{normalized_query}%"

        statement = (
            select(RelayMemory)
            .where(
                RelayMemory.verification_status
                == MemoryVerificationStatus.VERIFIED,
                or_(
                    func.lower(RelayMemory.title).like(pattern),
                    func.lower(RelayMemory.summary).like(pattern),
                    func.lower(RelayMemory.root_cause).like(pattern),
                    func.lower(RelayMemory.resolution).like(pattern),
                    func.lower(RelayMemory.incident_type).like(pattern),
                    func.lower(RelayMemory.primary_asset_urn).like(pattern),
                ),
            )
            .order_by(RelayMemory.created_at.desc())
            .limit(limit)
        )

        result = await self.session.execute(statement)

        return list(result.scalars().all())

    async def _next_version(
        self,
        memory_key: str,
    ) -> int:
        """
        Return the next version number for a stable memory key.
        """

        statement = select(
            func.max(RelayMemory.version)
        ).where(
            RelayMemory.memory_key == memory_key
        )

        result = await self.session.execute(statement)
        latest_version = result.scalar_one_or_none()

        return (latest_version or 0) + 1