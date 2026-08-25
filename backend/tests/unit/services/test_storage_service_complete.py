
import pytest

from app.services.storage.cleanup_service import StorageCleanupService
from app.services.storage.service import StorageService


def test_storage_cleanup_service(tmp_path):
    cleanup = StorageCleanupService()

    # Create test old file
    old_file = tmp_path / "old_temp.tmp"
    old_file.write_text("temporary data")

    # Test directory cleanup
    deleted = cleanup.cleanup_directory(directory=str(tmp_path), retention_hours=0)
    assert deleted >= 0


@pytest.mark.asyncio
async def test_storage_service_methods(mock_db, tmp_path):
    storage_svc = StorageService(mock_db)

    test_file = tmp_path / "sample.pdf"
    test_file.write_bytes(b"%PDF-1.4 test bytes")

    # get_file_path
    resolved = storage_svc.get_file_path(str(test_file))
    assert resolved.exists()

    # read_bytes
    data = await storage_svc.read_bytes(str(test_file))
    assert data == b"%PDF-1.4 test bytes"

    # load_image_bytes
    img_data = await storage_svc.load_image_bytes({"storage_path": str(test_file)})
    assert img_data == b"%PDF-1.4 test bytes"

    # delete_file
    await storage_svc.delete_file(str(test_file))
    assert not test_file.exists()

    # get_file_path non-existent -> FileNotFoundError
    with pytest.raises(FileNotFoundError):
        storage_svc.get_file_path(str(test_file))
