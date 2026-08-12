from celery.schedules import crontab

BEAT_SCHEDULE = {

    "cleanup-expired-refresh-tokens": {
        "task": "cleanup.refresh_tokens",
        "schedule": crontab(
            minute=0,
        ),
    },

    "cleanup-temp-files": {
        "task": "cleanup.temp_files",
        "schedule": crontab(
            hour=2,
            minute=0,
        ),
    },

    "cleanup-audit-logs": {
        "task": "cleanup.audit_logs",
        "schedule": crontab(
            hour=3,
            minute=0,
        ),
    },
}