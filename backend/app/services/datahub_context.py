from __future__ import annotations

from typing import Any

from.app.integrations.datahub.gateway import DataHubGateway
from.app.integrations.datahub.models import AssetContext, LineageGraph


class DataHubContextService:
    """
    Collects and normalizes DataHub context for an investigation.
    """

    def __init__(
        self,
        gateway: DataHubGateway,
    ) -> None:
        self.gateway = gateway

    async def gather(
        self,
        asset_urn: str,
        *,
        upstream_depth: int = 2,
        downstream_depth: int = 2,
    ) -> dict[str, Any]:
        """
        Retrieve the selected asset and its lineage, then return a
        JSON-serializable snapshot suitable for database persistence.
        """

        asset = await self.gateway.get_asset(asset_urn)

        lineage = await self.gateway.get_lineage(
            asset_urn,
            upstream_depth=upstream_depth,
            downstream_depth=downstream_depth,
        )

        return self._build_snapshot(
            asset=asset,
            lineage=lineage,
        )

    @staticmethod
    def _build_snapshot(
        *,
        asset: AssetContext,
        lineage: LineageGraph,
    ) -> dict[str, Any]:
        """
        Convert validated Pydantic models into a stable storage structure.
        """

        return {
            "asset": asset.model_dump(mode="json"),
            "lineage": lineage.model_dump(mode="json"),
            "summary": {
                "asset_urn": asset.urn,
                "asset_name": asset.display_name,
                "entity_type": asset.entity_type,
                "platform": asset.platform,
                "domain": asset.domain,
                "owner_count": len(asset.owners),
                "schema_field_count": len(asset.schema_fields),
                "upstream_count": len(asset.upstream_assets),
                "downstream_count": len(asset.downstream_assets),
                "quality_status": asset.quality_status,
                "memory_count": asset.memory_count,
            },
        }