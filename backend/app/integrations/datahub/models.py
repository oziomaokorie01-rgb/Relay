from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


AssetEntityType = Literal[
    "dataset",
    "dashboard",
    "chart",
    "data_job",
    "ml_model",
]


class AssetOwner(BaseModel):
    name: str
    type: str = "group"
    email: str | None = None


class SchemaField(BaseModel):
    name: str
    data_type: str
    description: str | None = None
    nullable: bool = True


class AssetSummary(BaseModel):
    urn: str
    name: str
    display_name: str
    entity_type: AssetEntityType
    platform: str
    owner: str | None = None
    domain: str | None = None
    description: str | None = None


class AssetReference(BaseModel):
    urn: str
    name: str
    display_name: str
    entity_type: AssetEntityType
    platform: str


class AssetContext(BaseModel):
    urn: str
    name: str
    display_name: str
    entity_type: AssetEntityType
    platform: str
    domain: str | None = None
    description: str | None = None

    owners: list[AssetOwner] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    schema_fields: list[SchemaField] = Field(default_factory=list)

    upstream_assets: list[AssetReference] = Field(default_factory=list)
    downstream_assets: list[AssetReference] = Field(default_factory=list)

    last_updated: datetime | None = None
    quality_status: str | None = None
    memory_count: int = 0

    metadata: dict[str, Any] = Field(default_factory=dict)


class LineageNode(BaseModel):
    id: str
    urn: str
    label: str
    entity_type: AssetEntityType
    platform: str
    depth: int = 0


class LineageEdge(BaseModel):
    source: str
    target: str
    direction: Literal["upstream", "downstream"]


class LineageGraph(BaseModel):
    root_urn: str
    nodes: list[LineageNode] = Field(default_factory=list)
    edges: list[LineageEdge] = Field(default_factory=list)