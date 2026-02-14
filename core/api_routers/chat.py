'''
Copyright 2019-Present The OpenUBA Platform Authors
chat api router — streams LLM responses via SSE
'''

import json
import logging
from typing import List, Optional, Dict

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

router = APIRouter()
logger = logging.getLogger(__name__)


class Message(BaseModel):
    role: str
    content: str


class PageContext(BaseModel):
    route: str = ""
    params: Optional[Dict[str, str]] = None


class ChatRequest(BaseModel):
    messages: List[Message]
    context: Optional[PageContext] = None
    provider: Optional[str] = None
    model: Optional[str] = None


@router.post("/chat")
async def chat(request: ChatRequest):
    '''
    stream LLM assistant responses via server-sent events.
    each SSE data line contains {"token": "..."}.
    final line is [DONE].
    '''
    from core.services.chat_service import ChatService

    service = ChatService()
    messages = [{"role": m.role, "content": m.content} for m in request.messages]
    context = None
    if request.context:
        context = {"route": request.context.route, "params": request.context.params}

    async def event_stream():
        try:
            async for token in service.process_message_stream(
                messages, context,
                provider=request.provider,
                model=request.model,
            ):
                yield f"data: {json.dumps({'token': token})}\n\n"
        except Exception as e:
            logger.error(f"chat stream error: {e}")
            yield f"data: {json.dumps({'token': f'Error: {str(e)}'})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
