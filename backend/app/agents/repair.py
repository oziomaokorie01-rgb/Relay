from __future__ import annotations

from app.models.evidence import Evidence
from app.schemas.repair import (
    RepairResult,
    RepairTest,
)


class RepairAgent:
    """
    Deterministic Repair Agent for Relay's hackathon workflow.

    It generates a structured SQL repair proposal from the Investigator's
    persisted findings and evidence.
    """

    async def run(
        self,
        *,
        root_cause_summary: str,
        affected_asset_urns: list[str],
        evidence: list[Evidence],
    ) -> RepairResult:
        if not root_cause_summary.strip():
            raise ValueError(
                "Repair Agent requires a root-cause summary."
            )

        if not affected_asset_urns:
            raise ValueError(
                "Repair Agent requires at least one affected asset."
            )

        if not evidence:
            raise ValueError(
                "Repair Agent requires persisted investigation evidence."
            )

        evidence_ids = [item.id for item in evidence]

        clean_orders_urn = self._find_asset_urn(
            affected_asset_urns,
            "clean_orders",
        )

        raw_orders_urn = self._find_asset_urn(
            affected_asset_urns,
            "raw_orders",
        )

        primary_repair_asset = clean_orders_urn or affected_asset_urns[0]

        sql_artifact = """select
    order_id,
    try_cast(customer_id as integer) as customer_id,
    order_total,
    created_at
from {{ source('commerce', 'raw_orders') }}
where try_cast(customer_id as integer) is not null
"""

        validation_test = """select
    customer_id
from {{ ref('clean_orders') }}
where customer_id is null
"""

        failed_cast_test = """select
    customer_id
from {{ source('commerce', 'raw_orders') }}
where customer_id is not null
  and try_cast(customer_id as integer) is null
"""

        affected_assets = [
            asset_urn
            for asset_urn in [
                raw_orders_urn,
                primary_repair_asset,
            ]
            if asset_urn is not None
        ]

        if not affected_assets:
            affected_assets = affected_asset_urns

        return RepairResult(
            proposal_summary=(
                "Update the clean_orders transformation to explicitly cast "
                "raw_orders.customer_id to an integer before the downstream "
                "join. Exclude failed casts from the production result and "
                "surface them through a dedicated data quality test."
            ),
            artifact_type="sql",
            artifact_content=sql_artifact,
            language="sql",
            affected_assets=affected_assets,
            risk_level="medium",
            expected_outcome=(
                "Valid customer identifiers will once again match the integer "
                "join key used by clean_orders. Revenue rows should flow into "
                "revenue_model and restore the dashboard totals."
            ),
            rollback_plan=(
                "Revert the clean_orders model to its previous revision and "
                "temporarily cast the upstream source field outside the model "
                "if the proposed change causes unexpected row loss."
            ),
            tests=[
                RepairTest(
                    name="customer_id not-null validation",
                    description=(
                        "Verify that the repaired clean_orders model does not "
                        "produce null customer identifiers."
                    ),
                    artifact=validation_test,
                ),
                RepairTest(
                    name="failed customer_id cast detection",
                    description=(
                        "Identify source values that cannot safely be converted "
                        "to integers before they reach the revenue pipeline."
                    ),
                    artifact=failed_cast_test,
                ),
            ],
            assumptions=[
                (
                    "The downstream clean_orders join is intended to continue "
                    "using an integer customer_id."
                ),
                (
                    "Non-numeric customer identifiers should be quarantined "
                    "rather than silently coerced."
                ),
                (
                    "The generated SQL is a recommendation and will not be "
                    "executed automatically by Relay."
                ),
            ],
            evidence_ids=evidence_ids,
            confidence=0.93,
        )

    @staticmethod
    def _find_asset_urn(
        asset_urns: list[str],
        asset_name: str,
    ) -> str | None:
        normalized_name = asset_name.lower()

        for urn in asset_urns:
            if normalized_name in urn.lower():
                return urn

        return None