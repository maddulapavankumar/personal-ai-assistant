from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.memory import Memory
from app.schemas.memory import MemoryCreate, MemoryUpdate


def list_memories(db: Session, user_id: str) -> list[Memory]:
    return list(db.scalars(select(Memory).where(Memory.user_id == user_id).order_by(Memory.updated_at.desc())))


def create_memory(db: Session, user_id: str, payload: MemoryCreate) -> Memory:
    memory = Memory(user_id=user_id, **payload.model_dump())
    db.add(memory)
    db.commit()
    db.refresh(memory)
    return memory


def update_memory(db: Session, memory: Memory, payload: MemoryUpdate) -> Memory:
    update_values = payload.model_dump(exclude_unset=True)
    for key, value in update_values.items():
        setattr(memory, key, value)
    db.add(memory)
    db.commit()
    db.refresh(memory)
    return memory

