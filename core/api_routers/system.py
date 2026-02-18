'''
Copyright 2019-Present The OpenUBA Platform Authors
System API endpoints
'''

import logging
from fastapi import APIRouter, Depends
from typing import Dict, Any, List, Optional

from core.auth import get_current_user
from core.services.system_logs import SystemLogService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/system", tags=["system"])

@router.get("/logs")
async def get_system_logs(
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    '''
    Get recent system logs from infrastructure components
    '''
    try:
        service = SystemLogService()
        return service.get_logs(limit)
    except Exception as e:
        logger.error(f"Failed to fetch system logs: {e}")
        return []
