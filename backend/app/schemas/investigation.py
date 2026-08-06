from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.investigation import (
    InvestigationPriority,
    InvestigationStatus,
)


class InvestigationCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=10, max_length=5000)
    asset_urn: str = Field(min_length=5, max_length=2000)
    priority: InvestigationPriority = InvestigationPriority.NORMAL


class InvestigationUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = Field(
        default=None,
        min_length=10,
        max_length=5000,
    )
    priority: InvestigationPriority | None = None


class InvestigationSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    asset_urn: str
    priority: InvestigationPriority
    status: InvestigationStatus
    current_agent: str | None
    overall_confidence: float | None
    created_at: datetime
    updated_at: datetime


class InvestigationDetail(InvestigationSummary):
    description: str
    context_snapshot: dict
    root_cause_summary: str | None
    failure_message: str | None
    completed_at: datetime | None


class InvestigationCreated(BaseModel):
    id: str
    status: InvestigationStatus