from unittest.mock import patch

from app.workers.ai_tasks import (
    extract_document_metadata_task,
    generate_proactive_insights_task,
    update_user_memory_task,
)


def test_ai_task_celery_entrypoints():
    # 1. Proactive insights task
    with patch("app.workers.ai_tasks.run_async_task") as mock_run:
        generate_proactive_insights_task(owner_id="u1", document_ids=["d1"])
        assert mock_run.called

    # 2. Update user memory task
    with patch("app.workers.ai_tasks.run_async_task") as mock_run:
        update_user_memory_task(owner_id="u1", session_id="s1")
        assert mock_run.called

    # 3. Extract document metadata task
    with patch("app.workers.ai_tasks.run_async_task") as mock_run:
        extract_document_metadata_task(owner_id="u1", document_id="d1")
        assert mock_run.called
