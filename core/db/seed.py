'''
Copyright 2019-Present The OpenUBA Platform Authors
database seed data for development and testing
'''

import logging
import uuid
from datetime import datetime

from passlib.hash import bcrypt
from sqlalchemy.orm import Session

from core.db.connection import SessionLocal
from core.db.models import (
    User, RolePermission, Environment, Model,
)

logger = logging.getLogger(__name__)

# default admin user
DEFAULT_ADMIN = {
    "username": "admin",
    "email": "admin@openuba.local",
    "password": "admin",
    "role": "admin",
    "display_name": "Platform Admin",
}

# default role permissions
DEFAULT_PERMISSIONS = [
    # admin - full access
    {"role": "admin", "page": "models", "can_read": True, "can_write": True},
    {"role": "admin", "page": "anomalies", "can_read": True, "can_write": True},
    {"role": "admin", "page": "entities", "can_read": True, "can_write": True},
    {"role": "admin", "page": "cases", "can_read": True, "can_write": True},
    {"role": "admin", "page": "rules", "can_read": True, "can_write": True},
    {"role": "admin", "page": "alerts", "can_read": True, "can_write": True},
    {"role": "admin", "page": "settings", "can_read": True, "can_write": True},
    {"role": "admin", "page": "workspaces", "can_read": True, "can_write": True},
    {"role": "admin", "page": "datasets", "can_read": True, "can_write": True},
    {"role": "admin", "page": "jobs", "can_read": True, "can_write": True},
    {"role": "admin", "page": "visualizations", "can_read": True, "can_write": True},
    {"role": "admin", "page": "dashboards", "can_read": True, "can_write": True},
    {"role": "admin", "page": "features", "can_read": True, "can_write": True},
    {"role": "admin", "page": "experiments", "can_read": True, "can_write": True},
    {"role": "admin", "page": "hyperparameters", "can_read": True, "can_write": True},
    {"role": "admin", "page": "pipelines", "can_read": True, "can_write": True},
    # analyst - read most, write some
    {"role": "analyst", "page": "models", "can_read": True, "can_write": False},
    {"role": "analyst", "page": "anomalies", "can_read": True, "can_write": True},
    {"role": "analyst", "page": "entities", "can_read": True, "can_write": False},
    {"role": "analyst", "page": "cases", "can_read": True, "can_write": True},
    {"role": "analyst", "page": "rules", "can_read": True, "can_write": False},
    {"role": "analyst", "page": "alerts", "can_read": True, "can_write": True},
    {"role": "analyst", "page": "workspaces", "can_read": True, "can_write": True},
    {"role": "analyst", "page": "datasets", "can_read": True, "can_write": True},
    {"role": "analyst", "page": "jobs", "can_read": True, "can_write": True},
    {"role": "analyst", "page": "visualizations", "can_read": True, "can_write": True},
    {"role": "analyst", "page": "dashboards", "can_read": True, "can_write": True},
    {"role": "analyst", "page": "features", "can_read": True, "can_write": True},
    {"role": "analyst", "page": "experiments", "can_read": True, "can_write": True},
    {"role": "analyst", "page": "hyperparameters", "can_read": True, "can_write": True},
    {"role": "analyst", "page": "pipelines", "can_read": True, "can_write": True},
    # triage - read only
    {"role": "triage", "page": "anomalies", "can_read": True, "can_write": False},
    {"role": "triage", "page": "cases", "can_read": True, "can_write": True},
    {"role": "triage", "page": "alerts", "can_read": True, "can_write": True},
    {"role": "triage", "page": "entities", "can_read": True, "can_write": False},
]

# default environments
DEFAULT_ENVIRONMENTS = [
    {
        "name": "default",
        "display_name": "Default Python",
        "description": "Standard Python environment with common ML packages",
        "docker_image": "openuba-workspace:latest",
        "default_packages": ["numpy", "pandas", "scikit-learn", "matplotlib"],
    },
    {
        "name": "pytorch",
        "display_name": "PyTorch",
        "description": "PyTorch environment for deep learning models",
        "docker_image": "openuba-workspace:pytorch",
        "default_packages": ["torch", "torchvision", "numpy", "pandas"],
    },
    {
        "name": "tensorflow",
        "display_name": "TensorFlow",
        "description": "TensorFlow/Keras environment for deep learning",
        "docker_image": "openuba-workspace:tensorflow",
        "default_packages": ["tensorflow", "keras", "numpy", "pandas"],
    },
]


def seed_database(db: Session = None):
    '''seed the database with default data'''
    own_session = db is None
    if own_session:
        db = SessionLocal()

    try:
        _seed_admin_user(db)
        _seed_permissions(db)
        _seed_environments(db)
        if own_session:
            db.commit()
        logger.info("database seeded successfully")
    except Exception as e:
        if own_session:
            db.rollback()
        logger.error(f"failed to seed database: {e}")
        raise
    finally:
        if own_session:
            db.close()


def _seed_admin_user(db: Session):
    '''create default admin user if not exists'''
    existing = db.query(User).filter(User.username == DEFAULT_ADMIN["username"]).first()
    if existing:
        logger.debug("admin user already exists")
        return

    user = User(
        id=uuid.uuid4(),
        username=DEFAULT_ADMIN["username"],
        email=DEFAULT_ADMIN["email"],
        password_hash=bcrypt.hash(DEFAULT_ADMIN["password"]),
        role=DEFAULT_ADMIN["role"],
        display_name=DEFAULT_ADMIN["display_name"],
        is_active=True,
    )
    db.add(user)
    db.flush()
    logger.info("admin user created")


def _seed_permissions(db: Session):
    '''create default role permissions if not exist'''
    existing_count = db.query(RolePermission).count()
    if existing_count > 0:
        logger.debug(f"role permissions already exist ({existing_count})")
        return

    for perm in DEFAULT_PERMISSIONS:
        db.add(RolePermission(id=uuid.uuid4(), **perm))
    db.flush()
    logger.info(f"created {len(DEFAULT_PERMISSIONS)} role permissions")


def _seed_environments(db: Session):
    '''create default workspace environments if not exist'''
    for env_data in DEFAULT_ENVIRONMENTS:
        existing = db.query(Environment).filter(Environment.name == env_data["name"]).first()
        if existing:
            continue
        db.add(Environment(id=uuid.uuid4(), **env_data))
    db.flush()
    logger.info(f"seeded {len(DEFAULT_ENVIRONMENTS)} environments")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    seed_database()
