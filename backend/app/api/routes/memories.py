from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_user_id
from app.db.session import get_db
from app.models.memory import Memory
from app.schemas.memory import MemoryCreate, MemoryOut, MemoryUpdate
from app.services.memory_service import create_memory, list_memories, update_memory

router = APIRouter(prefix="/api/v1/memories", tags=["memories"])


@router.get("", response_model=list[MemoryOut])
def get_memories(
    status: Literal["ACTIVE", "SUPERSEDED", "REJECTED"] | None = None,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_user_id),
):
    return list_memories(db, user_id=user_id, status=status)


@router.post("", response_model=MemoryOut, status_code=status.HTTP_201_CREATED)
def post_memory(payload: MemoryCreate, db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    return create_memory(db, user_id=user_id, payload=payload)


@router.patch("/{memory_id}", response_model=MemoryOut)
def patch_memory(memory_id: int, payload: MemoryUpdate, db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    memory = db.get(Memory, memory_id)
    if not memory or memory.user_id != user_id:
        raise HTTPException(status_code=404, detail="Memory not found")
    return update_memory(db, memory, payload)


@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_memory(memory_id: int, db: Session = Depends(get_db), user_id: str = Depends(get_user_id)):
    memory = db.get(Memory, memory_id)
    if not memory or memory.user_id != user_id:
        raise HTTPException(status_code=404, detail="Memory not found")
    db.delete(memory)
    db.commit()
    return None
