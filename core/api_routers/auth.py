'''
Copyright 2019-Present The OpenUBA Platform Authors
authentication router — login, user management, roles, permissions
'''

import logging
from typing import Optional, List, Dict
from datetime import timedelta, datetime
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from sqlalchemy import text

from core.db import get_db, User, RolePermission, Notification
from core.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

logger = logging.getLogger(__name__)

router = APIRouter()

VALID_ROLES = ["admin", "manager", "triage", "analyst"]
ALL_PAGES = ["home", "data", "models", "rules", "alerts", "entities", "anomalies", "cases", "schedules", "settings", "users"]


# --- pydantic models ---

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    username: str
    role: str


class UserCreate(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    password: str
    role: str = "analyst"
    display_name: Optional[str] = None


class UserUpdate(BaseModel):
    role: Optional[str] = None
    display_name: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


class PermissionEntry(BaseModel):
    read: bool = False
    write: bool = False


class UserResponse(BaseModel):
    id: str
    username: str
    email: Optional[str] = None
    role: str
    display_name: Optional[str] = None
    is_active: bool = True
    last_login_at: Optional[str] = None
    created_at: str
    permissions: Optional[Dict[str, PermissionEntry]] = None

    class Config:
        from_attributes = True


class RolePermissionsUpdate(BaseModel):
    role: str
    permissions: Dict[str, PermissionEntry]


# --- auth endpoints ---

@router.post("/auth/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    '''login and return jwt token'''
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if hasattr(user, 'is_active') and not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="account is disabled"
        )

    # update last login
    try:
        user.last_login_at = datetime.utcnow()
        db.commit()
    except Exception:
        db.rollback()

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.username,
            "user_id": str(user.id),
            "role": user.role,
        },
        expires_delta=access_token_expires
    )

    logger.info(f"user {user.username} logged in")
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": str(user.id),
        "username": user.username,
        "role": user.role,
    }


@router.get("/auth/me")
async def get_current_user_info(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    '''get current user information with permissions'''
    user = db.query(User).filter(User.username == current_user["username"]).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")

    # load permissions for role
    permissions = _get_role_permissions(db, user.role)

    return {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "display_name": user.display_name,
        "is_active": user.is_active if hasattr(user, 'is_active') else True,
        "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
        "created_at": user.created_at.isoformat() if user.created_at else "",
        "permissions": permissions,
    }


# --- user management (admin) ---

@router.post("/auth/register", status_code=201)
async def register(
    user_data: UserCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    '''create new user (admin only)'''
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin access required")

    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="username already registered")

    if user_data.role not in VALID_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"invalid role, must be one of: {', '.join(VALID_ROLES)}"
        )

    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        role=user_data.role,
        display_name=user_data.display_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    logger.info(f"user {user.username} created with role {user.role}")
    return {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "display_name": user.display_name,
        "is_active": True,
        "created_at": user.created_at.isoformat() if user.created_at else "",
    }


@router.get("/auth/users")
async def list_users(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    '''list all users (admin and manager)'''
    if current_user.get("role") not in ["admin", "manager"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin or manager access required")

    users = db.query(User).offset(skip).limit(limit).all()
    return [
        {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "display_name": user.display_name,
            "is_active": user.is_active if hasattr(user, 'is_active') else True,
            "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
            "created_at": user.created_at.isoformat() if user.created_at else "",
        }
        for user in users
    ]


@router.put("/auth/users/{user_id}")
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    '''update user (admin only)'''
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin access required")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")

    if user_data.role is not None:
        if user_data.role not in VALID_ROLES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"invalid role")
        user.role = user_data.role
    if user_data.display_name is not None:
        user.display_name = user_data.display_name
    if user_data.email is not None:
        user.email = user_data.email
    if user_data.is_active is not None:
        user.is_active = user_data.is_active
    if user_data.password is not None:
        user.password_hash = get_password_hash(user_data.password)

    db.commit()
    db.refresh(user)
    logger.info(f"user {user.username} updated by {current_user['username']}")
    return {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "display_name": user.display_name,
        "is_active": user.is_active if hasattr(user, 'is_active') else True,
    }


@router.delete("/auth/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    '''soft-delete user by deactivating (admin only)'''
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin access required")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")

    if user.username == current_user["username"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="cannot delete yourself")

    user.is_active = False
    db.commit()
    logger.info(f"user {user.username} deactivated by {current_user['username']}")
    return {"detail": f"user {user.username} deactivated"}


# --- roles & permissions ---

@router.get("/auth/roles")
async def list_roles(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    '''list all roles with their permissions'''
    if current_user.get("role") not in ["admin", "manager"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin or manager access required")

    result = {}
    for role in VALID_ROLES:
        result[role] = _get_role_permissions(db, role)
    return result


@router.get("/auth/permissions")
async def get_permissions_matrix(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    '''get full permissions matrix'''
    if current_user.get("role") not in ["admin", "manager"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin or manager access required")

    rows = db.query(RolePermission).all()
    matrix = {}
    for row in rows:
        if row.role not in matrix:
            matrix[row.role] = {}
        matrix[row.role][row.page] = {"read": row.can_read, "write": row.can_write}
    return matrix


@router.put("/auth/permissions")
async def update_permissions(
    data: RolePermissionsUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    '''update permissions for a role (admin only)'''
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin access required")

    if data.role not in VALID_ROLES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid role")

    if data.role == "admin":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="cannot modify admin permissions")

    for page, perm in data.permissions.items():
        if page not in ALL_PAGES:
            continue

        existing = db.query(RolePermission).filter(
            RolePermission.role == data.role,
            RolePermission.page == page
        ).first()

        if existing:
            existing.can_read = perm.read
            existing.can_write = perm.write
        else:
            db.add(RolePermission(
                role=data.role,
                page=page,
                can_read=perm.read,
                can_write=perm.write,
            ))

    db.commit()
    logger.info(f"permissions updated for role {data.role} by {current_user['username']}")
    return {"detail": f"permissions updated for role {data.role}"}


# --- helpers ---

def _get_role_permissions(db: Session, role: str) -> Dict[str, PermissionEntry]:
    '''load permissions for a role from DB'''
    permissions = {}
    if role == "admin":
        # admin always has full access
        for page in ALL_PAGES:
            permissions[page] = {"read": True, "write": True}
        return permissions

    rows = db.query(RolePermission).filter(RolePermission.role == role).all()
    for row in rows:
        permissions[row.page] = {"read": row.can_read, "write": row.can_write}

    # fill in missing pages as no access
    for page in ALL_PAGES:
        if page not in permissions:
            permissions[page] = {"read": False, "write": False}

    return permissions
