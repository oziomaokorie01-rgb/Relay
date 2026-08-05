from __future__ import annotations

from urllib.parse import unquote

from fastapi import APIRouter, HTTPException, Query, status

from app.api.dependencies import DataHubGatewayDependency
from app.integrations.datahub.mock_gateway import DataHubAssetNotFoundError
from app.integrations.datahub.models import (
    AssetContext,
    AssetSummary,
    LineageGraph,
)


router = APIRouter(
    prefix="/assets",
    tags=["Assets"],
)


@router.get(
    "/search",
    response_model=list[AssetSummary],
)
async def search_assets(
    gateway: DataHubGatewayDependency,
    q: str = Query(default="", max_length=200),
    limit: int = Query(default=20, ge=1, le=100),
) -> list[AssetSummary]:
    """
    Search assets in the configured DataHub environment.
    """

    return await gateway.search_assets(
        query=q,
        limit=limit,
    )


@router.get(
    "/{encoded_urn}/lineage",
    response_model=LineageGraph,
)
async def get_asset_lineage(
    encoded_urn: str,
    gateway: DataHubGatewayDependency,
    upstream_depth: int = Query(default=2, ge=0, le=5),
    downstream_depth: int = Query(default=2, ge=0, le=5),
) -> LineageGraph:
    """
    Retrieve upstream and downstream lineage for one asset.
    """

    urn = unquote(encoded_urn)

    try:
        return await gateway.get_lineage(
            urn=urn,
            upstream_depth=upstream_depth,
            downstream_depth=downstream_depth,
        )
    except DataHubAssetNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get(
    "/{encoded_urn}",
    response_model=AssetContext,
)
async def get_asset(
    encoded_urn: str,
    gateway: DataHubGatewayDependency,
) -> AssetContext:
    """
    Retrieve normalized metadata and schema context for one asset.
    """

    urn = unquote(encoded_urn)

    try:
        return await gateway.get_asset(urn)
    except DataHubAssetNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc