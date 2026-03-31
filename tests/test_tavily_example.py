from src.tavily_example import format_results_for_llm

MOCK_RESULTS = [
    {
        "title": "LangGraph Intro",
        "url": "https://example.com/1",
        "content": "LangGraph is a library for building stateful agents.",
    },
    {
        "title": "LangGraph Tutorial",
        "url": "https://example.com/2",
        "content": "In this tutorial we build a ReAct agent.",
    },
]


def test_format_results_contains_urls() -> None:
    formatted = format_results_for_llm(MOCK_RESULTS)
    assert "https://example.com/1" in formatted
    assert "https://example.com/2" in formatted


def test_format_results_has_numbered_labels() -> None:
    formatted = format_results_for_llm(MOCK_RESULTS)
    assert "[1]" in formatted
    assert "[2]" in formatted


def test_format_results_includes_content() -> None:
    formatted = format_results_for_llm(MOCK_RESULTS)
    assert "LangGraph is a library" in formatted
    assert "ReAct agent" in formatted
