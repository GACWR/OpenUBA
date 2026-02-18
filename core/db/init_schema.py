'''
Copyright 2019-Present The OpenUBA Platform Authors
database schema initialization script
can be run standalone to initialize database schema
creates database if it doesn't exist
'''

import os
import sys
import logging
from pathlib import Path
from urllib.parse import urlparse
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.db.connection import init_db, DATABASE_URL

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def parse_database_url(database_url: str) -> dict:
    '''
    parse postgresql database url into components
    returns dict with: user, password, host, port, database
    '''
    parsed = urlparse(database_url)
    return {
        "user": parsed.username or "postgres",
        "password": parsed.password or "",
        "host": parsed.hostname or "localhost",
        "port": parsed.port or 5432,
        "database": parsed.path.lstrip("/") if parsed.path else "postgres"
    }


def ensure_database_exists(database_url: str) -> None:
    '''
    ensure target database exists, create it if it doesn't
    connects to default postgres database to create target database
    '''
    db_config = parse_database_url(database_url)
    target_db = db_config["database"]
    
    # connect to default postgres database to check/create target database
    postgres_url = f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/postgres"
    
    try:
        # connect to postgres database
        conn = psycopg2.connect(postgres_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # check if target database exists
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (target_db,)
        )
        exists = cursor.fetchone()
        
        if not exists:
            logger.info(f"database '{target_db}' does not exist, creating it...")
            # create database
            cursor.execute(f'CREATE DATABASE "{target_db}"')
            logger.info(f"database '{target_db}' created successfully")
        else:
            logger.info(f"database '{target_db}' already exists")
        
        cursor.close()
        conn.close()
    except psycopg2.Error as e:
        logger.error(f"failed to ensure database exists: {e}")
        raise
    except Exception as e:
        logger.error(f"unexpected error ensuring database exists: {e}")
        raise


def main():
    '''
    main function to initialize database schema
    creates database if it doesn't exist, then initializes schema
    '''
    database_url = os.getenv("DATABASE_URL", DATABASE_URL)
    logger.info(f"initializing database schema at {database_url}")
    
    try:
        # ensure database exists first
        ensure_database_exists(database_url)
        
        # now initialize schema
        init_db()
        logger.info("database schema initialization completed successfully")
        return 0
    except Exception as e:
        logger.error(f"database schema initialization failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

