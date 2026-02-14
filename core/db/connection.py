'''
Copyright 2019-Present The OpenUBA Platform Authors
database connection and session management
'''

import os
import logging
from typing import Generator, List
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager

# database url from environment or default
# default to local postgres with user's credentials
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://gacwr:test1234@localhost:5432/openuba"
)

# create engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # verify connections before using
    pool_size=10,
    max_overflow=20
)

# session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# base class for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    '''
    dependency for fastapi to get database session
    yields a database session and closes it after use
    '''
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    '''
    context manager for database sessions
    use this outside of fastapi dependency injection
    '''
    db = SessionLocal()
    logging.debug("created new database session")
    try:
        yield db
        db.commit()
        logging.debug("database transaction committed")
    except Exception as e:
        db.rollback()
        logging.error(f"database session error: {e}")
        logging.debug("database transaction rolled back")
        raise
    finally:
        db.close()
        logging.debug("database session closed")


def parse_sql_statements(sql_content: str) -> List[str]:
    '''
    parse sql content into individual statements
    handles multi-line statements, dollar-quoted strings, and comments
    returns list of sql statements
    '''
    statements = []
    current_statement = []
    in_dollar_quote = False
    dollar_quote_tag = None
    in_single_quote = False
    in_double_quote = False
    in_block_comment = False
    i = 0
    
    while i < len(sql_content):
        char = sql_content[i]
        next_char = sql_content[i + 1] if i + 1 < len(sql_content) else ''
        
        # handle block comments /* ... */
        if not in_single_quote and not in_double_quote and not in_dollar_quote:
            if char == '/' and next_char == '*':
                in_block_comment = True
                i += 2
                continue
            elif in_block_comment and char == '*' and next_char == '/':
                in_block_comment = False
                i += 2
                continue
            elif in_block_comment:
                i += 1
                continue
        
        if in_block_comment:
            i += 1
            continue
        
        # handle line comments -- (but not inside quotes)
        if not in_single_quote and not in_double_quote and not in_dollar_quote:
            if char == '-' and next_char == '-':
                # skip rest of line
                while i < len(sql_content) and sql_content[i] != '\n':
                    i += 1
                continue
        
        # handle dollar-quoted strings $$ ... $$ or $tag$ ... $tag$
        if not in_single_quote and not in_double_quote:
            if char == '$':
                # find the dollar quote tag (everything between $ and next $)
                tag_start = i
                tag_end = i + 1
                while tag_end < len(sql_content) and sql_content[tag_end] != '$':
                    tag_end += 1
                if tag_end < len(sql_content):
                    potential_tag = sql_content[tag_start:tag_end + 1]
                    if not in_dollar_quote:
                        # opening dollar quote
                        in_dollar_quote = True
                        dollar_quote_tag = potential_tag
                        current_statement.append(potential_tag)
                        i = tag_end + 1
                        continue
                    else:
                        # check if this is the closing tag
                        if potential_tag == dollar_quote_tag:
                            # closing dollar quote
                            in_dollar_quote = False
                            current_statement.append(potential_tag)
                            dollar_quote_tag = None
                            i = tag_end + 1
                            continue
                        # else, it's a different dollar quote inside, just add the $ char
        
        # handle single quotes (but not inside dollar quotes)
        if not in_dollar_quote:
            if char == "'" and not in_double_quote:
                in_single_quote = not in_single_quote
            elif char == '"' and not in_single_quote:
                in_double_quote = not in_double_quote
        
        # handle semicolon (statement terminator)
        if char == ';' and not in_single_quote and not in_double_quote and not in_dollar_quote:
            # end of statement
            statement = ''.join(current_statement).strip()
            if statement:
                statements.append(statement)
            current_statement = []
            i += 1
            continue
        
        # add character to current statement
        current_statement.append(char)
        i += 1
    
    # add final statement if exists
    if current_statement:
        statement = ''.join(current_statement).strip()
        if statement:
            statements.append(statement)
    
    return statements


def init_schema_from_sql() -> None:
    '''
    initialize database schema from schema.sql file
    this creates extensions, tables, indexes, and triggers
    executes each statement individually to avoid transaction cascading failures
    '''
    from pathlib import Path
    schema_file = Path(__file__).parent / "schema.sql"
    if not schema_file.exists():
        logging.warning(f"schema.sql not found at {schema_file}, skipping SQL schema initialization")
        return
    
    try:
        with open(schema_file, "r") as f:
            schema_sql = f.read()
        
        # parse sql into individual statements
        statements = parse_sql_statements(schema_sql)
        
        # execute each statement individually in its own transaction
        for statement in statements:
            if not statement.strip():
                continue
            
            try:
                # execute each statement in its own transaction
                with engine.begin() as conn:
                    conn.execute(text(statement))
            except Exception as e:
                # ignore errors for existing objects
                error_str = str(e).lower()
                if any(phrase in error_str for phrase in [
                    "already exists", "duplicate", "already defined",
                    "infailedsqltransaction"  # transaction already aborted, skip
                ]):
                    logging.debug(f"schema object already exists or transaction aborted, skipping: {statement[:50]}...")
                else:
                    # check if it's a syntax error that might be due to parsing
                    if "syntax error" in error_str or "unterminated" in error_str:
                        logging.warning(f"schema statement syntax error (may be parsing issue): {e}")
                        logging.debug(f"failed statement: {statement[:200]}...")
                    else:
                        logging.warning(f"schema statement failed: {e}")
                        logging.debug(f"failed statement: {statement[:200]}...")
        
        logging.info("database schema initialized from schema.sql")
    except Exception as e:
        logging.error(f"failed to initialize schema from SQL: {e}")
        raise


def init_db() -> None:
    '''
    initialize database by creating all tables
    call this after importing all models
    includes connection test before creating tables
    executes schema.sql first for complete schema setup, then SQLAlchemy models
    also creates triggers for real-time updates
    '''
    try:
        # test connection first
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logging.info("database connection verified")
    except Exception as e:
        logging.error(f"database connection failed: {e}")
        raise
    
    try:
        # first, execute schema.sql for complete schema (extensions, tables, indexes, triggers)
        init_schema_from_sql()
        
        # then, ensure SQLAlchemy models are synced (handles any missing columns)
        Base.metadata.create_all(bind=engine)
        logging.info("database tables created/verified")
        
        # create triggers for real-time updates (if not already in schema.sql)
        try:
            from pathlib import Path
            triggers_file = Path(__file__).parent / "triggers.sql"
            if triggers_file.exists():
                with open(triggers_file, "r") as f:
                    triggers_sql = f.read()
                
                # parse triggers sql into individual statements using same parser
                trigger_statements = parse_sql_statements(triggers_sql)
                
                # execute each trigger statement individually in its own transaction
                for statement in trigger_statements:
                    if not statement.strip():
                        continue
                    
                    try:
                        # execute each statement in its own transaction
                        with engine.begin() as conn:
                            conn.execute(text(statement))
                    except Exception as e:
                        # ignore errors for existing objects
                        error_str = str(e).lower()
                        if any(phrase in error_str for phrase in [
                            "already exists", "duplicate", "already defined",
                            "infailedsqltransaction"
                        ]):
                            logging.debug(f"trigger already exists or transaction aborted, skipping: {statement[:50]}...")
                        else:
                            # check if it's a syntax error that might be due to parsing
                            if "syntax error" in error_str or "unterminated" in error_str:
                                logging.warning(f"trigger statement syntax error (may be parsing issue): {e}")
                                logging.debug(f"failed statement: {statement[:200]}...")
                            else:
                                logging.warning(f"trigger statement failed: {e}")
                                logging.debug(f"failed statement: {statement[:200]}...")
                logging.info("database triggers created")
        except Exception as e:
            logging.warning(f"failed to create triggers (may already exist): {e}")
    except Exception as e:
        logging.error(f"failed to create database tables: {e}")
        raise


def drop_db() -> None:
    '''
    drop all database tables
    use with caution
    '''
    Base.metadata.drop_all(bind=engine)
    logging.warning("database tables dropped")

