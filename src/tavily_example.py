"""Tavily search → LLM summary pipeline.

This script demonstrates the search-to-answer pipeline:
1. Query Tavily for web results (cleaned text, not raw HTML)
2. Format results into a text block for the LLM
3. Ask DeepSeek to summarize with citations

This is the manual prototype of the agent's `web_search` tool (M1).
The pattern (search → format → summarize) is the foundation of RAG
(Retrieval-Augmented Generation).
"""

import argparse
from typing import Any

from openai import OpenAI
from tavily import TavilyClient

from src.models.config import Settings


def search(query: str, api_key: str, max_results: int = 5) -> list[dict[str, Any]]:
    """Query Tavily and return structured results."""
    client = TavilyClient(api_key=api_key)
    response = client.search(
        query=query,
        search_depth="basic",
        max_results=max_results,
        include_answer=False,
    )
    return response["results"]  # type: ignore[no-any-return]


def format_results_for_llm(results: list[dict[str, Any]]) -> str:
    """Convert Tavily results into a text block the LLM can reason over.

    Example output:
        [1] LangGraph Introduction
            URL: https://example.com/langgraph
            LangGraph is a library for building stateful agents...
    """
    lines: list[str] = []
    for i, r in enumerate(results, start=1):
        lines.append(f"[{i}] {r['title']}")
        lines.append(f"    URL: {r['url']}")
        content = r.get("content", "")[:400]
        lines.append(f"    {content}")
        lines.append("")
    return "\n".join(lines)


def summarize_with_llm(query: str, formatted_results: str, api_key: str) -> str:
    """Ask DeepSeek to produce a cited summary of the search results."""
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com",
    )
    prompt = (
        f"Based on the following search results for the query '{query}', "
        "write a 2-3 sentence summary and cite sources by their [number].\n\n"
        f"{formatted_results}"
    )
    response = client.chat.completions.create(
        model="deepseek-chat",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content or ""


def main() -> None:
    parser = argparse.ArgumentParser(description="Tavily search → LLM summary")
    parser.add_argument("query", nargs="?", default="What is LangGraph?")
    args = parser.parse_args()

    settings = Settings()  # type: ignore[call-arg]

    print(f"Searching for: {args.query}\n")

    results = search(args.query, settings.tavily_api_key)
    formatted = format_results_for_llm(results)

    print("=== Search Results ===")
    print(formatted)

    print("=== LLM Summary ===")
    summary = summarize_with_llm(args.query, formatted, settings.deepseek_api_key)
    print(summary)


if __name__ == "__main__":
    main()
