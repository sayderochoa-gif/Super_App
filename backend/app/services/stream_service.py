"""
Server-Sent Events (SSE) Streaming Service for Real-Time Earthquake Updates.
"""

import asyncio
import json
from datetime import datetime, timezone, timedelta
from typing import AsyncGenerator
from sqlalchemy import select, desc
from app.database import AsyncSessionLocal
from app.models.earthquake import CuratedEarthquake


async def event_generator() -> AsyncGenerator[str, None]:
    """
    Asynchronous generator streaming real-time earthquake updates and heartbeats
    using Server-Sent Events (SSE) format.
    """
    last_seen_time = datetime.now(timezone.utc) - timedelta(minutes=60)
    seen_ids = set()

    # Initial handshake
    yield f"event: connect\ndata: {json.dumps({'message': 'Connected to SismoWatch Live SSE Stream', 'timestamp': datetime.now(timezone.utc).isoformat()})}\n\n"

    while True:
        try:
            async with AsyncSessionLocal() as session:
                # Query for any new curated events
                stmt = (
                    select(CuratedEarthquake)
                    .where(CuratedEarthquake.time >= last_seen_time)
                    .order_by(desc(CuratedEarthquake.time))
                    .limit(10)
                )
                res = await session.execute(stmt)
                events = list(res.scalars().all())

                for ev in reversed(events):
                    if ev.id not in seen_ids:
                        seen_ids.add(ev.id)
                        payload = {
                            "id": ev.id,
                            "mag": ev.mag,
                            "place": ev.place,
                            "time": ev.time.isoformat() if ev.time else None,
                            "latitude": ev.latitude,
                            "longitude": ev.longitude,
                            "depth_km": ev.depth_km,
                            "tsunami": ev.tsunami,
                            "alert": ev.alert,
                            "url": ev.url
                        }
                        yield f"event: new_earthquake\ndata: {json.dumps(payload)}\n\n"

                # Send heartbeat
                heartbeat = {
                    "event": "heartbeat",
                    "time": datetime.now(timezone.utc).isoformat(),
                    "status": "online"
                }
                yield f"event: ping\ndata: {json.dumps(heartbeat)}\n\n"

        except Exception as exc:
            yield f"event: error\ndata: {json.dumps({'error': str(exc)})}\n\n"

        await asyncio.sleep(5)
