'''
Copyright 2019-Present The OpenUBA Platform Authors
pytest configuration and fixtures
uses testcontainers for real services (no mocks)
'''

import os
import pytest
import asyncio
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from testcontainers.postgres import PostgresContainer
from fastapi.testclient import TestClient
from docker import DockerClient

from core.db.connection import get_db
from core.db.models import Base
from core.fastapi_app import app


@pytest.fixture(scope="session")
def postgres_container() -> Generator[PostgresContainer, None, None]:
    '''
    create a real postgresql container for testing
    '''
    with PostgresContainer("postgres:15-alpine") as postgres:
        yield postgres


@pytest.fixture(scope="session")
def db_engine(postgres_container: PostgresContainer):
    '''
    create database engine from testcontainer
    '''
    database_url = postgres_container.get_connection_url()
    engine = create_engine(database_url)
    # create all tables
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(db_engine) -> Generator[Session, None, None]:
    '''
    create a database session for each test
    '''
    connection = db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def test_client(db_session: Session) -> TestClient:
    '''
    create a test client with database dependency override
    '''
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def docker_client() -> DockerClient:
    '''
    create docker client for container testing
    '''
    return DockerClient()


@pytest.fixture(scope="session")
def event_loop():
    '''
    create event loop for async tests
    '''
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

