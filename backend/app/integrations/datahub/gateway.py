from __future__ import annotations

from typing import Protocol

from backend.app.integrations.datahub.models import (
    AssetContext,
    AssetSummary,
    LineageGraph,
)


class DataHubGateway(Protocol):
    """
    Contract used by Relay to retrieve organizational context from DataHub.

    Implementations may use the DataHub MCP Server, SDK, GraphQL API,
    REST API, or deterministic demo fixtures.
    """

    async def health_check(self) -> bool:
        """
        Return True when the configured DataHub source is available.
        """

        ...

    async def search_assets(
        self,
        query: str,
        limit: int = 20,
    ) -> list[AssetSummary]:
        """
        Search DataHub assets using a human-readable query.
        """

        ...

    async def get_asset(
        self,
        urn: str,
    ) -> AssetContext:
        """
        Retrieve normalized metadata and schema context for one asset.
        """

        ...

    async def get_lineage(
        self,
        urn: str,
        upstream_depth: int = 2,
        downstream_depth: int = 2,
    ) -> LineageGraph:
        """
        Retrieve normalized upstream and downstream lineage.
        """

        ...