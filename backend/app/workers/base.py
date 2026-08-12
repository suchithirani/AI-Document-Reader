import asyncio
import logging
from app.workers.database import get_worker_database

logger = logging.getLogger(__name__)
_worker_loop: asyncio.AbstractEventLoop | None = None

def run_async_task(coro):
    
    global _worker_loop

    if _worker_loop is None:
        _worker_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_worker_loop)

    try:
        return _worker_loop.run_until_complete(coro)

    except Exception:
        logger.exception(
            "Worker task failed.",
        )
        raise


async def with_database(callback):

    _, db = await get_worker_database()

    return await callback(db)

def get_worker_loop():

    return _worker_loop