import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Any, Dict
from pydantic import BaseModel
from uuid import UUID

from core.auth import get_current_user
from core.db import get_db
from core.db.models import SourceGroup

router = APIRouter(prefix="/source_groups", tags=["source_groups"])
logger = logging.getLogger(__name__)

# Pydantic items
class SourceGroupBase(BaseModel):
    slug: str
    description: Optional[str] = None
    config: List[Dict[str, Any]]

class SourceGroupCreate(SourceGroupBase):
    pass

class SourceGroupRead(SourceGroupBase):
    id: UUID
    created_at: Any
    updated_at: Any

    class Config:
        orm_mode = True


def require_source_group_write_access(current_user: Any = Depends(get_current_user)):
    role = getattr(current_user, "role", None)
    roles = getattr(current_user, "roles", None)

    if isinstance(current_user, dict):
        role = role or current_user.get("role")
        roles = roles or current_user.get("roles")

    if role in {"admin", "editor"}:
        return current_user

    if isinstance(roles, (list, set, tuple)) and any(r in {"admin", "editor"} for r in roles):
        return current_user

    raise HTTPException(status_code=403, detail="Insufficient permissions")

@router.get("/", response_model=List[SourceGroupRead])
def list_source_groups(
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user)
):
    return db.query(SourceGroup).all()

@router.get("/{group_id}", response_model=SourceGroupRead)
def get_source_group(
    group_id: UUID,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user)
):
    sg = db.query(SourceGroup).filter(SourceGroup.id == group_id).first()
    if not sg:
        raise HTTPException(status_code=404, detail="SourceGroup not found")
    return sg

@router.post("/", response_model=SourceGroupRead)
def create_source_group(
    sg: SourceGroupCreate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_source_group_write_access)
):
    existing = db.query(SourceGroup).filter(SourceGroup.slug == sg.slug).first()
    if existing:
        raise HTTPException(status_code=400, detail="SourceGroup with this slug already exists")

    db_sg = SourceGroup(
        slug=sg.slug,
        description=sg.description,
        config=sg.config
    )
    db.add(db_sg)
    db.commit()
    db.refresh(db_sg)
    logger.info("source_group_created", extra={"source_group_id": str(db_sg.id), "actor": str(getattr(current_user, "id", None) or current_user.get("id") if isinstance(current_user, dict) else None)})
    return db_sg

@router.put("/{group_id}", response_model=SourceGroupRead)
def update_source_group(
    group_id: UUID,
    sg: SourceGroupCreate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(require_source_group_write_access)
):
    db_sg = db.query(SourceGroup).filter(SourceGroup.id == group_id).first()
    if not db_sg:
        raise HTTPException(status_code=404, detail="SourceGroup not found")

    db_sg.slug = sg.slug
    db_sg.description = sg.description
    db_sg.config = sg.config
    db.commit()
    db.refresh(db_sg)
    logger.info("source_group_updated", extra={"source_group_id": str(db_sg.id), "actor": str(getattr(current_user, "id", None) or current_user.get("id") if isinstance(current_user, dict) else None)})
    return db_sg
