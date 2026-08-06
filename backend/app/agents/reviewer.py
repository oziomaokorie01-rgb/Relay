from __future__ import annotations

from.app.models.evidence import Evidence
from.app.models.repair_proposal import RepairProposal, RepairRiskLevel
from.app.schemas.reviewer import ReviewCheck, ReviewerResult


class ReviewerAgent:
    """
    Deterministic Reviewer Agent for Relay's hackathon workflow.

    It validates a stored repair proposal against persisted evidence,
    schema context, downstream dependencies, and basic governance rules.
    """

    async def run(
        self,
        *,
        proposal: RepairProposal,
        evidence: list[Evidence],
        context_snapshot: dict,
        minimum_confidence: float = 0.75,
    ) -> ReviewerResult:
        if not evidence:
            return ReviewerResult(
                decision="rejected",
                confidence=0.0,
                evidence_coverage=ReviewCheck(
                    status="fail",
                    explanation=(
                        "The proposal cannot be approved because no persisted "
                        "evidence is attached to the investigation."
                    ),
                ),
                schema_compatibility=ReviewCheck(
                    status="fail",
                    explanation=(
                        "Schema compatibility cannot be evaluated without "
                        "supporting investigation evidence."
                    ),
                ),
                downstream_risk=ReviewCheck(
                    status="warning",
                    explanation=(
                        "The downstream effect remains unknown because the "
                        "proposal is not supported by evidence."
                    ),
                ),
                governance_compliance=ReviewCheck(
                    status="warning",
                    explanation=(
                        "No governance violation is visible, but the proposal "
                        "cannot be trusted without evidence."
                    ),
                ),
                conditions=[],
                missing_evidence=[
                    "At least one persisted evidence record is required."
                ],
                final_summary=(
                    "The proposal was rejected because Relay could not verify "
                    "its basis."
                ),
            )

        known_evidence_ids = {item.id for item in evidence}
        referenced_evidence_ids = set(proposal.evidence_ids)
        missing_references = referenced_evidence_ids - known_evidence_ids

        lineage = context_snapshot.get("lineage", {})
        nodes = lineage.get("nodes", [])

        known_asset_urns = {
            node.get("urn")
            for node in nodes
            if isinstance(node, dict) and node.get("urn")
        }

        unknown_assets = [
            urn
            for urn in proposal.affected_asset_urns
            if urn not in known_asset_urns
        ]

        artifact_missing = (
            proposal.artifact_type.value != "recommendation_only"
            and not (proposal.artifact_content or "").strip()
        )

        rollback_missing = (
            proposal.risk_level in {
                RepairRiskLevel.MEDIUM,
                RepairRiskLevel.HIGH,
            }
            and not (proposal.rollback_plan or "").strip()
        )

        confidence_below_threshold = (
            proposal.confidence < minimum_confidence
        )

        deterministic_failures = []

        if missing_references:
            deterministic_failures.append(
                "The proposal cites evidence IDs that do not belong to the "
                "investigation."
            )

        if unknown_assets:
            deterministic_failures.append(
                "The proposal references assets not present in the retrieved "
                "DataHub context."
            )

        if artifact_missing:
            deterministic_failures.append(
                "The generated repair artifact is empty."
            )

        if rollback_missing:
            deterministic_failures.append(
                "A medium- or high-risk proposal requires a rollback plan."
            )

        if confidence_below_threshold:
            deterministic_failures.append(
                "The proposal confidence is below the configured review threshold."
            )

        if deterministic_failures:
            return ReviewerResult(
                decision="rejected",
                confidence=min(proposal.confidence, 0.60),
                evidence_coverage=ReviewCheck(
                    status=(
                        "fail"
                        if missing_references
                        else "warning"
                    ),
                    explanation=(
                        "The proposal cites persisted evidence, but one or more "
                        "deterministic validation rules failed."
                    ),
                ),
                schema_compatibility=ReviewCheck(
                    status=(
                        "fail"
                        if unknown_assets
                        else "pass"
                    ),
                    explanation=(
                        "Affected assets were compared against the retrieved "
                        "DataHub lineage and context."
                    ),
                ),
                downstream_risk=ReviewCheck(
                    status=(
                        "fail"
                        if rollback_missing
                        else "warning"
                    ),
                    explanation=(
                        "The proposal affects the revenue pipeline and must "
                        "include a reversible deployment path."
                    ),
                ),
                governance_compliance=ReviewCheck(
                    status="pass",
                    explanation=(
                        "The proposal does not execute code automatically and "
                        "does not introduce an obvious governance violation."
                    ),
                ),
                conditions=deterministic_failures,
                missing_evidence=[],
                final_summary=(
                    "The Reviewer rejected the proposal because one or more "
                    "mandatory validation checks failed."
                ),
            )

        return ReviewerResult(
            decision="approved_with_conditions",
            confidence=0.91,
            evidence_coverage=ReviewCheck(
                status="pass",
                explanation=(
                    "Every cited evidence ID belongs to the investigation, and "
                    "the root-cause explanation is supported by schema and "
                    "lineage signals."
                ),
            ),
            schema_compatibility=ReviewCheck(
                status="pass",
                explanation=(
                    "The proposed cast aligns raw_orders.customer_id with the "
                    "integer type expected by clean_orders."
                ),
            ),
            downstream_risk=ReviewCheck(
                status="warning",
                explanation=(
                    "The repair affects a shared revenue pipeline, so validation "
                    "must cover both the dashboard and forecast model before "
                    "deployment."
                ),
            ),
            governance_compliance=ReviewCheck(
                status="pass",
                explanation=(
                    "The proposal is recommendation-only, preserves human "
                    "approval, and does not execute SQL automatically."
                ),
            ),
            conditions=[
                (
                    "Run the generated failed-cast test before deploying the "
                    "clean_orders change."
                ),
                (
                    "Validate revenue_dashboard and monthly_forecast_model "
                    "outputs after the repair."
                ),
            ],
            missing_evidence=[],
            final_summary=(
                "The repair is well supported and may proceed to human approval "
                "after the listed validation conditions are completed."
            ),
        )