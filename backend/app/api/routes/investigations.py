from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status

from.app.api.dependencies import (
    AgentActivityServiceDependency,
    EvidenceServiceDependency,
    HumanApprovalServiceDependency,
    InvestigationOrchestratorDependency,
    InvestigationServiceDependency,
    InvestigationStateMachineDependency,
    MemoryReuseServiceDependency,
    RepairProposalServiceDependency,
    ReviewServiceDependency,
)
from.app.schemas.approval import (
    HumanApprovalInput,
    HumanApprovalResponse,
)
from.app.schemas.memory_reuse import MemoryReuseEventResponse
from.app.schemas.memory import (
    InvestigationArchiveResponse,
    MemoryResponse,
)
from.app.schemas.review import ReviewResponse
from.app.services.review import ReviewNotFoundError
from.app.schemas.repair_proposal import RepairProposalResponse
from.app.services.repair_proposal import RepairProposalNotFoundError
from.app.models.agent_activity import ActivityStatus, AgentName
from.app.models.investigation import InvestigationStatus
from.app.schemas.evidence import EvidenceResponse
from.app.orchestration.state_machine import (
    InvalidInvestigationTransitionError,
)
from.app.schemas.agent_activity import AgentActivityResponse
from.app.schemas.investigation import (
    InvestigationCreate,
    InvestigationCreated,
    InvestigationDetail,
    InvestigationSummary,
)
from.app.services.investigation import InvestigationNotFoundError


router = APIRouter(
    prefix="/investigations",
    tags=["Investigations"],
)


@router.post(
    "",
    response_model=InvestigationCreated,
    status_code=status.HTTP_201_CREATED,
)
async def create_investigation(
    payload: InvestigationCreate,
    service: InvestigationServiceDependency,
) -> InvestigationCreated:
    investigation = await service.create(payload)

    return InvestigationCreated(
        id=investigation.id,
        status=investigation.status,
    )


@router.get(
    "",
    response_model=list[InvestigationSummary],
)
async def list_investigations(
    service: InvestigationServiceDependency,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[InvestigationSummary]:
    investigations = await service.list_all(
        limit=limit,
        offset=offset,
    )

    return [
        InvestigationSummary.model_validate(investigation)
        for investigation in investigations
    ]


@router.get(
    "/{investigation_id}/activity",
    response_model=list[AgentActivityResponse],
)
async def get_investigation_activity(
    investigation_id: str,
    investigation_service: InvestigationServiceDependency,
    activity_service: AgentActivityServiceDependency,
) -> list[AgentActivityResponse]:
    try:
        await investigation_service.get_by_id(investigation_id)
    except InvestigationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    activities = await activity_service.list_for_investigation(
        investigation_id
    )

    return [
        AgentActivityResponse.model_validate(activity)
        for activity in activities
    ]

@router.get(
    "/{investigation_id}/evidence",
    response_model=list[EvidenceResponse],
)
async def get_investigation_evidence(
    investigation_id: str,
    investigation_service: InvestigationServiceDependency,
    evidence_service: EvidenceServiceDependency,
) -> list[EvidenceResponse]:
    """
    Return all persisted evidence for an investigation.
    """

    try:
        await investigation_service.get_by_id(investigation_id)
    except InvestigationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    evidence = await evidence_service.list_for_investigation(
        investigation_id
    )

    return [
        EvidenceResponse.model_validate(item)
        for item in evidence
    ]
@router.get(
    "/{investigation_id}/repair",
    response_model=RepairProposalResponse,
)
async def get_investigation_repair(
    investigation_id: str,
    investigation_service: InvestigationServiceDependency,
    repair_service: RepairProposalServiceDependency,
) -> RepairProposalResponse:
    """
    Return the newest repair proposal for an investigation.
    """

    try:
        await investigation_service.get_by_id(investigation_id)

        proposal = await repair_service.get_for_investigation(
            investigation_id
        )

    except InvestigationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except RepairProposalNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return RepairProposalResponse.model_validate(proposal)
@router.get(
    "/{investigation_id}/review",
    response_model=ReviewResponse,
)
async def get_investigation_review(
    investigation_id: str,
    investigation_service: InvestigationServiceDependency,
    review_service: ReviewServiceDependency,
) -> ReviewResponse:
    """
    Return the newest Reviewer decision for an investigation.
    """

    try:
        await investigation_service.get_by_id(investigation_id)

        review = await review_service.get_for_investigation(
            investigation_id
        )

    except InvestigationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except ReviewNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return ReviewResponse.model_validate(review)
@router.post(
    "/{investigation_id}/approval",
    response_model=HumanApprovalResponse,
)
async def submit_investigation_approval(
    investigation_id: str,
    payload: HumanApprovalInput,
    investigation_service: InvestigationServiceDependency,
    review_service: ReviewServiceDependency,
    approval_service: HumanApprovalServiceDependency,
    state_machine: InvestigationStateMachineDependency,
    activity_service: AgentActivityServiceDependency,
) -> HumanApprovalResponse:
    """
    Record the human decision made after Reviewer validation.
    """

    try:
        investigation = await investigation_service.get_by_id(
            investigation_id
        )

        if investigation.status != InvestigationStatus.AWAITING_APPROVAL:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Human approval requires an investigation in "
                    "awaiting_approval status."
                ),
            )

        review = await review_service.get_for_investigation(
            investigation_id
        )

        approval = await approval_service.create(
            investigation_id=investigation.id,
            review_id=review.id,
            approval=payload,
        )

        await activity_service.record(
            investigation_id=investigation.id,
            agent_name=AgentName.HUMAN,
            event_type="human.approval_recorded",
            status=ActivityStatus.COMPLETED,
            message=(
                f"Human decision recorded: {approval.decision.value}."
            ),
            structured_payload={
                "approval_id": approval.id,
                "review_id": review.id,
                "decision": approval.decision.value,
                "notes": approval.notes,
            },
        )

        if payload.decision == "approve":
            investigation = await state_machine.transition(
                investigation,
                InvestigationStatus.ARCHIVING,
                message=(
                    "Human approval recorded. The Archivist Agent may now "
                    "create organizational memory."
                ),
            )

            response_message = (
                "Approval recorded. Investigation is ready for archiving."
            )

        elif payload.decision == "request_revision":
            investigation = await state_machine.transition(
                investigation,
                InvestigationStatus.REPAIRING,
                message="Human reviewer requested a revised repair proposal.",
            )

            response_message = (
                "Revision requested. Investigation returned to Repair."
            )

        else:
            investigation = await state_machine.transition(
                investigation,
                InvestigationStatus.CANCELLED,
                message=(
                    "Human reviewer rejected the investigation for "
                    "organizational preservation."
                ),
            )

            response_message = (
                "Investigation rejected and cancelled."
            )

    except InvestigationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except ReviewNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except InvalidInvestigationTransitionError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return HumanApprovalResponse(
        investigation_id=investigation.id,
        decision=payload.decision,
        status=investigation.status.value,
        message=response_message,
    )
@router.post(
    "/{investigation_id}/archive",
    response_model=InvestigationArchiveResponse,
)
async def archive_investigation(
    investigation_id: str,
    orchestrator: InvestigationOrchestratorDependency,
) -> InvestigationArchiveResponse:
    """
    Run the Archivist Agent and create verified organizational memory.
    """

    try:
        investigation, memory = await orchestrator.archive(
            investigation_id
        )

    except InvestigationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    except InvalidInvestigationTransitionError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Memory creation failed: {exc}",
        ) from exc

    return InvestigationArchiveResponse(
        investigation_id=investigation.id,
        investigation_status=investigation.status.value,
        memory=MemoryResponse.model_validate(memory),
    )
@router.get(
    "/{investigation_id}/memory-reuse",
    response_model=list[MemoryReuseEventResponse],
)
async def get_investigation_memory_reuse(
    investigation_id: str,
    investigation_service: InvestigationServiceDependency,
    memory_reuse_service: MemoryReuseServiceDependency,
) -> list[MemoryReuseEventResponse]:
    """
    Return all verified memories inherited by an investigation.
    """

    try:
        await investigation_service.get_by_id(investigation_id)
    except InvestigationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    events = await memory_reuse_service.list_for_investigation(
        investigation_id
    )

    return [
        MemoryReuseEventResponse.model_validate(event)
        for event in events
    ]
@router.get(
    "/{investigation_id}",
    response_model=InvestigationDetail,
)
async def get_investigation(
    investigation_id: str,
    service: InvestigationServiceDependency,
) -> InvestigationDetail:
    try:
        investigation = await service.get_by_id(investigation_id)
    except InvestigationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return InvestigationDetail.model_validate(investigation)


@router.post(
    "/{investigation_id}/run",
    response_model=InvestigationDetail,
    status_code=status.HTTP_202_ACCEPTED,
)
async def run_investigation(
    investigation_id: str,
    service: InvestigationServiceDependency,
    state_machine: InvestigationStateMachineDependency,
    orchestrator: InvestigationOrchestratorDependency,
) -> InvestigationDetail:
    """
Start an investigation, gather DataHub context, and run the Investigator.

Current workflow:

draft
→ queued
→ gathering_context
→ investigating
→ repairing
"""

    try:
        investigation = await service.get_by_id(investigation_id)

        investigation = await state_machine.transition(
            investigation,
            InvestigationStatus.QUEUED,
            message="Investigation queued for DataHub context gathering.",
        )

        investigation = await orchestrator.run(
    investigation.id
)

    except InvestigationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except InvalidInvestigationTransitionError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Context gathering failed: {exc}",
        ) from exc

    return InvestigationDetail.model_validate(investigation)