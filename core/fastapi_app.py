'''
Copyright 2019-Present The OpenUBA Platform Authors
fastapi application entry point
'''

import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from sqlalchemy import text

from core.db import init_db, SessionLocal, User, RolePermission, Notification
from core.api_routers import models, anomalies, cases, rules, feedback, display, data, chat, notifications
from core.graphql import PostGraphileServer
from core.services.model_scheduler import ModelScheduler
from core.services.model_installer import ModelInstaller
from core.auth import get_password_hash
import coloredlogs

# configure logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# install coloredlogs
coloredlogs.install(
    level=log_level,
    fmt=log_format,
    field_styles={
        'asctime': {'color': 'green'},
        'hostname': {'color': 'magenta'},
        'levelname': {'bold': True, 'color': 'black'},
        'name': {'color': 'blue'},
        'programname': {'color': 'cyan'}
    },
    level_styles={
        'debug': {'color': 'cyan'},
        'info': {'color': 'green'},
        'warning': {'color': 'yellow'},
        'error': {'color': 'red'},
        'critical': {'bold': True, 'color': 'red'}
    }
)

logger = logging.getLogger(__name__)


DEFAULT_PERMISSIONS = {
    "manager": {
        "home": (True, False), "data": (True, False), "models": (True, False),
        "rules": (True, False), "alerts": (True, False), "entities": (True, False),
        "anomalies": (True, False), "cases": (True, False), "schedules": (True, False),
        "settings": (True, False), "users": (True, False),
    },
    "triage": {
        "home": (True, False), "data": (False, False), "models": (False, False),
        "rules": (True, False), "alerts": (True, False), "entities": (True, False),
        "anomalies": (False, False), "cases": (True, False), "schedules": (False, False),
        "settings": (False, False), "users": (False, False),
    },
    "analyst": {
        "home": (True, False), "data": (True, False), "models": (True, True),
        "rules": (True, True), "alerts": (True, False), "entities": (True, True),
        "anomalies": (True, True), "cases": (True, False), "schedules": (False, False),
        "settings": (False, False), "users": (False, False),
    },
}


def seed_defaults():
    '''seed default admin user and role permissions if they don't exist'''
    db = SessionLocal()
    try:
        # seed default admin user
        admin = db.query(User).filter(User.username == "openuba").first()
        if not admin:
            admin = User(
                username="openuba",
                email="admin@openuba.org",
                password_hash=get_password_hash("password"),
                role="admin",
                display_name="OpenUBA Admin",
                is_active=True,
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)
            logger.info("seeded default admin user: openuba")

            # create welcome notification
            db.add(Notification(
                user_id=admin.id,
                title="Welcome to OpenUBA",
                message="Your account has been created. Get started by exploring the dashboard.",
                type="info",
            ))
            db.commit()

        # seed default role permissions
        existing_count = db.query(RolePermission).count()
        if existing_count == 0:
            for role, pages in DEFAULT_PERMISSIONS.items():
                for page, (can_read, can_write) in pages.items():
                    db.add(RolePermission(
                        role=role,
                        page=page,
                        can_read=can_read,
                        can_write=can_write,
                    ))
            db.commit()
            logger.info("seeded default role permissions")
    except Exception as e:
        db.rollback()
        logger.warning(f"failed to seed defaults: {e}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    '''
    lifespan events for fastapi app
    initialize database on startup
    '''
    logger.info("initializing openuba backend")
    # initialize database tables with retry logic
    max_retries = 10
    retry_delay = 5
    for attempt in range(max_retries):
        try:
            init_db()
            logger.info("database initialized")

            # seed default user and role permissions
            seed_defaults()

            # Discover local models on startup
            try:
                logger.info("discovering local models...")
                ModelInstaller().discover_local_models()
                logger.info("local models discovery complete")
            except Exception as e:
                logger.warning(f"local model discovery failed: {e}")
            break
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"database initialization failed (attempt {attempt + 1}/{max_retries}): {e}, retrying in {retry_delay}s...")
                import time
                time.sleep(retry_delay)
            else:
                logger.error(f"database initialization failed after {max_retries} attempts: {e}")
    
    # Trigger local data ingestion (only in local mode)
    if os.getenv("EXECUTION_MODE", "docker") != "kubernetes":
        try:
            logger.info("triggering local data ingestion...")
            import subprocess
            import sys
            
            script_path = os.path.join("scripts", "init_data_ingestion.py")
            if os.path.exists(script_path):
                # Run in background
                subprocess.Popen([sys.executable, script_path])
                logger.info("local data ingestion started in background")
            else:
                logger.warning(f"ingestion script not found: {script_path}")
        except Exception as e:
            logger.warning(f"failed to trigger local ingestion: {e}")
    
    # start postgraphile for graphql api (only in local/dev mode)
    # in kubernetes, postgraphile runs as a separate container
    postgraphile = None
    execution_mode = os.getenv("EXECUTION_MODE", "docker")
    
    if execution_mode != "kubernetes":
        # use same database url as connection module
        from core.db import DATABASE_URL
        database_url = os.getenv("DATABASE_URL", DATABASE_URL)
        if os.getenv("ENABLE_GRAPHQL", "true").lower() == "true":
            try:
                postgraphile = PostGraphileServer(
                    database_url=database_url,
                    host=os.getenv("POSTGRAPHILE_HOST", "0.0.0.0"),
                    port=int(os.getenv("POSTGRAPHILE_PORT", "5000"))
                )
                postgraphile.start()
                logger.info("postgraphile graphql api started (local mode)")
            except Exception as e:
                logger.warning(f"postgraphile not available: {e}")
    else:
        graphql_url = os.getenv("GRAPHQL_URL", "http://postgraphile:5000/graphql")
        logger.info(f"using external postgraphile service at {graphql_url}")
    
    # start model scheduler
    scheduler = None
    try:
        scheduler = ModelScheduler()
        logger.info("model scheduler started")
    except Exception as e:
        logger.warning(f"model scheduler not available: {e}")
    
    yield
    
    # shutdown scheduler
    if scheduler:
        try:
            scheduler.shutdown()
            logger.info("model scheduler shut down")
        except Exception as e:
            logger.warning(f"error shutting down scheduler: {e}")
    
    # shutdown postgraphile (only if we started it)
    if postgraphile:
        postgraphile.stop()
    logger.info("shutting down openuba backend")


# create fastapi app
app = FastAPI(
    title="OpenUBA API",
    description="OpenUBA v0.0.2 API - User and Entity Behavior Analytics",
    version="0.0.2",
    lifespan=lifespan
)

# configure cors
cors_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:3001,http://localhost:8080"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# include routers
from core.api_routers import auth, schedules
app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
app.include_router(models.router, prefix="/api/v1", tags=["models"])
app.include_router(anomalies.router, prefix="/api/v1", tags=["anomalies"])
app.include_router(cases.router, prefix="/api/v1", tags=["cases"])
app.include_router(rules.router, prefix="/api/v1", tags=["rules"])
app.include_router(feedback.router, prefix="/api/v1", tags=["feedback"])
app.include_router(display.router, prefix="/api/v1", tags=["display"])

app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
app.include_router(notifications.router, prefix="/api/v1", tags=["notifications"])
from core.api_routers import settings
app.include_router(settings.router, prefix="/api/v1", tags=["settings"])
app.include_router(schedules.router, prefix="/api/v1", tags=["schedules"])
from core.api_routers import source_groups
app.include_router(source_groups.router, prefix="/api/v1", tags=["source_groups"])
app.include_router(data.router, tags=["data"])
from core.api_routers import system
app.include_router(system.router, tags=["system"])


@app.get("/")
async def root():
    '''
    root endpoint
    '''
    from core.graphql import get_graphql_url, get_graphiql_url
    response = {
        "name": "OpenUBA API",
        "version": "0.0.2",
        "status": "running",
        "endpoints": {
            "rest": "/api/v1",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }
    # add graphql endpoint if available
    try:
        response["endpoints"]["graphql"] = get_graphql_url()
        response["endpoints"]["graphiql"] = get_graphiql_url()
    except Exception:
        pass
    return response


@app.get("/health")
async def health():
    '''
    health check endpoint
    checks database connectivity
    '''
    try:
        # check database connection
        from core.db import SessionLocal
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
            db_status = "connected"
        except Exception as e:
            db_status = f"error: {str(e)}"
        finally:
            db.close()
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    if db_status == "connected":
        return {"status": "healthy", "database": "connected"}
    else:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "database": db_status}
        )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    '''
    global exception handler
    '''
    logger.error(f"unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "core.fastapi_app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

