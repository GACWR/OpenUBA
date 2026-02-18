'''
Copyright 2019-Present The OpenUBA Platform Authors
migration script to migrate existing file-based data to postgresql
'''

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any

from core.db import get_db_context, init_db
from core.repositories.model_repository import ModelRepository
from core.repositories.anomaly_repository import AnomalyRepository

logger = logging.getLogger(__name__)


def migrate_models_from_json(storage_path: Path = Path("core/storage")):
    '''
    migrate models from models.json to postgresql
    '''
    models_file = storage_path / "models.json"
    if not models_file.exists():
        logger.warning(f"models.json not found at {models_file}")
        return

    with open(models_file, "r") as f:
        models_data = json.load(f)

    with get_db_context() as db:
        repo = ModelRepository(db)
        for group_name, group_data in models_data.items():
            models_list = group_data.get("models", [])
            for model_data in models_list:
                try:
                    # check if model already exists
                    existing = repo.get_by_name_version(
                        model_data.get("model_name"),
                        "1.0.0"  # default version
                    )
                    if existing:
                        logger.info(f"model {model_data.get('model_name')} already exists, skipping")
                        continue

                    # create model
                    model = repo.create(
                        name=model_data.get("model_name"),
                        slug=model_data.get("model_name"),
                        version="1.0.0",
                        source_type="local_fs",
                        description=model_data.get("description", ""),
                        manifest=model_data,
                        status="installed" if model_data.get("enabled") else "disabled",
                        enabled=model_data.get("enabled", True),
                        runtime=model_data.get("runtime", "python-base")
                    )

                    # add components
                    components = model_data.get("components", [])
                    for component in components:
                        repo.add_component(
                            model.id,
                            filename=component.get("filename"),
                            component_type=component.get("type", "external"),
                            file_hash=component.get("file_hash", ""),
                            data_hash=component.get("data_hash")
                        )

                    logger.info(f"migrated model: {model.name}")
                except Exception as e:
                    logger.error(f"error migrating model {model_data.get('model_name')}: {e}")


def migrate_users_from_json(storage_path: Path = Path("core/storage")):
    '''
    migrate users from users.json to postgresql
    '''
    users_file = storage_path / "users.json"
    if not users_file.exists():
        logger.warning(f"users.json not found at {users_file}")
        return

    with open(users_file, "r") as f:
        users_data = json.load(f)

    with get_db_context() as db:
        from core.db.models import User
        for user_data in users_data:
            try:
                # check if user exists
                existing = db.query(User).filter(
                    User.username == user_data.get("username")
                ).first()
                if existing:
                    continue

                user = User(
                    username=user_data.get("username", ""),
                    email=user_data.get("email"),
                    role=user_data.get("role", "analyst")
                )
                db.add(user)
                db.commit()
                logger.info(f"migrated user: {user.username}")
            except Exception as e:
                logger.error(f"error migrating user: {e}")


def run_migration():
    '''
    run all migrations
    '''
    logger.info("starting migration from file-based storage to postgresql")
    
    # initialize database
    init_db()
    
    # migrate models
    migrate_models_from_json()

    # migrate source groups
    migrate_source_groups_from_json()
    
    # migrate users
    # migrate_users_from_json()


def migrate_source_groups_from_json(storage_path: Path = Path("core/storage")):
    '''
    migrate source groups from scheme.json to postgresql
    '''
    scheme_file = storage_path / "scheme.json"
    if not scheme_file.exists():
        logger.warning(f"scheme.json not found at {scheme_file}")
        return

    with open(scheme_file, "r") as f:
        scheme_data = json.load(f)

    with get_db_context() as db:
        from core.db.models import SourceGroup
        source_groups = scheme_data.get("source_groups", [])
        for group in source_groups:
            try:
                name = group.get("source_group_name")
                if not name:
                    continue

                # check existing
                existing = db.query(SourceGroup).filter(
                    SourceGroup.slug == name
                ).first()
                if existing:
                    logger.info(f"source group {name} already exists, skipping")
                    continue
                
                # create
                sg = SourceGroup(
                    slug=name,
                    description=f"Imported from scheme.json (mode={group.get('mode')})",
                    config=group.get("data", [])
                )
                db.add(sg)
                db.commit()
                logger.info(f"migrated source group: {name}")
            except Exception as e:
                logger.error(f"error migrating source group {group.get('source_group_name')}: {e}")
    
    logger.info("migration completed")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_migration()

