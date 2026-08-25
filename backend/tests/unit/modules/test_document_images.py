
import pytest

from app.modules.document_images.service import DocumentImageService


@pytest.mark.asyncio
async def test_document_image_service(mock_db):
    service = DocumentImageService(mock_db)

    mock_images = [
        {
            "document_id": "doc_123",
            "page_number": 1,
            "image_index": 0,
            "storage_path": "uploads/img1.png",
            "width": 800,
            "height": 600,
        },
        {
            "document_id": "doc_123",
            "page_number": 2,
            "image_index": 0,
            "storage_path": "uploads/img2.png",
            "width": 1024,
            "height": 768,
        }
    ]

    # 1. Save images
    saved = await service.save_images(mock_images)
    assert len(saved) == 2

    # 2. Get images for document pages
    page_imgs = await service.get_images_for_document_pages(
        document_id="doc_123",
        page_numbers=[1],
    )
    assert len(page_imgs) >= 1

    # 3. Get images for documents
    doc_imgs = await service.get_images_for_documents(["doc_123"])
    assert len(doc_imgs) >= 1

    # 4. Delete images
    await service.delete_document_images("doc_123")
