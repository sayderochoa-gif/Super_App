"""
Router for Seismic Agent API endpoints.
Provides conversational AI analysis, SQL queries, and USGS synchronization.
Accessible to both Viewer and Admin roles.
"""

from datetime import datetime, timezone
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.models.user import User
from app.security import get_current_user
from agentebot.agent.core import SeismicAgent
from agentebot.agent.tools import (
    get_database_schema,
    get_seismic_statistics,
    get_tsunami_alerts,
    sync_realtime_earthquakes,
)

logger = logging.getLogger("sismowatch.agent")

router = APIRouter(prefix="/api/agent", tags=["Seismic Agent"])

# Singleton agent instance for server session
_agent = SeismicAgent()


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User prompt or question")
    reset: Optional[bool] = Field(False, description="Reset conversational history")


class ChatResponse(BaseModel):
    response: str
    user_role: str
    timestamp: str


@router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Process conversational query or analysis request with the Seismic Relational Agent.
    Available to both 'viewer' and 'admin' roles.
    """
    try:
        from agentebot.agent.core import SeismicAgent
        agent = SeismicAgent()
        if payload.reset:
            agent.reset_chat()

        answer = agent.chat(payload.message, user_role=current_user.role)
        return ChatResponse(
            response=answer,
            user_role=current_user.role,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    except Exception as exc:
        logger.error(f"Error in agent chat endpoint: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent analysis failed: {str(exc)}",
        )


@router.post("/sync")
async def trigger_agent_sync(
    current_user: User = Depends(get_current_user),
):
    """Trigger real-time synchronization from USGS GeoJSON feed."""
    try:
        result = sync_realtime_earthquakes()
        return {
            "status": "success",
            "triggered_by": current_user.username,
            "role": current_user.role,
            "data": result,
        }
    except Exception as exc:
        logger.error(f"Error triggering agent sync: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {str(exc)}",
        )


@router.get("/stats")
async def get_agent_stats(
    current_user: User = Depends(get_current_user),
):
    """Retrieve aggregate seismic statistics."""
    return get_seismic_statistics()


@router.get("/tsunami")
async def get_agent_tsunami(
    current_user: User = Depends(get_current_user),
):
    """Retrieve tsunami alerts catalog."""
    return get_tsunami_alerts()


@router.get("/schema")
async def get_agent_schema(
    current_user: User = Depends(get_current_user),
):
    """Retrieve relational database schema."""
    return {"schema": get_database_schema()}
