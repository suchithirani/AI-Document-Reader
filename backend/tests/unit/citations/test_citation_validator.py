from app.services.citation_validator.service import CitationValidator


def test_citation_validator_preserves_valid_citations():
    validator = CitationValidator()
    sources = [{"id": 1}, {"id": 2}, {"id": 3}]

    text = "Machine learning is supervised [1] and unsupervised [2]."
    result = validator.validate(text, sources)
    assert result == "Machine learning is supervised [1] and unsupervised [2]."


def test_citation_validator_removes_invalid_citations():
    validator = CitationValidator()
    sources = [{"id": 1}]

    text = "Valid claim [1] and unsupported claim [99]."
    result = validator.validate(text, sources)
    assert result == "Valid claim [1] and unsupported claim ."


def test_citation_validator_normalizes_asian_brackets():
    validator = CitationValidator()
    sources = [{"id": 1}, {"id": 4}]

    text = "AI roadmap details 【1】 and project results 【4】."
    result = validator.validate(text, sources)
    assert result == "AI roadmap details [1] and project results [4]."


def test_citation_validator_normalizes_complex_line_reference_citations():
    validator = CitationValidator()
    sources = [{"id": 1}, {"id": 6}]

    text = "Explicit timestamp appears on every page【1†L1-L3】【6†L1-L3】."
    result = validator.validate(text, sources)
    assert result == "Explicit timestamp appears on every page[1][6]."


def test_citation_validator_empty_text():
    validator = CitationValidator()
    assert validator.validate("", [{"id": 1}]) == ""
