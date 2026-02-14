from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Any, Dict
from pydantic import BaseModel
from uuid import UUID

from core.db import get_db
from core.db.models import SourceGroup

router = APIRouter(prefix="/source_groups", tags=["source_groups"])

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

@router.get("/", response_model=List[SourceGroupRead])
def list_source_groups(db: Session = Depends(get_db)):
    return db.query(SourceGroup).all()

@router.get("/{group_id}", response_model=SourceGroupRead)
def get_source_group(group_id: UUID, db: Session = Depends(get_db)):
    sg = db.query(SourceGroup).filter(SourceGroup.id == group_id).first()
    if not sg:
        raise HTTPException(status_code=404, detail="SourceGroup not found")
    return sg

@router.post("/", response_model=SourceGroupRead)
def create_source_group(sg: SourceGroupCreate, db: Session = Depends(get_db)):
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
    return db_sg

@router.put("/{group_id}", response_model=SourceGroupRead)
def update_source_group(group_id: UUID, sg: SourceGroupCreate, db: Session = Depends(get_db)):
    db_sg = db.query(SourceGroup).filter(SourceGroup.id == group_id).first()
    if not db_sg:
        raise HTTPException(status_code=404, detail="SourceGroup not found")
    
    db_sg.slug = sg.slug
    db_sg.description = sg.description
    db_sg.config = sg.config
    db.commit()
    db.refresh(db_sg)
    return db_sg
