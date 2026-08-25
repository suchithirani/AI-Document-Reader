from app.services.chunking.service import ChunkingService


def test_chunking_service_basic_split():
    service = ChunkingService()

    text = (
        "Artificial Intelligence is a wide field of computer science. "
        "Machine Learning is a subset of AI that focuses on learning from data. "
        "Deep Learning uses multilayered artificial neural networks. "
        "Natural Language Processing enables computers to understand human languages."
    )

    chunks = service.split_text(text, chunk_size=100, overlap_sentences=1)
    assert len(chunks) >= 1
    assert all(isinstance(c, str) for c in chunks)


def test_chunking_service_empty_text():
    service = ChunkingService()
    assert service.split_text("") == []
    assert service.split_text("   \n\n\t  ") == []


def test_chunking_service_clean_text():
    service = ChunkingService()
    raw = "Line 1\r\nLine 2   with   extra   spaces\n\n\n\nLine 3"
    cleaned = service._clean_text(raw)
    assert "\r" not in cleaned
    assert "   " not in cleaned
    assert "\n\n\n" not in cleaned
