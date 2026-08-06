from __future__ import annotations

from typing import Any

from backend.app.models.memory import RelayMemory
from backend.app.schemas.investigator import (
    InheritedMemoryReference,
    InvestigatorEvidence,
    InvestigatorResult,
)


class InvestigatorAgent:
    """
    Deterministic Investigator used for Relay's hackathon workflow.

    It analyzes DataHub context and may inherit relevant, verified knowledge
    created by previous investigations.
    """

    async def run(
        self,
        *,
        investigation_title: str,
        investigation_description: str,
        context_snapshot: dict[str, Any],
        previous_verified_memories: list[RelayMemory] | None = None,
    ) -> InvestigatorResult:
        asset = context_snapshot.get("asset", {})
        lineage = context_snapshot.get("lineage", {})
        nodes = lineage.get("nodes", [])

        previous_verified_memories = previous_verified_memories or []

        root_asset_urn = asset.get("urn")

        affected_assets = [
            node["urn"]
            for node in nodes
            if isinstance(node, dict) and node.get("urn")
        ]

        if root_asset_urn and root_asset_urn not in affected_assets:
            affected_assets.insert(0, root_asset_urn)

        if not affected_assets:
            raise ValueError(
                "The Investigator cannot run without DataHub asset context."
            )

        raw_orders = self._find_asset_node(
            nodes,
            "raw_orders",
        )
        clean_orders = self._find_asset_node(
            nodes,
            "clean_orders",
        )
        revenue_model = self._find_asset_node(
            nodes,
            "revenue_model",
        )

        evidence = [
            InvestigatorEvidence(
                type="lineage_dependency",
                title="Revenue dashboard depends on the revenue model",
                description=(
                    "DataHub lineage shows that the selected revenue dashboard "
                    "is supplied by the revenue model. Downstream results "
                    "therefore depend on the health of that upstream chain."
                ),
                source_asset_urn=root_asset_urn,
                source_reference="context_snapshot.lineage",
                confidence=0.98,
            ),
            InvestigatorEvidence(
                type="quality_failure",
                title="Selected asset is in a critical quality state",
                description=(
                    "The selected dashboard is marked with a critical quality "
                    "status in the retrieved DataHub context."
                ),
                source_asset_urn=root_asset_urn,
                source_reference="context_snapshot.asset.quality_status",
                confidence=0.95,
            ),
        ]

        if raw_orders is not None:
            evidence.append(
                InvestigatorEvidence(
                    type="schema_change",
                    title="customer_id type changed in raw orders",
                    description=(
                        "The DataHub context records that customer_id in "
                        "raw_orders changed from integer to string. This "
                        "conflicts with the downstream clean_orders model, "
                        "which expects an integer join key."
                    ),
                    source_asset_urn=raw_orders["urn"],
                    source_reference=(
                        "mock_datahub.raw_orders.metadata.schema_change"
                    ),
                    confidence=0.99,
                )
            )

        if clean_orders is not None and revenue_model is not None:
            evidence.append(
                InvestigatorEvidence(
                    type="lineage_dependency",
                    title="Schema mismatch propagates into revenue reporting",
                    description=(
                        "clean_orders feeds revenue_model, which feeds the "
                        "dashboard. A join failure in clean_orders can therefore "
                        "reduce downstream revenue totals."
                    ),
                    source_asset_urn=clean_orders["urn"],
                    source_reference="context_snapshot.lineage.edges",
                    confidence=0.97,
                )
            )

        inherited_memories: list[InheritedMemoryReference] = []

        for memory in previous_verified_memories:
            inherited_memories.append(
                InheritedMemoryReference(
                    memory_id=memory.id,
                    relevance=memory.confidence,
                    usage=(
                        "Used the verified root-cause pattern, accepted casting "
                        "repair, and recommended schema-validation tests as "
                        "precedent for this investigation."
                    ),
                )
            )

            evidence.append(
                InvestigatorEvidence(
                    type="previous_memory",
                    title=f"Verified precedent: {memory.title}",
                    description=(
                        "Relay found a verified memory describing the same "
                        "customer_id schema-change pattern and its reviewed "
                        "resolution."
                    ),
                    source_asset_urn=memory.primary_asset_urn,
                    source_reference=f"relay_memory:{memory.id}",
                    confidence=memory.confidence,
                )
            )

        memory_context = ""

        if inherited_memories:
            memory_context = (
                " Relay also found a verified precedent supporting the same "
                "root-cause pattern and approved repair approach."
            )

        return InvestigatorResult(
            problem_summary=(
                f"{investigation_title}. {investigation_description}"
            ),
            suspected_root_cause=(
                "The customer_id field in raw_orders changed from an integer to a text value. Because clean_orders still expected an integer, many order records no longer matched during the join. As a result, fewer orders reached the revenue model, causing the Revenue Dashboard to under-report revenue by 35%."
            ),
            confidence=0.97 if inherited_memories else 0.96,
            affected_assets=affected_assets,
            evidence=evidence,
            inherited_memories=inherited_memories,
            unresolved_questions=[
                "When was the source schema change introduced?",
                "How many rows failed or were excluded by the affected join?",
            ],
            reasoning_summary=(
                "The selected dashboard is marked critical and depends on "
                "revenue_model. The lineage continues upstream through "
                "clean_orders to raw_orders. The recorded customer_id type "
                "change conflicts with the integer key expected downstream, "
                "providing a direct explanation for the revenue reduction."
                + memory_context
            ),
        )

    @staticmethod
    def _find_asset_node(
        nodes: list[dict[str, Any]],
        asset_name: str,
    ) -> dict[str, Any] | None:
        normalized_name = asset_name.lower()

        for node in nodes:
            if not isinstance(node, dict):
                continue

            label = str(node.get("label", "")).lower()
            urn = str(node.get("urn", "")).lower()

            if normalized_name in label or normalized_name in urn:
                return node

        return None