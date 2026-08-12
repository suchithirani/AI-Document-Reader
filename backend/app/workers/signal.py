import asyncio

from celery.signals import worker_shutdown

from app.workers.database import (
    close_worker_database,
)
from app.workers.base import (
    get_worker_loop,
)


@worker_shutdown.connect
def shutdown_worker(**kwargs):

    loop = get_worker_loop()

    if loop is None:
        return

    if loop.is_closed():
        return

    try:

        loop.run_until_complete(
            close_worker_database()
        )

    finally:

        loop.close()