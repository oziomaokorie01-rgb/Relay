from __future__ import annotations

from app.models.investigation import Investigation
from app.repositories.investigation import InvestigationRepository
from app.schemas.investigation import InvestigationCreate


class InvestigationNotFoundError(Exception):
    """
    Raised when a requested investigation does not exist.
    """


class InvestigationService:
    """
    Business-logic layer for Relay investigations.
    """

    def __init__(
        self,
        repository: InvestigationRepository,
    ) -> None:
        self.repository = repository

    async def create(
        self,
        data: InvestigationCreate,
    ) -> Investigation:
        """
        Create a new investigation in its default draft state.
        """

        return await self.repository.create(data)

    async def get_by_id(
        self,
        investigation_id: str,
    ) -> Investigation:
        """
        Retrieve an investigation or raise a domain-specific error.
        """

        investigation = await self.repository.get_by_id(investigation_id)

        if investigation is None:
            raise InvestigationNotFoundError(
                f"Investigation '{investigation_id}' was not found."
            )

        return investigation

    async def list_all(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Investigation]:
        """
        Return investigations ordered from newest to oldest.
        """

        safe_limit = min(max(limit, 1), 100)
        safe_offset = max(offset, 0)

        return await self.repository.list_all(
            limit=safe_limit,
            offset=safe_offset,
        )