from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_user_id
from app.db.session import get_db
from app.schemas.memory import MemoryCreate, MemoryOut, MemoryReviewRequest, MemoryUpdate
from app.services.memory_service import (
    create_memory,
    get_memory,
    list_memories,
    list_review_queue_with_filters,
    review_memory,
    update_memory,
)

router = APIRouter(prefix="/api/v1/memories", tags=["memories"])


@router.get("", response_model=list[MemoryOut])
def get_memories(
    status: Literal["ACTIVE", "SUPERSEDED", "REJECTED", "PENDING_REVIEW"] | None = None,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    return list_memories(db, user_id=user_id, status=status)


@router.get("/review-queue", response_model=list[MemoryOut])
def get_review_queue(
    status: Literal["ACTIVE", "SUPERSEDED", "REJECTED", "PENDING_REVIEW"] | None = "PENDING_REVIEW",
    memory_type: str | None = Query(default=None, alias="type", min_length=2, max_length=64),
    sort_by: Literal["created_at", "updated_at", "confidence", "importance"] = "updated_at",
    order: Literal["asc", "desc"] = "desc",
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    return list_review_queue_with_filters(
        db=db,
        user_id=user_id,
        status=status,
        memory_type=memory_type,
        sort_by=sort_by,
        order=order,
    )


@router.get("/{memory_id}", response_model=MemoryOut)
def get_memory_by_id(memory_id: int, db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    memory = get_memory(db=db, user_id=user_id, memory_id=memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    return memory


@router.post("", response_model=MemoryOut, status_code=status.HTTP_201_CREATED)
def post_memory(payload: MemoryCreate, db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    return create_memory(db, user_id=user_id, payload=payload)


@router.patch("/{memory_id}", response_model=MemoryOut)
def patch_memory(memory_id: int, payload: MemoryUpdate, db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    memory = get_memory(db=db, user_id=user_id, memory_id=memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    try:
        return update_memory(db, memory, payload)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_memory(memory_id: int, db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    memory = get_memory(db=db, user_id=user_id, memory_id=memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    db.delete(memory)
    db.commit()
    return None


@router.post("/{memory_id}/review", response_model=MemoryOut)
def post_memory_review(
    memory_id: int,
    payload: MemoryReviewRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    memory = get_memory(db=db, user_id=user_id, memory_id=memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    try:
        return review_memory(db=db, memory=memory, payload=payload, user_id=user_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
