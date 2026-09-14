import asyncio

from fastapi import APIRouter
from starlette.responses import StreamingResponse

from app.store import store

router = APIRouter(tags=["Realtime"])


@router.get("/stream")
async def event_stream():
    """Server-Sent Events endpoint streaming live match and standings updates."""
    queue = store.subscribe()

    async def event_generator():
        try:
            yield ": connected\n\n"
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield f"data: {event.model_dump_json()}\n\n"
                except TimeoutError:
                    yield ": ping\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            store.unsubscribe(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
