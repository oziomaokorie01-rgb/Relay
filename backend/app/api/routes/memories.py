from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status

from.app.api.dependencies import (
    MemoryReuseServiceDependency,
    MemoryServiceDependency,
)
from.app.schemas.memory import MemoryResponse
from.app.schemas.memory_reuse import MemoryReuseEventResponse
from.app.services.memory import MemoryNotFoundError


router = APIRouter(
    prefix="/memories",
    tags=["Memories"],
)


@router.get(
    "",
    response_model=list[MemoryResponse],
)
async def list_memories(
    memory_service: MemoryServiceDependency,
    q: str | None = Query(
        default=None,
        max_length=200,
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=100,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
) -> list[MemoryResponse]:
    """
    List or search verified Relay memories.
    """

    if q and q.strip():
        memories = await memory_service.search_verified(
            q,
            limit=limit,
        )
    else:
        memories = await memory_service.list_verified(
            limit=limit,
            offset=offset,
        )

    return [
        MemoryResponse.model_validate(memory)
        for memory in memories
    ]


@router.get(
    "/{memory_id}/reuse",
    response_model=list[MemoryReuseEventResponse],
)
async def get_memory_reuse_history(
    memory_id: str,
    memory_service: MemoryServiceDependency,
    memory_reuse_service: MemoryReuseServiceDependency,
) -> list[MemoryReuseEventResponse]:
    """
    Return every later investigation that reused this verified memory.
    """

    try:
        await memory_service.get_by_id(memory_id)
    except MemoryNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    events = await memory_reuse_service.list_for_memory(
        memory_id
    )

    return [
        MemoryReuseEventResponse.model_validate(event)
        for event in events
    ]


@router.get(
    "/{memory_id}",
    response_model=MemoryResponse,
)
async def get_memory(
    memory_id: str,
    memory_service: MemoryServiceDependency,
) -> MemoryResponse:
    """
    Retrieve one Relay memory by ID.
    """

    try:
        memory = await memory_service.get_by_id(memory_id)
    except MemoryNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return MemoryResponse.model_validate(memory)