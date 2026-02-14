'''
Copyright 2019-Present The OpenUBA Platform Authors
authentication and authorization
'''

import os
import logging
from typing import Optional
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import text

logger = logging.getLogger(__name__)

# security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)

# jwt settings
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480


def verify_password(plain_password: str, hashed_password: str) -> bool:
    '''
    verify a password against hash
    '''
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    '''
    hash a password
    '''
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    '''
    create jwt access token
    '''
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> dict:
    '''
    get current user from jwt token
    '''
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise credentials_exception

    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        return {
            "username": username,
            "user_id": payload.get("user_id"),
            "role": payload.get("role", "analyst"),
            "payload": payload,
        }
    except JWTError:
        raise credentials_exception


def require_permission(page: str, access: str = "read"):
    '''
    dependency factory that checks if the current user's role
    has the required permission for a page.
    admin role always passes.
    '''
    async def permission_checker(
        current_user: dict = Depends(get_current_user)
    ) -> dict:
        role = current_user.get("role", "analyst")

        # admin always has full access
        if role == "admin":
            return current_user

        # check role_permissions table
        from core.db import get_db_context
        try:
            with get_db_context() as db:
                row = db.execute(text(
                    "SELECT can_read, can_write FROM role_permissions "
                    "WHERE role = :role AND page = :page"
                ), {"role": role, "page": page}).fetchone()

                if not row:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"no permissions configured for role '{role}' on '{page}'"
                    )

                can_read, can_write = row[0], row[1]

                if access == "write" and not can_write:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"write access denied for role '{role}' on '{page}'"
                    )
                if access == "read" and not can_read:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"read access denied for role '{role}' on '{page}'"
                    )

        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"permission check failed: {e}")
            # if table doesn't exist yet or other error, allow access
            pass

        return current_user

    return permission_checker
