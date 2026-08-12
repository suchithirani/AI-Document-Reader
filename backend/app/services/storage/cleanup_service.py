import logging
import time
from pathlib import Path

logger = logging.getLogger(__name__)


class StorageCleanupService:

    def cleanup_directory(
        self,
        directory: str,
        retention_hours: int,
    ) -> int:

        path = Path(directory)

        if not path.exists():
            return 0

        deleted = 0

        cutoff = (
            time.time()
            - retention_hours * 3600
        )

        for file in path.rglob("*"):

            if not file.is_file():
                continue

            if file.stat().st_mtime < cutoff:

                file.unlink(
                    missing_ok=True,
                )

                deleted += 1

        logger.info(
            "Deleted %d temporary files.",
            deleted,
        )

        return deleted