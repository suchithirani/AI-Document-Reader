from app.services.embedding.factory import EmbeddingFactory
from app.services.ocr_cleaner.service import clean_ocr_text
from app.services.storage.local_storage import LocalStorage


def test_storage_service():
    storage = LocalStorage()
    assert storage.upload_directory is not None


def test_embedding_factory():
    gemini_embedder = EmbeddingFactory.get_engine("gemini")
    assert gemini_embedder is not None

    ollama_embedder = EmbeddingFactory.get_engine("ollama")
    assert ollama_embedder is not None


def test_ocr_cleaner():
    raw_ocr = "Bill Amount: Nine Thousand Two Hundred Twenty Two Only"
    cleaned = clean_ocr_text(raw_ocr)
    assert "9,222" in cleaned
