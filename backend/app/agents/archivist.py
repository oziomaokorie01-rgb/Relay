from __future__ import annotations

from.app.models.evidence import Evidence
from.app.models.human_approval import HumanApproval
from.app.models.investigation import Investigation
from.app.models.repair_proposal import RepairProposal
from.app.models.review import Review
from.app.schemas.archivist import ArchivistResult


class ArchivistAgent:
    """
    Deterministic Archivist Agent for Relay's hackathon workflow.

    It converts a reviewed and human-approved investigation into a
    structured, reusable organizational memory candidate.
    """

    async def run(
        self,
        *,
        investigation: Investigation,
        proposal: RepairProposal,
        review: Review,
        approval: HumanApproval,
        evidence: list[Evidence],
    ) -> ArchivistResult:
        if approval.decision.value != "approve":
            raise ValueError(
                "Archivist requires explicit human approval."
            )

        if review.decision.value not in {
            "approved",
            "approved_with_conditions",
        }:
            raise ValueError(
                "Archivist requires an approved Reviewer decision."
            )

        if not evidence:
            raise ValueError(
                "Archivist requires persisted supporting evidence."
            )

        evidence_ids = [item.id for item in evidence]

        approved_title = (
            approval.edited_title.strip()
            if approval.edited_title
            else "Revenue join failed after customer_id schema change"
        )

        approved_summary = (
            approval.edited_summary.strip()
            if approval.edited_summary
            else (
                "A source schema change converted raw_orders.customer_id "
                "from integer to string. The downstream clean_orders model "
                "continued expecting an integer key, causing join failures "
                "and reducing rows reaching revenue reporting."
            )
        )

        lineage = investigation.context_snapshot.get("lineage", {})
        nodes = lineage.get("nodes", [])

        related_asset_urns = [
            node["urn"]
            for node in nodes
            if isinstance(node, dict)
            and node.get("urn")
            and node["urn"] != investigation.asset_urn
        ]

        memory_confidence = min(
            investigation.overall_confidence or 0.0,
            proposal.confidence,
            review.confidence,
        )

        return ArchivistResult(
            memory_key="schema-change-customer-id-revenue",
            title=approved_title,
            summary=approved_summary,
            incident_type="schema_change",
            root_cause=investigation.root_cause_summary or approved_summary,
            resolution=(
                proposal.summary
                + "\n\n"
                + (proposal.artifact_content or "")
            ),
            confidence=memory_confidence,
            keywords=[
                "customer_id",
                "schema change",
                "revenue",
                "clean_orders",
                "raw_orders",
                "join failure",
            ],
            primary_asset_urn=investigation.asset_urn,
            related_asset_urns=related_asset_urns,
            evidence_ids=evidence_ids,
            supersedes_memory_id=None,
        )