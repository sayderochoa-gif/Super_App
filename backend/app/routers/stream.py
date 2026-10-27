"""
Server-Sent Events (SSE) Real-Time Stream Endpoint.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status, Header
from fastapi.responses import StreamingResponse
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.services.stream_service import event_generator

router = APIRouter(prefix="/api/stream", tags=["Real-Time Streaming"])


async def authenticate_sse_connection(
    token: Optional[str] = Query(None, description="JWT token via query param for EventSource"),
    authorization: Optional[str] = Header(None, description="Bearer token header"),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Authenticates SSE stream connection via either Authorization header or query parameter.
    Ensures 401 Unauthorized if token is missing or invalid.
    """
    jwt_token = None
    if authorization and authorization.startswith("Bearer "):
        jwt_token = authorization.split(" ")[1]
    elif token:
        jwt_token = token

    if not jwt_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required to connect to live stream"
        )

    try:
        payload = jwt.decode(jwt_token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    stmt = select(User).where(User.username == username)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    return user


@router.get("")
async def stream_live_events(
    user: User = Depends(authenticate_sse_connection)
):
    """
    Server-Sent Events (SSE) endpoint emitting newly ingested/curated earthquakes
    in real time, along with periodic heartbeats.
    """
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
            "X-Accel-Buffering": "no"
        }
    )
