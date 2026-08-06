from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.agents.archivist import ArchivistAgent
from backend.app.agents.investigator import InvestigatorAgent
from backend.app.agents.repair import RepairAgent
from backend.app.agents.reviewer import ReviewerAgent
from backend.app.database.session import get_db
from backend.app.integrations.datahub.gateway import DataHubGateway
from backend.app.integrations.datahub.mock_gateway import MockDataHubGateway
from backend.app.orchestration.orchestrator import InvestigationOrchestrator
from backend.app.orchestration.state_machine import InvestigationStateMachine
from backend.app.repositories.agent_activity import AgentActivityRepository
from backend.app.repositories.evidence import EvidenceRepository
from backend.app.repositories.human_approval import HumanApprovalRepository
from backend.app.repositories.investigation import InvestigationRepository
from backend.app.repositories.memory import MemoryRepository
from backend.app.repositories.repair_proposal import RepairProposalRepository
from backend.app.repositories.review import ReviewRepository
from backend.app.repositories.memory_reuse_event import MemoryReuseEventRepository
from backend.app.services.memory_reuse import MemoryReuseService
from backend.app.services.agent_activity import AgentActivityService
from backend.app.services.datahub_context import DataHubContextService
from backend.app.services.evidence import EvidenceService
from backend.app.services.human_approval import HumanApprovalService
from backend.app.services.investigation import InvestigationService
from backend.app.services.memory import MemoryService
from backend.app.services.repair_proposal import RepairProposalService
from backend.app.services.review import ReviewService


DatabaseSession = Annotated[AsyncSession, Depends(get_db)]


def get_investigation_repository(
    session: DatabaseSession,
) -> InvestigationRepository:
    return InvestigationRepository(session)


InvestigationRepositoryDependency = Annotated[
    InvestigationRepository,
    Depends(get_investigation_repository),
]


def get_agent_activity_repository(
    session: DatabaseSession,
) -> AgentActivityRepository:
    return AgentActivityRepository(session)


AgentActivityRepositoryDependency = Annotated[
    AgentActivityRepository,
    Depends(get_agent_activity_repository),
]


def get_evidence_repository(
    session: DatabaseSession,
) -> EvidenceRepository:
    return EvidenceRepository(session)


EvidenceRepositoryDependency = Annotated[
    EvidenceRepository,
    Depends(get_evidence_repository),
]


def get_repair_proposal_repository(
    session: DatabaseSession,
) -> RepairProposalRepository:
    return RepairProposalRepository(session)


RepairProposalRepositoryDependency = Annotated[
    RepairProposalRepository,
    Depends(get_repair_proposal_repository),
]


def get_review_repository(
    session: DatabaseSession,
) -> ReviewRepository:
    return ReviewRepository(session)


ReviewRepositoryDependency = Annotated[
    ReviewRepository,
    Depends(get_review_repository),
]


def get_human_approval_repository(
    session: DatabaseSession,
) -> HumanApprovalRepository:
    return HumanApprovalRepository(session)


HumanApprovalRepositoryDependency = Annotated[
    HumanApprovalRepository,
    Depends(get_human_approval_repository),
]


def get_memory_repository(
    session: DatabaseSession,
) -> MemoryRepository:
    return MemoryRepository(session)


MemoryRepositoryDependency = Annotated[
    MemoryRepository,
    Depends(get_memory_repository),
]

def get_memory_reuse_event_repository(
    session: DatabaseSession,
) -> MemoryReuseEventRepository:
    return MemoryReuseEventRepository(session)


MemoryReuseEventRepositoryDependency = Annotated[
    MemoryReuseEventRepository,
    Depends(get_memory_reuse_event_repository),
]
def get_investigation_service(
    repository: InvestigationRepositoryDependency,
) -> InvestigationService:
    return InvestigationService(repository)


InvestigationServiceDependency = Annotated[
    InvestigationService,
    Depends(get_investigation_service),
]


def get_agent_activity_service(
    repository: AgentActivityRepositoryDependency,
) -> AgentActivityService:
    return AgentActivityService(repository)


AgentActivityServiceDependency = Annotated[
    AgentActivityService,
    Depends(get_agent_activity_service),
]


def get_evidence_service(
    repository: EvidenceRepositoryDependency,
) -> EvidenceService:
    return EvidenceService(repository)


EvidenceServiceDependency = Annotated[
    EvidenceService,
    Depends(get_evidence_service),
]


def get_repair_proposal_service(
    repository: RepairProposalRepositoryDependency,
) -> RepairProposalService:
    return RepairProposalService(repository)


RepairProposalServiceDependency = Annotated[
    RepairProposalService,
    Depends(get_repair_proposal_service),
]


def get_review_service(
    repository: ReviewRepositoryDependency,
) -> ReviewService:
    return ReviewService(repository)


ReviewServiceDependency = Annotated[
    ReviewService,
    Depends(get_review_service),
]


def get_human_approval_service(
    repository: HumanApprovalRepositoryDependency,
) -> HumanApprovalService:
    return HumanApprovalService(repository)


HumanApprovalServiceDependency = Annotated[
    HumanApprovalService,
    Depends(get_human_approval_service),
]


def get_memory_service(
    repository: MemoryRepositoryDependency,
) -> MemoryService:
    return MemoryService(repository)


MemoryServiceDependency = Annotated[
    MemoryService,
    Depends(get_memory_service),
]

def get_memory_reuse_service(
    repository: MemoryReuseEventRepositoryDependency,
) -> MemoryReuseService:
    return MemoryReuseService(repository)


MemoryReuseServiceDependency = Annotated[
    MemoryReuseService,
    Depends(get_memory_reuse_service),
]
def get_investigation_state_machine(
    investigation_repository: InvestigationRepositoryDependency,
    activity_service: AgentActivityServiceDependency,
) -> InvestigationStateMachine:
    return InvestigationStateMachine(
        investigation_repository=investigation_repository,
        activity_service=activity_service,
    )


InvestigationStateMachineDependency = Annotated[
    InvestigationStateMachine,
    Depends(get_investigation_state_machine),
]


def get_datahub_gateway() -> DataHubGateway:
    return MockDataHubGateway()


DataHubGatewayDependency = Annotated[
    DataHubGateway,
    Depends(get_datahub_gateway),
]


def get_datahub_context_service(
    gateway: DataHubGatewayDependency,
) -> DataHubContextService:
    return DataHubContextService(gateway)


DataHubContextServiceDependency = Annotated[
    DataHubContextService,
    Depends(get_datahub_context_service),
]


def get_investigator_agent() -> InvestigatorAgent:
    return InvestigatorAgent()


InvestigatorAgentDependency = Annotated[
    InvestigatorAgent,
    Depends(get_investigator_agent),
]


def get_repair_agent() -> RepairAgent:
    return RepairAgent()


RepairAgentDependency = Annotated[
    RepairAgent,
    Depends(get_repair_agent),
]


def get_reviewer_agent() -> ReviewerAgent:
    return ReviewerAgent()


ReviewerAgentDependency = Annotated[
    ReviewerAgent,
    Depends(get_reviewer_agent),
]


def get_archivist_agent() -> ArchivistAgent:
    return ArchivistAgent()


ArchivistAgentDependency = Annotated[
    ArchivistAgent,
    Depends(get_archivist_agent),
]


def get_investigation_orchestrator(
    investigation_service: InvestigationServiceDependency,
    investigation_repository: InvestigationRepositoryDependency,
    state_machine: InvestigationStateMachineDependency,
    context_service: DataHubContextServiceDependency,
    activity_service: AgentActivityServiceDependency,
    evidence_service: EvidenceServiceDependency,
    repair_proposal_service: RepairProposalServiceDependency,
    review_service: ReviewServiceDependency,
    human_approval_service: HumanApprovalServiceDependency,
    memory_service: MemoryServiceDependency,
    memory_reuse_service: MemoryReuseServiceDependency,
    investigator_agent: InvestigatorAgentDependency,
    repair_agent: RepairAgentDependency,
    reviewer_agent: ReviewerAgentDependency,
    archivist_agent: ArchivistAgentDependency,
) -> InvestigationOrchestrator:
    """
    Build Relay's complete investigation orchestrator for this request.
    """

    return InvestigationOrchestrator(
        investigation_service=investigation_service,
        investigation_repository=investigation_repository,
        state_machine=state_machine,
        context_service=context_service,
        activity_service=activity_service,
        evidence_service=evidence_service,
        repair_proposal_service=repair_proposal_service,
        review_service=review_service,
        human_approval_service=human_approval_service,
        memory_service=memory_service,
        memory_reuse_service=memory_reuse_service,
        investigator_agent=investigator_agent,
        repair_agent=repair_agent,
        reviewer_agent=reviewer_agent,
        archivist_agent=archivist_agent,
    )
InvestigationOrchestratorDependency = Annotated[
    InvestigationOrchestrator,
    Depends(get_investigation_orchestrator),
]