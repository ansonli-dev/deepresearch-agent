# Milestone Log

This document records what was built in each milestone, the key decisions made, and the lessons learned.

---

## P0: Python Ecosystem Bootstrap + LLM API

**Status:** Complete
**Issues:** ANS-5 ~ ANS-15
**Date completed:** 2026-03-31

### What was built

| Issue | What | Why it matters |
|-------|------|----------------|
| ANS-5~10 | Project scaffolding — `pyproject.toml`, uv, Ruff, mypy (strict), pre-commit hooks, GitHub Actions CI | The Python equivalent of a well-configured Java project with Maven + Checkstyle + CI. Every commit is auto-linted, formatted, and type-checked before it lands. |
| ANS-11 | Hello-world LLM call (`src/hello_llm.py`) | Proved DeepSeek V3 works via the OpenAI-compatible API. Key insight: DeepSeek reuses the OpenAI wire protocol, so the `openai` Python SDK works by just changing `base_url`. |
| ANS-12 | Tool calling example (`src/tool_calling_example.py`) | The LLM doesn't execute code — it *requests* function calls. Your code runs the function and feeds results back. This multi-round loop is the foundation of all agent behavior in M1. |
| ANS-13 | Tavily search + LLM summary (`src/tavily_example.py`) | The RAG (Retrieval-Augmented Generation) pattern: search → format → summarize with citations. This becomes the agent's `web_search` tool in M1. |
| ANS-14 | LangSmith tracing (`src/tracing.py`) | Every LLM call through LangChain's `ChatModel` is auto-recorded. Like adding Datadog APM to your Spring Boot app — full observability for free. |
| ANS-15 | README (`README.md`) | The front door for anyone cloning the repo — setup instructions, tech stack, milestone roadmap. |

### Key decisions

- **DeepSeek V3 as default LLM** — cost-effective, OpenAI-compatible API, good enough for development. Model switching deferred to M1 via LangChain's `ChatModel` interface.
- **uv over pip/poetry** — Rust-based, 10-100x faster, manages Python versions, replaces pip + virtualenv + pip-tools in one binary.
- **Ruff over flake8 + black + isort** — single tool, Rust-based, covers linting and formatting.
- **mypy strict mode from day one** — catches type errors early; easier to start strict than to migrate later.
- **Editable install via `[build-system]`** — enables `from src.xxx import yyy` imports throughout the project.

### Java analogies (for reference)

| Python (this project) | Java equivalent |
|----------------------|-----------------|
| `pyproject.toml` | `pom.xml` / `build.gradle` |
| `uv` | Maven / Gradle |
| `Ruff` | Checkstyle + Google Java Format |
| `mypy` | Java's built-in type system (but opt-in) |
| `pre-commit` | Maven Enforcer + git hooks |
| `pytest` | JUnit |
| `pydantic-settings` | Spring `@ConfigurationProperties` |
| `.env` → `Settings` | `application.yml` → `@Value` |

---

## M1: ReAct Agent + CLI

**Status:** In Progress
**Issues:** TBD

*To be filled as M1 issues are completed.*

---

## M2: Planning & Reasoning Sub-graphs + FastAPI

**Status:** Planned

*To be filled as M2 issues are completed.*

---

## M3: Memory + RAG

**Status:** Planned

*To be filled as M3 issues are completed.*

---

## M4: Multi-Agent Collaboration

**Status:** Planned

*To be filled as M4 issues are completed.*

---

## M5: Next.js Web UI + Deployment

**Status:** Planned

*To be filled as M5 issues are completed.*
