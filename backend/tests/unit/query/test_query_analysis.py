from app.common.constants import QueryIntent, QueryScope
from app.services.query_analysis.analyzer import QueryAnalyzer


def test_query_analyzer_page_extraction():
    analyzer = QueryAnalyzer()

    analysis = analyzer.analyze("What is on page 5 and page 6?")
    assert 5 in analysis.page_numbers
    assert 6 in analysis.page_numbers
    assert analysis.scope == QueryScope.PAGE


def test_query_analyzer_comparison_intent():
    analyzer = QueryAnalyzer()

    analysis = analyzer.analyze("Compare document A and document B")
    assert analysis.intent == QueryIntent.COMPARISON


def test_query_analyzer_toc_intent():
    analyzer = QueryAnalyzer()

    analysis = analyzer.analyze("Show me the table of contents of this document")
    assert analysis.intent == QueryIntent.TOC


def test_query_analyzer_visual_context():
    analyzer = QueryAnalyzer()

    analysis = analyzer.analyze("Describe the architecture diagram and workflow chart on page 3")
    assert analysis.requires_visual is True


def test_query_analyzer_broad_query():
    analyzer = QueryAnalyzer()

    analysis = analyzer.analyze("Give me a full overview and summary of the document")
    assert analysis.is_broad is True
