from __future__ import annotations

from app.agents.archivist import ArchivistAgent
from app.agents.investigator import InvestigatorAgent
from app.agents.repair import RepairAgent
from app.agents.reviewer import ReviewerAgent
from app.core.config import get_settings
from app.models.agent_activity import (
    ActivityStatus,
    AgentName,
)
from app.models.investigation import (
    Investigation,
    InvestigationStatus,
)
from app.models.memory import RelayMemory
from app.models.memory_reuse_event import MemoryReuseType
from app.models.repair_proposal import RepairProposalStatus
from app.orchestration.state_machine import InvestigationStateMachine
from app.repositories.investigation import InvestigationRepository
from app.services.agent_activity import AgentActivityService
from app.services.datahub_context import DataHubContextService
from app.services.evidence import EvidenceService
from app.services.human_approval import HumanApprovalService
from app.services.investigation import InvestigationService
from app.services.memory import MemoryService
from app.services.memory_reuse import MemoryReuseService
from app.services.repair_proposal import RepairProposalService
from app.services.review import ReviewService


settings = get_settings()


class InvestigationOrchestrator:
    """
    Coordinates Relay's complete investigation and archival workflow.

    Investigation workflow:

    queued
    → gathering_context
    → investigating
    → repairing
    → reviewing
    → awaiting_approval

    Archival workflow:

    archiving
    → completed
    """

    def __init__(
        self,
        investigation_service: InvestigationService,
        investigation_repository: InvestigationRepository,
        state_machine: InvestigationStateMachine,
        context_service: DataHubContextService,
        activity_service: AgentActivityService,
        evidence_service: EvidenceService,
        repair_proposal_service: RepairProposalService,
        review_service: ReviewService,
        human_approval_service: HumanApprovalService,
        memory_service: MemoryService,
        memory_reuse_service: MemoryReuseService,
        investigator_agent: InvestigatorAgent,
        repair_agent: RepairAgent,
        reviewer_agent: ReviewerAgent,
        archivist_agent: ArchivistAgent,
    ) -> None:
        self.investigation_service = investigation_service
        self.investigation_repository = investigation_repository
        self.state_machine = state_machine
        self.context_service = context_service
        self.activity_service = activity_service
        self.evidence_service = evidence_service
        self.repair_proposal_service = repair_proposal_service
        self.review_service = review_service
        self.human_approval_service = human_approval_service
        self.memory_service = memory_service
        self.memory_reuse_service = memory_reuse_service
        self.investigator_agent = investigator_agent
        self.repair_agent = repair_agent
        self.reviewer_agent = reviewer_agent
        self.archivist_agent = archivist_agent

    async def run(
        self,
        investigation_id: str,
    ) -> Investigation:
        """
        Run context gathering, investigation, repair, and review.
        """

        investigation = await self.investigation_service.get_by_id(
            investigation_id
        )

        if investigation.status != InvestigationStatus.QUEUED:
            raise ValueError(
                "Investigation orchestration requires queued status."
            )

        try:
            investigation = await self._gather_context(investigation)
            investigation = await self._run_investigator(investigation)
            investigation = await self._run_repair(investigation)
            investigation = await self._run_reviewer(investigation)

            return investigation

        except Exception as exc:
            if investigation.status in {
                InvestigationStatus.GATHERING_CONTEXT,
                InvestigationStatus.INVESTIGATING,
                InvestigationStatus.REPAIRING,
                InvestigationStatus.REVIEWING,
                InvestigationStatus.ARCHIVING,
            }:
                await self.state_machine.transition(
                    investigation,
                    InvestigationStatus.FAILED,
                    message="Relay investigation failed.",
                    failure_message=str(exc),
                )

            raise

    async def archive(
        self,
        investigation_id: str,
    ) -> tuple[Investigation, RelayMemory]:
        """
        Run the Archivist after explicit human approval.

        Workflow:

        archiving
        → completed
        """

        investigation = await self.investigation_service.get_by_id(
            investigation_id
        )

        if investigation.status != InvestigationStatus.ARCHIVING:
            raise ValueError(
                "Archivist requires an investigation in archiving status."
            )

        try:
            approval = (
                await self.human_approval_service.require_approval(
                    investigation.id
                )
            )

            review = await self.review_service.get_for_investigation(
                investigation.id
            )

            proposal = (
                await self.repair_proposal_service.get_for_investigation(
                    investigation.id
                )
            )

            evidence = await self.evidence_service.list_for_investigation(
                investigation.id
            )

            await self.activity_service.record(
                investigation_id=investigation.id,
                agent_name=AgentName.ARCHIVIST,
                event_type="agent.started",
                status=ActivityStatus.STARTED,
                message=(
                    "Archivist Agent started converting the approved "
                    "investigation into organizational memory."
                ),
                structured_payload={
                    "agent": AgentName.ARCHIVIST.value,
                    "approval_id": approval.id,
                    "review_id": review.id,
                    "repair_proposal_id": proposal.id,
                },
            )

            archivist_result = await self.archivist_agent.run(
                investigation=investigation,
                proposal=proposal,
                review=review,
                approval=approval,
                evidence=evidence,
            )

            memory = await self.memory_service.create_verified(
                investigation_id=investigation.id,
                result=archivist_result,
            )

            await self.activity_service.record(
                investigation_id=investigation.id,
                agent_name=AgentName.ARCHIVIST,
                event_type="memory.created",
                status=ActivityStatus.COMPLETED,
                message=(
                    "Verified organizational memory was created and linked "
                    "to the affected DataHub asset."
                ),
                structured_payload={
                    "memory_id": memory.id,
                    "memory_key": memory.memory_key,
                    "version": memory.version,
                    "primary_asset_urn": memory.primary_asset_urn,
                    "confidence": memory.confidence,
                    "verification_status": (
                        memory.verification_status.value
                    ),
                },
            )

            await self.activity_service.record(
                investigation_id=investigation.id,
                agent_name=AgentName.ARCHIVIST,
                event_type="agent.completed",
                status=ActivityStatus.COMPLETED,
                message="Archivist Agent completed memory creation.",
                structured_payload={
                    "memory_id": memory.id,
                },
            )

            investigation = await self.state_machine.transition(
                investigation,
                InvestigationStatus.COMPLETED,
                message=(
                    "Investigation completed and verified memory stored."
                ),
            )

            return investigation, memory

        except Exception as exc:
            if investigation.status == InvestigationStatus.ARCHIVING:
                await self.state_machine.transition(
                    investigation,
                    InvestigationStatus.FAILED,
                    message="Relay could not create organizational memory.",
                    failure_message=str(exc),
                )

            raise

    async def _gather_context(
        self,
        investigation: Investigation,
    ) -> Investigation:
        """
        Retrieve and persist DataHub metadata and lineage.
        """

        investigation = await self.state_machine.transition(
            investigation,
            InvestigationStatus.GATHERING_CONTEXT,
            message="Relay is retrieving DataHub metadata and lineage.",
        )

        await self.activity_service.record(
            investigation_id=investigation.id,
            agent_name=AgentName.SYSTEM,
            event_type="datahub.context_started",
            status=ActivityStatus.IN_PROGRESS,
            message="Retrieving asset metadata and lineage from DataHub.",
            structured_payload={
                "asset_urn": investigation.asset_urn,
            },
        )

        context_snapshot = await self.context_service.gather(
            investigation.asset_urn,
            upstream_depth=3,
            downstream_depth=2,
        )

        investigation = (
            await self.investigation_repository.update_context_snapshot(
                investigation,
                context_snapshot,
            )
        )

        await self.activity_service.record(
            investigation_id=investigation.id,
            agent_name=AgentName.SYSTEM,
            event_type="datahub.context_loaded",
            status=ActivityStatus.COMPLETED,
            message="DataHub context was retrieved and stored.",
            structured_payload={
                "asset_urn": investigation.asset_urn,
                "summary": context_snapshot["summary"],
            },
        )

        return await self.state_machine.transition(
            investigation,
            InvestigationStatus.INVESTIGATING,
            message="DataHub context is ready for the Investigator Agent.",
        )

    async def _run_investigator(
        self,
        investigation: Investigation,
    ) -> Investigation:
        """
        Find relevant verified memories, run the Investigator Agent,
        persist evidence, and record any inherited precedent.
        """

        await self.activity_service.record(
            investigation_id=investigation.id,
            agent_name=AgentName.INVESTIGATOR,
            event_type="agent.started",
            status=ActivityStatus.STARTED,
            message="Investigator Agent started analyzing DataHub context.",
            structured_payload={
                "agent": AgentName.INVESTIGATOR.value,
            },
        )

        inherited_memories = await self._find_relevant_memories(
            investigation
        )

        result = await self.investigator_agent.run(
            investigation_title=investigation.title,
            investigation_description=investigation.description,
            context_snapshot=investigation.context_snapshot,
            previous_verified_memories=inherited_memories,
        )

        stored_evidence = await self.evidence_service.create_many(
            investigation_id=investigation.id,
            items=result.evidence,
            created_by_agent=AgentName.INVESTIGATOR.value,
        )

        investigation = await self.investigation_repository.update_findings(
            investigation,
            root_cause_summary=result.suspected_root_cause,
            overall_confidence=result.confidence,
        )

        await self.activity_service.record(
            investigation_id=investigation.id,
            agent_name=AgentName.INVESTIGATOR,
            event_type="evidence.created",
            status=ActivityStatus.COMPLETED,
            message=(
                f"Investigator Agent produced "
                f"{len(stored_evidence)} evidence records."
            ),
            structured_payload={
                "evidence_ids": [
                    evidence.id for evidence in stored_evidence
                ],
                "confidence": result.confidence,
                "affected_assets": result.affected_assets,
                "inherited_memories": [
                    reference.model_dump(mode="json")
                    for reference in result.inherited_memories
                ],
                "unresolved_questions": result.unresolved_questions,
                "reasoning_summary": result.reasoning_summary,
            },
        )

        await self.activity_service.record(
            investigation_id=investigation.id,
            agent_name=AgentName.INVESTIGATOR,
            event_type="agent.completed",
            status=ActivityStatus.COMPLETED,
            message="Investigator Agent completed its analysis.",
            structured_payload={
                "root_cause": result.suspected_root_cause,
                "confidence": result.confidence,
                "inherited_memory_count": len(inherited_memories),
            },
        )

        return await self.state_machine.transition(
            investigation,
            InvestigationStatus.REPAIRING,
            message="Investigator findings are ready for the Repair Agent.",
        )

    async def _find_relevant_memories(
        self,
        investigation: Investigation,
    ) -> list[RelayMemory]:
        """
        Find and record the strongest verified memory precedent.

        The MVP inherits at most one memory so the demo remains clear and
        deterministic.
        """

        verified_memories = await self.memory_service.list_verified(
            limit=100,
            offset=0,
        )

        lineage = investigation.context_snapshot.get("lineage", {})
        nodes = lineage.get("nodes", [])

        related_asset_urns = [
            node["urn"]
            for node in nodes
            if isinstance(node, dict) and node.get("urn")
        ]

        candidates: list[tuple[RelayMemory, float]] = []

        for memory in verified_memories:
            if memory.originating_investigation_id == investigation.id:
                continue

            similarity = self.memory_reuse_service.calculate_similarity(
                memory=memory,
                investigation=investigation,
                related_asset_urns=related_asset_urns,
            )

            if similarity >= settings.memory_inheritance_threshold:
                candidates.append((memory, similarity))

        candidates.sort(
            key=lambda item: item[1],
            reverse=True,
        )

        if not candidates:
            await self.activity_service.record(
                investigation_id=investigation.id,
                agent_name=AgentName.INVESTIGATOR,
                event_type="memory.search_completed",
                status=ActivityStatus.COMPLETED,
                message=(
                    "No sufficiently relevant verified memory was found. "
                    "Relay will investigate from the beginning."
                ),
                structured_payload={
                    "threshold": settings.memory_inheritance_threshold,
                    "candidate_count": 0,
                },
            )

            return []

        memory, similarity = candidates[0]

        reuse_event = await self.memory_reuse_service.record(
            memory=memory,
            investigation=investigation,
            similarity_score=similarity,
            reuse_type=MemoryReuseType.ROOT_CAUSE_PRECEDENT,
            agent_explanation=(
                "The verified memory describes the same revenue asset, "
                "customer_id schema-change pattern, downstream join failure, "
                "and reviewed repair approach."
            ),
            accepted=True,
            estimated_steps_skipped=2,
            estimated_time_saved_minutes=20,
        )

        await self.activity_service.record(
            investigation_id=investigation.id,
            agent_name=AgentName.INVESTIGATOR,
            event_type="memory.inherited",
            status=ActivityStatus.COMPLETED,
            message=(
                "Relay found and inherited a verified resolution from an "
                "earlier investigation."
            ),
            structured_payload={
                "memory_id": memory.id,
                "memory_title": memory.title,
                "originating_investigation_id": (
                    memory.originating_investigation_id
                ),
                "reuse_event_id": reuse_event.id,
                "similarity_score": similarity,
                "estimated_steps_skipped": (
                    reuse_event.estimated_steps_skipped
                ),
                "estimated_time_saved_minutes": (
                    reuse_event.estimated_time_saved_minutes
                ),
            },
        )

        return [memory]

    async def _run_repair(
        self,
        investigation: Investigation,
    ) -> Investigation:
        """
        Run the Repair Agent and persist its proposed repair.
        """

        await self.activity_service.record(
            investigation_id=investigation.id,
            agent_name=AgentName.REPAIR,
            event_type="agent.started",
            status=ActivityStatus.STARTED,
            message="Repair Agent started generating a supported proposal.",
            structured_payload={
                "agent": AgentName.REPAIR.value,
            },
        )

        evidence = await self.evidence_service.list_for_investigation(
            investigation.id
        )

        lineage = investigation.context_snapshot.get("lineage", {})
        nodes = lineage.get("nodes", [])

        affected_asset_urns = [
            node["urn"]
            for node in nodes
            if isinstance(node, dict) and node.get("urn")
        ]

        if (
            investigation.asset_urn
            and investigation.asset_urn not in affected_asset_urns
        ):
            affected_asset_urns.insert(0, investigation.asset_urn)

        repair_result = await self.repair_agent.run(
            root_cause_summary=investigation.root_cause_summary or "",
            affected_asset_urns=affected_asset_urns,
            evidence=evidence,
        )

        proposal = await self.repair_proposal_service.create(
            investigation_id=investigation.id,
            result=repair_result,
        )

        await self.activity_service.record(
            investigation_id=investigation.id,
            agent_name=AgentName.REPAIR,
            event_type="repair.created",
            status=ActivityStatus.COMPLETED,
            message="Repair Agent generated and stored a repair proposal.",
            structured_payload={
                "repair_proposal_id": proposal.id,
                "artifact_type": proposal.artifact_type.value,
                "risk_level": proposal.risk_level.value,
                "confidence": proposal.confidence,
                "evidence_ids": proposal.evidence_ids,
            },
        )

        await self.activity_service.record(
            investigation_id=investigation.id,
            agent_name=AgentName.REPAIR,
            event_type="agent.completed",
            status=ActivityStatus.COMPLETED,
            message="Repair Agent completed its proposal.",
            structured_payload={
                "repair_proposal_id": proposal.id,
                "summary": proposal.summary,
            },
        )

        await self.repair_proposal_service.mark_under_review(
            proposal
        )

        return await self.state_machine.transition(
            investigation,
            InvestigationStatus.REVIEWING,
            message="Repair proposal is ready for Reviewer validation.",
        )

    async def _run_reviewer(
        self,
        investigation: Investigation,
    ) -> Investigation:
        """
        Run the Reviewer Agent and persist its verification decision.
        """

        await self.activity_service.record(
            investigation_id=investigation.id,
            agent_name=AgentName.REVIEWER,
            event_type="agent.started",
            status=ActivityStatus.STARTED,
            message="Reviewer Agent started validating the repair proposal.",
            structured_payload={
                "agent": AgentName.REVIEWER.value,
            },
        )

        evidence = await self.evidence_service.list_for_investigation(
            investigation.id
        )

        proposal = (
            await self.repair_proposal_service.get_for_investigation(
                investigation.id
            )
        )

        reviewer_result = await self.reviewer_agent.run(
            proposal=proposal,
            evidence=evidence,
            context_snapshot=investigation.context_snapshot,
            minimum_confidence=settings.review_minimum_confidence,
        )

        review = await self.review_service.create(
            investigation_id=investigation.id,
            repair_proposal_id=proposal.id,
            result=reviewer_result,
        )

        await self.activity_service.record(
            investigation_id=investigation.id,
            agent_name=AgentName.REVIEWER,
            event_type="review.created",
            status=ActivityStatus.COMPLETED,
            message="Reviewer Agent completed validation.",
            structured_payload={
                "review_id": review.id,
                "decision": review.decision.value,
                "confidence": review.confidence,
                "conditions": review.conditions,
                "missing_evidence": review.missing_evidence,
            },
        )

        await self.activity_service.record(
            investigation_id=investigation.id,
            agent_name=AgentName.REVIEWER,
            event_type="agent.completed",
            status=ActivityStatus.COMPLETED,
            message="Reviewer Agent completed its assessment.",
            structured_payload={
                "review_id": review.id,
                "decision": review.decision.value,
            },
        )

        if reviewer_result.decision in {
            "approved",
            "approved_with_conditions",
        }:
            await self.repair_proposal_service.update_status(
                proposal,
                RepairProposalStatus.APPROVED,
            )

            return await self.state_machine.transition(
                investigation,
                InvestigationStatus.AWAITING_APPROVAL,
                message=(
                    "Reviewer validation passed. Human approval is required "
                    "before creating organizational memory."
                ),
            )

        if reviewer_result.decision == "needs_revision":
            await self.repair_proposal_service.update_status(
                proposal,
                RepairProposalStatus.NEEDS_REVISION,
            )

            return await self.state_machine.transition(
                investigation,
                InvestigationStatus.REPAIRING,
                message="Reviewer requested a revised repair proposal.",
            )

        await self.repair_proposal_service.update_status(
            proposal,
            RepairProposalStatus.REJECTED,
        )

        raise ValueError("Reviewer rejected the repair proposal.")