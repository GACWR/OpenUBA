
import os
import sys
import logging
from pathlib import Path
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.db.init_schema import parse_database_url
from core.db import init_db, DATABASE_URL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reset_db():
    database_url = os.getenv("DATABASE_URL", DATABASE_URL)
    logger.info(f"Resetting database at {database_url}...")
    
    db_config = parse_database_url(database_url)
    target_db = db_config["database"]
    postgres_url = f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{target_db}"

    try:
        conn = psycopg2.connect(postgres_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        logger.info("Dropping public schema...")
        cursor.execute("DROP SCHEMA public CASCADE;")
        cursor.execute("CREATE SCHEMA public;")
        cursor.execute("GRANT ALL ON SCHEMA public TO public;") # Ensure permissions
        
        cursor.close()
        # Do NOT close conn here, reuse it
        logger.info("Schema dropped.")
        
        logger.info("Re-initializing schema...")
        import core.db.models
        init_db()
        
        # FORCE ADD COLUMN if it missed it (fail-safe)
        logger.info("Force-checking runtime column...")
        cursor = conn.cursor()
        try:
             cursor.execute("ALTER TABLE models ADD COLUMN IF NOT EXISTS runtime VARCHAR(50) DEFAULT 'python-base' NOT NULL;")
             logger.info("Column runtime added/verified.")
        except Exception as e:
             logger.warning(f"Could not alter table: {e}")
             
        cursor.close()
        conn.close()
        
        logger.info("Schema re-initialized successfully.")
        
    except Exception as e:
        logger.error(f"Failed to reset DB: {e}")
        sys.exit(1)

if __name__ == "__main__":
    reset_db()
