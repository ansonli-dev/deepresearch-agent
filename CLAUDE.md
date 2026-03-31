# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DeepResearch Agent — a production-grade autonomous research agent that searches the web, analyzes information, and produces structured research reports with citations. Built as a full-stack application progressing through 6 milestones (P0→M5).

## Tech Stack

- **Agent framework:** LangGraph (LangChain ecosystem)
- **Language:** Python 3.12+
- **Package manager:** uv (Astral)
- **Lint/format:** Ruff (replaces flake8 + black + isort)
- **Type checker:** mypy (strict mode)
- **Testing:** pytest + pytest-asyncio
- **LLM:** DeepSeek V3 (default) — model-agnostic via LangChain ChatModel, provider switching via config
- **Search:** Tavily (primary), Brave Search (alternative), custom web_fetch tool
- **Vector store:** ChromaDB (introduced at M3)
- **API:** FastAPI (M2+)
- **Frontend:** Next.js 15 + React 19 + TypeScript + Tailwind CSS + shadcn/ui (M5)
- **Observability:** LangSmith (tracing) + structlog (logging)
- **Database:** SQLite (dev) → PostgreSQL (production)
- **CI:** GitHub Actions

## Build & Development Commands

```bash
# Install dependencies
uv sync

# Run the CLI agent
uv run python -m src.cli

# Run the API server (M2+)
uv run uvicorn src.api:app --reload

# Lint and format
uv run ruff check .
uv run ruff format .

# Type checking
uv run mypy src/

# Run all tests
uv run pytest

# Run a single test
uv run pytest tests/path/to/test_file.py::test_name -v

# Docker (M2+)
docker compose up
```

## Architecture

### Milestone Progression

Each milestone builds on the previous and produces a shippable increment:

- **P0:** Python ecosystem scaffolding + LLM API + Tavily search script
- **M1:** ReAct agent + tool use + CLI (LangGraph core)
- **M2:** Planning & reasoning sub-graphs + FastAPI HTTP API
- **M3:** Memory & RAG — LangGraph checkpointing + ChromaDB
- **M4:** Multi-agent collaboration — supervisor pattern with researcher, analyst, writer agents
- **M5:** Next.js web UI + cloud deployment (Vercel + Railway)

### Repository Structure

```
src/
├── agents/       # Agent definitions (M4: researcher, analyst, writer)
├── graph/        # LangGraph state graphs and nodes
├── tools/        # Tool implementations (search, fetch, memory)
├── memory/       # RAG pipeline, vector store, checkpointing (M3)
├── prompts/      # System prompts and prompt templates
├── models/       # Pydantic models for state and messages
├── api.py        # FastAPI application (M2+)
└── cli.py        # CLI entry point (M1+)
web/              # Next.js frontend (M5)
configs/
└── models.yaml   # Model/provider configuration
```

### Key Architectural Decisions

- **Model-agnostic design:** LLM access is abstracted through LangChain's ChatModel interface. Provider switching is a config change, not a code change.
- **No vector DB before M3:** Research results flow through LangGraph state. ChromaDB is added only when persistent semantic retrieval is needed.
- **CLI-first:** The agent is fully functional via CLI (M1–M4). Web UI is layered on top at M5.
- **Search architecture:** `web_search` tool → Tavily API (discovery); `web_fetch` tool → self-built with httpx + trafilatura (content extraction). Both independently swappable.
- **Supervisor pattern (M4):** Central supervisor agent delegates to specialized worker agents (researcher, analyst, writer).
- **SSE streaming:** FastAPI streams agent responses to Next.js frontend via Server-Sent Events.

## Project Documentation

Detailed project context is maintained in human-readable documents under `docs/`:

- **Project Background:** [`docs/planning/project_background.md`](docs/planning/project_background.md) — motivation, goals, non-goals, success criteria, risks
- **Technical Selection:** [`docs/planning/tech_selection.md`](docs/planning/tech_selection.md) — rationale for every technology choice
- **ADR Template:** [`docs/adr/template.md`](docs/adr/template.md) — MADR template for architecture decisions

Refer to these documents when you need deeper context on *why* a technology or pattern was chosen.

## Conventions

- **Commits:** Conventional Commits format (feat:, fix:, docs:, refactor:, chore:)
- **Branches:** main (protected) + feature branches, squash merge
- **Docs:** ADRs in `docs/adr/`, TIL notes in `docs/til/`, planning docs in `docs/planning/`
- **Config:** All model/provider config in YAML (`configs/models.yaml`), not hardcoded
- **Pre-commit:** Runs ruff + mypy on every commit
- **Definition of Done:** Tests passing, LangSmith trace verified, docs updated
