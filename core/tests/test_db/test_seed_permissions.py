'''
Copyright 2019-Present The OpenUBA Platform Authors
seed idempotency / upgrade-backfill tests

regression guard for the audit finding: an all-or-nothing `count() == 0` seed
gate left already-seeded (upgraded) deployments WITHOUT rows for newly-added
pages (e.g. source_groups) → non-admin roles 403. seeding must be idempotent
per (role, page) and backfill missing pages.
'''

import uuid

from core.db.seed import _seed_permissions, DEFAULT_PERMISSIONS
from core.db.models import RolePermission


def test_seed_permissions_backfills_new_page_without_duplicating(db_session):
    # simulate an OLD deployment: every default row seeded EXCEPT source_groups
    for perm in DEFAULT_PERMISSIONS:
        if perm["page"] != "source_groups":
            db_session.add(RolePermission(id=uuid.uuid4(), **perm))
    db_session.flush()
    assert db_session.query(RolePermission).filter_by(page="source_groups").count() == 0

    # run seeding (as on upgrade) — must backfill the missing page only
    _seed_permissions(db_session)

    sg = db_session.query(RolePermission).filter_by(page="source_groups").count()
    assert sg == 3  # admin, analyst, triage
    # nothing duplicated: total == the full default set, exactly once each
    assert db_session.query(RolePermission).count() == len(DEFAULT_PERMISSIONS)


def test_seed_permissions_is_idempotent(db_session):
    _seed_permissions(db_session)
    total1 = db_session.query(RolePermission).count()
    assert total1 == len(DEFAULT_PERMISSIONS)

    # running again must not add or duplicate anything
    _seed_permissions(db_session)
    total2 = db_session.query(RolePermission).count()
    assert total2 == total1
