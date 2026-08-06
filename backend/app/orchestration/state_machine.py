from __future__ import annotations

from backend.app.models.agent_activity import (
    ActivityStatus,
    AgentName,
)
from backend.app.models.investigation import (
    Investigation,
    InvestigationStatus,
)
from backend.app.repositories.investigation import InvestigationRepository
from backend.app.services.agent_activity import AgentActivityService


class InvalidInvestigationTransitionError(Exception):
    """
    Raised when Relay attempts an invalid investigation state transition.
    """


ALLOWED_TRANSITIONS: dict[
    InvestigationStatus,
    set[InvestigationStatus],
] = {
    InvestigationStatus.DRAFT: {
        InvestigationStatus.QUEUED,
    },
    InvestigationStatus.QUEUED: {
        InvestigationStatus.GATHERING_CONTEXT,
        InvestigationStatus.CANCELLED,
    },
    InvestigationStatus.GATHERING_CONTEXT: {
        InvestigationStatus.INVESTIGATING,
        InvestigationStatus.FAILED,
    },
    InvestigationStatus.INVESTIGATING: {
        InvestigationStatus.REPAIRING,
        InvestigationStatus.FAILED,
    },
    InvestigationStatus.REPAIRING: {
        InvestigationStatus.REVIEWING,
        InvestigationStatus.FAILED,
    },
    InvestigationStatus.REVIEWING: {
        InvestigationStatus.REPAIRING,
        InvestigationStatus.AWAITING_APPROVAL,
        InvestigationStatus.FAILED,
    },
    InvestigationStatus.AWAITING_APPROVAL: {
        InvestigationStatus.ARCHIVING,
        InvestigationStatus.REPAIRING,
        InvestigationStatus.CANCELLED,
    },
    InvestigationStatus.ARCHIVING: {
        InvestigationStatus.COMPLETED,
        InvestigationStatus.FAILED,
    },
    InvestigationStatus.COMPLETED: set(),
    InvestigationStatus.FAILED: set(),
    InvestigationStatus.CANCELLED: set(),
}


STATUS_AGENT_MAP: dict[InvestigationStatus, AgentName] = {
    InvestigationStatus.DRAFT: AgentName.HUMAN,
    InvestigationStatus.QUEUED: AgentName.SYSTEM,
    InvestigationStatus.GATHERING_CONTEXT: AgentName.SYSTEM,
    InvestigationStatus.INVESTIGATING: AgentName.INVESTIGATOR,
    InvestigationStatus.REPAIRING: AgentName.REPAIR,
    InvestigationStatus.REVIEWING: AgentName.REVIEWER,
    InvestigationStatus.AWAITING_APPROVAL: AgentName.HUMAN,
    InvestigationStatus.ARCHIVING: AgentName.ARCHIVIST,
    InvestigationStatus.COMPLETED: AgentName.SYSTEM,
    InvestigationStatus.FAILED: AgentName.SYSTEM,
    InvestigationStatus.CANCELLED: AgentName.HUMAN,
}


class InvestigationStateMachine:
    """
    Validates and persists Relay investigation workflow transitions.
    """

    def __init__(
        self,
        investigation_repository: InvestigationRepository,
        activity_service: AgentActivityService,
    ) -> None:
        self.investigation_repository = investigation_repository
        self.activity_service = activity_service

    def can_transition(
        self,
        current_status: InvestigationStatus,
        target_status: InvestigationStatus,
    ) -> bool:
        """
        Return whether a transition is allowed.
        """

        return target_status in ALLOWED_TRANSITIONS[current_status]

    async def transition(
        self,
        investigation: Investigation,
        target_status: InvestigationStatus,
        *,
        message: str | None = None,
        failure_message: str | None = None,
    ) -> Investigation:
        """
        Validate, record, and persist one workflow transition.
        """

        current_status = investigation.status

        if not self.can_transition(current_status, target_status):
            raise InvalidInvestigationTransitionError(
                "Invalid investigation transition: "
                f"{current_status.value} -> {target_status.value}."
            )

        agent_name = STATUS_AGENT_MAP[target_status]

        activity_status = self._activity_status_for(target_status)

        event_message = message or (
            f"Investigation moved from "
            f"{current_status.value} to {target_status.value}."
        )

        updated_investigation = (
            await self.investigation_repository.update_status(
                investigation,
                status=target_status,
                current_agent=self._current_agent_for(target_status),
                failure_message=failure_message,
            )
        )

        await self.activity_service.record(
            investigation_id=updated_investigation.id,
            agent_name=agent_name,
            event_type="investigation.status_changed",
            status=activity_status,
            message=event_message,
            structured_payload={
                "previous_status": current_status.value,
                "current_status": target_status.value,
            },
        )

        return updated_investigation

    @staticmethod
    def _current_agent_for(
        status: InvestigationStatus,
    ) -> str | None:
        """
        Return the active agent name shown on the investigation record.
        """

        terminal_statuses = {
            InvestigationStatus.COMPLETED,
            InvestigationStatus.FAILED,
            InvestigationStatus.CANCELLED,
        }

        if status in terminal_statuses:
            return None

        return STATUS_AGENT_MAP[status].value

    @staticmethod
    def _activity_status_for(
        status: InvestigationStatus,
    ) -> ActivityStatus:
        """
        Map an investigation status to its audit-event status.
        """

        if status == InvestigationStatus.COMPLETED:
            return ActivityStatus.COMPLETED

        if status == InvestigationStatus.FAILED:
            return ActivityStatus.FAILED

        if status == InvestigationStatus.CANCELLED:
            return ActivityStatus.CANCELLED

        if status == InvestigationStatus.AWAITING_APPROVAL:
            return ActivityStatus.WARNING

        return ActivityStatus.IN_PROGRESS