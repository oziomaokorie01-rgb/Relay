from __future__ import annotations

from datetime import datetime, timezone

from.app.integrations.datahub.models import (
    AssetContext,
    AssetOwner,
    AssetReference,
    AssetSummary,
    LineageEdge,
    LineageGraph,
    LineageNode,
    SchemaField,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class DataHubAssetNotFoundError(Exception):
    """
    Raised when the mock DataHub environment cannot find an asset.
    """


class MockDataHubGateway:
    """
    Deterministic DataHub gateway used for local development and demos.
    """

    def __init__(self) -> None:
        self.assets = self._build_assets()

    async def health_check(self) -> bool:
        return True

    async def search_assets(
        self,
        query: str,
        limit: int = 20,
    ) -> list[AssetSummary]:
        normalized_query = query.strip().lower()

        matches = []

        for asset in self.assets.values():
            searchable_text = " ".join(
                [
                    asset.name,
                    asset.display_name,
                    asset.entity_type,
                    asset.platform,
                    asset.domain or "",
                    asset.description or "",
                    " ".join(owner.name for owner in asset.owners),
                    " ".join(asset.tags),
                ]
            ).lower()

            if not normalized_query or normalized_query in searchable_text:
                matches.append(
                    AssetSummary(
                        urn=asset.urn,
                        name=asset.name,
                        display_name=asset.display_name,
                        entity_type=asset.entity_type,
                        platform=asset.platform,
                        owner=asset.owners[0].name if asset.owners else None,
                        domain=asset.domain,
                        description=asset.description,
                    )
                )

        return matches[: max(1, min(limit, 100))]

    async def get_asset(
        self,
        urn: str,
    ) -> AssetContext:
        asset = self.assets.get(urn)

        if asset is None:
            raise DataHubAssetNotFoundError(
                f"DataHub asset '{urn}' was not found."
            )

        return asset.model_copy(deep=True)

    async def get_lineage(
        self,
        urn: str,
        upstream_depth: int = 2,
        downstream_depth: int = 2,
    ) -> LineageGraph:
        root = await self.get_asset(urn)

        nodes: dict[str, LineageNode] = {
            root.urn: LineageNode(
                id=root.urn,
                urn=root.urn,
                label=root.display_name,
                entity_type=root.entity_type,
                platform=root.platform,
                depth=0,
            )
        }
        edges: list[LineageEdge] = []

        await self._walk_upstream(
            asset=root,
            depth=1,
            maximum_depth=max(upstream_depth, 0),
            nodes=nodes,
            edges=edges,
        )

        await self._walk_downstream(
            asset=root,
            depth=1,
            maximum_depth=max(downstream_depth, 0),
            nodes=nodes,
            edges=edges,
        )

        return LineageGraph(
            root_urn=root.urn,
            nodes=list(nodes.values()),
            edges=edges,
        )

    async def _walk_upstream(
        self,
        *,
        asset: AssetContext,
        depth: int,
        maximum_depth: int,
        nodes: dict[str, LineageNode],
        edges: list[LineageEdge],
    ) -> None:
        if depth > maximum_depth:
            return

        for reference in asset.upstream_assets:
            upstream = await self.get_asset(reference.urn)

            nodes.setdefault(
                upstream.urn,
                LineageNode(
                    id=upstream.urn,
                    urn=upstream.urn,
                    label=upstream.display_name,
                    entity_type=upstream.entity_type,
                    platform=upstream.platform,
                    depth=-depth,
                ),
            )

            edge = LineageEdge(
                source=upstream.urn,
                target=asset.urn,
                direction="upstream",
            )

            if edge not in edges:
                edges.append(edge)

            await self._walk_upstream(
                asset=upstream,
                depth=depth + 1,
                maximum_depth=maximum_depth,
                nodes=nodes,
                edges=edges,
            )

    async def _walk_downstream(
        self,
        *,
        asset: AssetContext,
        depth: int,
        maximum_depth: int,
        nodes: dict[str, LineageNode],
        edges: list[LineageEdge],
    ) -> None:
        if depth > maximum_depth:
            return

        for reference in asset.downstream_assets:
            downstream = await self.get_asset(reference.urn)

            nodes.setdefault(
                downstream.urn,
                LineageNode(
                    id=downstream.urn,
                    urn=downstream.urn,
                    label=downstream.display_name,
                    entity_type=downstream.entity_type,
                    platform=downstream.platform,
                    depth=depth,
                ),
            )

            edge = LineageEdge(
                source=asset.urn,
                target=downstream.urn,
                direction="downstream",
            )

            if edge not in edges:
                edges.append(edge)

            await self._walk_downstream(
                asset=downstream,
                depth=depth + 1,
                maximum_depth=maximum_depth,
                nodes=nodes,
                edges=edges,
            )

    def _build_assets(self) -> dict[str, AssetContext]:
        raw_customers_urn = "urn:li:dataset:(postgres,raw_customers,PROD)"
        raw_orders_urn = "urn:li:dataset:(postgres,raw_orders,PROD)"
        clean_orders_urn = "urn:li:dataset:(dbt,clean_orders,PROD)"
        revenue_model_urn = "urn:li:dataset:(dbt,revenue_model,PROD)"
        revenue_dashboard_urn = (
            "urn:li:dashboard:(looker,revenue_dashboard)"
        )
        forecast_model_urn = (
            "urn:li:mlModel:(monthly_forecast_model,PROD)"
        )

        finance_owner = AssetOwner(
            name="Finance Analytics",
            type="group",
            email="finance-analytics@example.com",
        )

        platform_owner = AssetOwner(
            name="Data Platform",
            type="group",
            email="data-platform@example.com",
        )

        raw_customers = AssetContext(
            urn=raw_customers_urn,
            name="raw_customers",
            display_name="Raw Customers",
            entity_type="dataset",
            platform="postgres",
            domain="Finance",
            description="Raw customer records from the transactional system.",
            owners=[platform_owner],
            tags=["raw", "customers", "source"],
            schema_fields=[
                SchemaField(name="customer_id", data_type="integer", nullable=False),
                SchemaField(name="customer_name", data_type="string"),
                SchemaField(name="country", data_type="string"),
            ],
            downstream_assets=[
                AssetReference(
                    urn=clean_orders_urn,
                    name="clean_orders",
                    display_name="Clean Orders",
                    entity_type="dataset",
                    platform="dbt",
                )
            ],
            last_updated=utc_now(),
            quality_status="healthy",
        )

        raw_orders = AssetContext(
            urn=raw_orders_urn,
            name="raw_orders",
            display_name="Raw Orders",
            entity_type="dataset",
            platform="postgres",
            domain="Finance",
            description="Raw order events ingested from the commerce database.",
            owners=[platform_owner],
            tags=["raw", "orders", "source"],
            schema_fields=[
                SchemaField(
                    name="order_id",
                    data_type="integer",
                    nullable=False,
                ),
                SchemaField(
                    name="customer_id",
                    data_type="string",
                    nullable=False,
                    description=(
                        "Changed from integer to string in the latest source update."
                    ),
                ),
                SchemaField(
                    name="order_total",
                    data_type="decimal",
                    nullable=False,
                ),
                SchemaField(
                    name="created_at",
                    data_type="timestamp",
                    nullable=False,
                ),
            ],
            downstream_assets=[
                AssetReference(
                    urn=clean_orders_urn,
                    name="clean_orders",
                    display_name="Clean Orders",
                    entity_type="dataset",
                    platform="dbt",
                )
            ],
            last_updated=utc_now(),
            quality_status="warning",
            metadata={
                "schema_change": {
                    "field": "customer_id",
                    "previous_type": "integer",
                    "current_type": "string",
                }
            },
        )

        clean_orders = AssetContext(
            urn=clean_orders_urn,
            name="clean_orders",
            display_name="Clean Orders",
            entity_type="dataset",
            platform="dbt",
            domain="Finance",
            description="Validated and normalized orders used by finance models.",
            owners=[finance_owner],
            tags=["dbt", "clean", "orders"],
            schema_fields=[
                SchemaField(name="order_id", data_type="integer", nullable=False),
                SchemaField(name="customer_id", data_type="integer", nullable=False),
                SchemaField(name="order_total", data_type="decimal", nullable=False),
            ],
            upstream_assets=[
                AssetReference(
                    urn=raw_orders_urn,
                    name="raw_orders",
                    display_name="Raw Orders",
                    entity_type="dataset",
                    platform="postgres",
                ),
                AssetReference(
                    urn=raw_customers_urn,
                    name="raw_customers",
                    display_name="Raw Customers",
                    entity_type="dataset",
                    platform="postgres",
                ),
            ],
            downstream_assets=[
                AssetReference(
                    urn=revenue_model_urn,
                    name="revenue_model",
                    display_name="Revenue Model",
                    entity_type="dataset",
                    platform="dbt",
                )
            ],
            last_updated=utc_now(),
            quality_status="degraded",
        )

        revenue_model = AssetContext(
            urn=revenue_model_urn,
            name="revenue_model",
            display_name="Revenue Model",
            entity_type="dataset",
            platform="dbt",
            domain="Finance",
            description="Aggregated revenue model for reporting and forecasting.",
            owners=[finance_owner],
            tags=["dbt", "revenue", "finance"],
            schema_fields=[
                SchemaField(name="report_date", data_type="date", nullable=False),
                SchemaField(name="revenue", data_type="decimal", nullable=False),
                SchemaField(name="customer_count", data_type="integer"),
            ],
            upstream_assets=[
                AssetReference(
                    urn=clean_orders_urn,
                    name="clean_orders",
                    display_name="Clean Orders",
                    entity_type="dataset",
                    platform="dbt",
                )
            ],
            downstream_assets=[
                AssetReference(
                    urn=revenue_dashboard_urn,
                    name="revenue_dashboard",
                    display_name="Revenue Dashboard",
                    entity_type="dashboard",
                    platform="looker",
                ),
                AssetReference(
                    urn=forecast_model_urn,
                    name="monthly_forecast_model",
                    display_name="Monthly Forecast Model",
                    entity_type="ml_model",
                    platform="python",
                ),
            ],
            last_updated=utc_now(),
            quality_status="degraded",
        )

        revenue_dashboard = AssetContext(
            urn=revenue_dashboard_urn,
            name="revenue_dashboard",
            display_name="Revenue Dashboard",
            entity_type="dashboard",
            platform="looker",
            domain="Finance",
            description="Executive dashboard showing current revenue performance.",
            owners=[finance_owner],
            tags=["dashboard", "revenue", "executive"],
            upstream_assets=[
                AssetReference(
                    urn=revenue_model_urn,
                    name="revenue_model",
                    display_name="Revenue Model",
                    entity_type="dataset",
                    platform="dbt",
                )
            ],
            last_updated=utc_now(),
            quality_status="critical",
        )

        forecast_model = AssetContext(
            urn=forecast_model_urn,
            name="monthly_forecast_model",
            display_name="Monthly Forecast Model",
            entity_type="ml_model",
            platform="python",
            domain="Finance",
            description="Monthly revenue forecasting model.",
            owners=[finance_owner],
            tags=["ml", "forecast", "revenue"],
            upstream_assets=[
                AssetReference(
                    urn=revenue_model_urn,
                    name="revenue_model",
                    display_name="Revenue Model",
                    entity_type="dataset",
                    platform="dbt",
                )
            ],
            last_updated=utc_now(),
            quality_status="warning",
        )

        return {
            asset.urn: asset
            for asset in [
                raw_customers,
                raw_orders,
                clean_orders,
                revenue_model,
                revenue_dashboard,
                forecast_model,
            ]
        }