from app.services.prompt_builder.service import PromptBuilder


def test_prompt_builder_basic_structure():
    builder = PromptBuilder()
    prompt = builder.build(
        history=[],
        context="SOURCE_1: Python is a programming language.",
        question="What is Python?",
        intent="GLOBAL",
        detail_level="standard",
    )

    assert "You are an AI Document Assistant." in prompt
    assert "SOURCE_1: Python is a programming language." in prompt
    assert "What is Python?" in prompt
    assert "CITATIONS:" in prompt


def test_prompt_builder_comparison_intent():
    builder = PromptBuilder()
    prompt = builder.build(
        history=[],
        context="Doc A vs Doc B",
        question="Compare both documents",
        intent="COMPARISON",
        detail_level="standard",
    )

    assert "COMPARISON & CROSS-DOCUMENT SYNTHESIS RULES:" in prompt
    assert "DYNAMICALLY SELECT RELEVANT COMPARATIVE DIMENSIONS:" in prompt


def test_prompt_builder_invoice_doc_type():
    builder = PromptBuilder()
    prompt = builder.build(
        history=[],
        context="Invoice context",
        question="What is the invoice total?",
        intent="GLOBAL",
        doc_types=["invoice"],
        detail_level="standard",
    )

    assert "DOCUMENT ENTITY ROLES:" in prompt
    assert "FINANCIAL FIELD SYNONYMS:" in prompt


def test_prompt_builder_detail_levels():
    builder = PromptBuilder()

    eli5_prompt = builder.build(
        history=[], context="Ctx", question="Q", detail_level="eli5"
    )
    assert "ELI5" in eli5_prompt or "simple" in eli5_prompt.lower()

    expert_prompt = builder.build(
        history=[], context="Ctx", question="Q", detail_level="expert"
    )
    assert "Expert" in expert_prompt or "technical" in expert_prompt.lower()


def test_prompt_builder_user_memories():
    builder = PromptBuilder()
    memories = ["User prefers concise answers", "User is a data engineer"]

    prompt = builder.build(
        history=[],
        context="Ctx",
        question="Q",
        memories=memories,
    )

    assert "User prefers concise answers" in prompt
    assert "User is a data engineer" in prompt


def test_prompt_builder_toc_intent():
    builder = PromptBuilder()
    prompt = builder.build(
        history=[],
        context="Chapter 1: Intro\nChapter 2: Methods",
        question="Show table of contents",
        intent="TOC",
    )

    assert "TABLE OF CONTENTS (TOC) GRANULARITY:" in prompt
