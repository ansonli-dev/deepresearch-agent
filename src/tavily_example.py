"""Tavily search → LLM summary pipeline.

This script demonstrates the search-to-answer pipeline (RAG prototype):

    Step 1: Tavily search      — query the web, get structured results
    Step 2: Format results     — convert dicts into numbered text for the LLM
    Step 3: LLM summarization  — DeepSeek writes a cited summary

Data flow for query "LangGraph stateful agents":

┌─ Step 1: search() ─────────────────────────────────────────────────────┐
│                                                                         │
│  Your code  ──HTTP POST──▶  Tavily API  ──▶  returns 5 results         │
│                                                                         │
│  Each result is a dict:                                                 │
│  {                                                                      │
│    "title":   "LangGraph: Building Stateful AI Agents",                 │
│    "url":     "https://medium.com/@kevinnjagi83/...",                   │
│    "content": "LangGraph is a Python library designed to build...",     │
│    "score":   0.95                                                      │
│  }                                                                      │
│                                                                         │
│  Tavily vs Google:                                                      │
│  - Google returns HTML page links — you must scrape content yourself    │
│  - Tavily returns cleaned plain text, optimized for LLM context windows │
└─────────────────────────────────────────────────────────────────────────┘
                    │
                    ▼  list[dict] — 5 search results
                    │
┌─ Step 2: format_results_for_llm() ─────────────────────────────────────┐
│                                                                         │
│  Converts the dicts into numbered text:                                 │
│                                                                         │
│  [1] LangGraph: Building Stateful AI Agents                             │
│      URL: https://medium.com/...                                        │
│      LangGraph is a Python library designed to build...                 │
│                                                                         │
│  [2] LangGraph Agents: Build Stateful, Controllable AI Workflows        │
│      URL: https://www.leanware.co/...                                   │
│      LangGraph agents are stateful AI workflows...                      │
│                                                                         │
│  Why numbered? So the LLM can cite "[1]" "[2]" in its summary.         │
│  Why truncate to 400 chars? To stay within the LLM context window.     │
└─────────────────────────────────────────────────────────────────────────┘
                    │
                    ▼  str — formatted text block
                    │
┌─ Step 3: summarize_with_llm() ─────────────────────────────────────────┐
│                                                                         │
│  Prompt sent to DeepSeek:                                               │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ "Based on the following search results for the query            │    │
│  │  'LangGraph stateful agents', write a 2-3 sentence summary     │    │
│  │  and cite sources by their [number].                            │    │
│  │                                                                 │    │
│  │  [1] LangGraph: Building Stateful AI Agents                     │    │
│  │      URL: https://medium.com/...                                │    │
│  │      LangGraph is a Python library...                           │    │
│  │  [2] ..."                                                       │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  DeepSeek returns:                                                      │
│  "LangGraph is a Python library designed for building stateful,         │
│   multi-agent AI workflows using graph-based control logic [1][2].      │
│   Created by the LangChain team, it enables developers to construct     │
│   complex applications like chatbots [1][3]."                           │
│                                                                         │
│   ↑ [1][2][3] = citation numbers matching the search results above     │
└─────────────────────────────────────────────────────────────────────────┘

This is the manual prototype of the agent's `web_search` tool (M1).
The pattern (search → format → summarize) is the foundation of RAG
(Retrieval-Augmented Generation) — retrieve real info first, then let the
LLM answer based on evidence instead of guessing from memory.
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
