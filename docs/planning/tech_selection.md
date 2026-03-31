# DeepResearch Agent — Technical Selection Document

v1.0 · March 2026

---

## 1. Project Overview

Build a production-grade Deep Research Agent that autonomously searches the web, analyzes information, and produces structured research reports. The project serves as a comprehensive learning vehicle for mastering agent technologies while producing a genuinely useful, deployable system.

| Dimension | Decision |
|---|---|
| Agent Framework | LangGraph (LangChain ecosystem) |
| Language | Python 3.12+ |
| LLM Provider | DeepSeek V3 (default) — model-agnostic, provider switching via config |
| Search API | Tavily (primary) + Brave Search (alternative) + custom web_fetch |
| Vector Store | ChromaDB (introduced at M3, not before) |
| Database | SQLite (dev/single-user) → PostgreSQL (multi-user) |
| Package Manager | uv (Astral) |
| Lint / Format | Ruff (replaces flake8 + black + isort) |
| Type Checker | mypy (strict mode) |
| Testing | pytest + pytest-asyncio |
| CI | GitHub Actions |
| Observability | LangSmith (tracing) + structlog (logging) |
| Frontend | Next.js 15 + React 19 + Tailwind CSS + shadcn/ui (M5) |
| Containerization | Docker + Docker Compose (from M2) |
| Deployment | Vercel (frontend) + Railway (API backend) |

---

## 2. LLM Provider

### 2.1 Strategy: Model-agnostic with configurable provider

The system does not bind to a single LLM. Users configure their preferred provider and model via YAML config. The codebase abstracts model access through LangChain's ChatModel interface, making provider switching a config change, not a code change.

### 2.2 Default: DeepSeek V3

| Attribute | Detail |
|---|---|
| Pricing | ¥1 / ¥2 per MTok (input/output) — 极具性价比 |
| Capability | 强大的通用能力，native tool calling，128K context |
| Speed | 高速推理 |
| LangChain | OpenAI-compatible API format，使用 `langchain-openai` 的 `ChatOpenAI` 配合 `base_url` 接入 |
| Monthly est. | ~¥10–20 for development workloads |
| API endpoint | `https://api.deepseek.com` |
| Model IDs | `deepseek-chat` (V3), `deepseek-reasoner` (R1) |

### 2.3 Model switching（后续扩展）

当前阶段只使用 DeepSeek。模型切换功能（支持 Anthropic Claude、OpenAI 等）作为独立功能在后续 milestone 中实现。架构设计保持 model-agnostic（通过 LangChain `BaseChatModel` 接口抽象），确保未来切换只需修改配置。

### 2.4 Cost control measures

- **Prompt caching:** DeepSeek 支持缓存命中价格优惠（cache hit: ¥0.1/MTok input）。
- **Model tiering:** 后续可将轻量任务路由到更便宜的模型。
- **Budget limits:** 已充值 ¥50，足够整个开发阶段使用。在 API 控制台设置消费上限。

---

## 3. Search API

### 3.1 Primary: Tavily

- **AI-native:** Returns LLM-ready structured output with relevance scores and citations. No post-processing needed.
- **LangChain native:** First-class integration, few lines to connect to LangGraph agent.
- **Free tier:** 1,000 credits/month. Covers P0–M1 development. Paid: ~$0.008/query.
- **Content extraction:** Supports both snippet mode and full-page extraction (useful for M3 RAG).

### 3.2 Alternative: Brave Search

Independent index (not Google/Bing dependent). Highest agent benchmark score (14.89). Lowest latency (669ms). Good second option for quality comparison experiments.

### 3.3 Custom web_fetch tool (self-built)

Tavily/Brave handle search result discovery. The web_fetch tool handles page content extraction: httpx for HTTP requests + trafilatura or readability-lxml for article extraction + Markdown conversion. This is your own code, giving full control over content cleaning and formatting.

> **Architecture:**
> - `web_search` tool → Tavily API (search result discovery)
> - `web_fetch` tool → Self-built (page content extraction + cleaning)
> - Both tools are independently configurable and swappable.

---

## 4. Vector Store & Memory

### 4.1 Progressive memory strategy

Most production deep research agents (including LangChain's Open Deep Research) do NOT use a vector database. Research results flow through the agent's state graph. Vector DB is introduced only when persistent semantic retrieval is needed.

| Phase | Memory Type | Technology | Purpose |
|---|---|---|---|
| M1–M2 | In-graph state | LangGraph state dict | Pass data between nodes |
| M3 early | Session persistence | LangGraph Checkpointer + SQLite | Resume conversations |
| M3 late | Semantic retrieval (RAG) | ChromaDB | Search past research findings |
| Future | Production scale | Qdrant (optional upgrade) | Multi-user, filtered search |

### 4.2 ChromaDB (M3)

- **Zero deployment:** `pip install chromadb`, runs in-process. No Docker needed.
- **LangChain integration:** langchain-chroma package, 3 lines to connect.
- **Capacity:** Comfortable up to 10M vectors. More than enough for research findings.

### 4.3 Embedding models (configurable)

- **Default:** text-embedding-3-small (OpenAI) — $0.02/MTok, 1536-dim, high quality.
- **Free alternative:** sentence-transformers/all-MiniLM-L6-v2 — local, 384-dim, zero cost.

---

## 5. Dev Tooling

| Category | Tool | Rationale |
|---|---|---|
| Package mgmt | uv | 10–100x faster than pip/poetry. Auto-manages Python versions. 2026 community standard. |
| Project config | pyproject.toml | Single source of truth. PEP 517/518 compliant. |
| Lint + format | Ruff | Replaces flake8 + black + isort. Same team as uv (Astral). Rust-based. |
| Type checker | mypy (strict) | Pydantic models + LangGraph state benefit from strong typing. |
| Pre-commit | pre-commit | Runs ruff + mypy on every commit automatically. |
| Testing | pytest + pytest-asyncio | LangGraph is async-first. Use FakeListLLM for deterministic tests. |
| CI | GitHub Actions | Free for public repos. Pipeline: uv sync → ruff → mypy → pytest. |
| Agent tracing | LangSmith | Essential for debugging agent behavior. Free tier: 5,000 traces/month. |
| Logging | structlog | Structured JSON logs. Excellent for agent debugging. |

---

## 6. Frontend

### 6.1 Strategy: CLI-first, Web UI at M5

The agent is fully functional via CLI (M1–M4). Web UI is added as M5 after the core agent system is production-ready. This ensures the agent's value is independent of the UI.

### 6.2 CLI (M1–M4)

Built with Rich for formatted terminal output. Supports single-shot and interactive modes. Progressively enhanced as agent capabilities grow.

### 6.3 Web UI (M5): Next.js + React

- **Framework:** Next.js 15 (App Router) + React 19 + TypeScript
- **Styling:** Tailwind CSS + shadcn/ui (high design quality, fully customizable components)
- **Agent integration:** @langchain/langgraph-sdk/react — useStream() hook for streaming, state management, branching
- **Backend connection:** SSE streaming from FastAPI (Python) to Next.js frontend

### 6.4 Architecture

```
┌──────────────────┐         ┌──────────────────┐
│   Next.js UI      │  SSE    │  FastAPI          │
│   React + shadcn  │◄──────►│  LangGraph Agent  │
│   Tailwind CSS    │         │  Python backend   │
└──────────────────┘         └──────────────────┘
     Vercel                    Railway
```

---

## 7. Infrastructure

### 7.1 Database

- **Dev / single-user:** SQLite. LangGraph checkpointer natively supports it. Zero config, file-based.
- **Production / multi-user:** PostgreSQL via langgraph-checkpoint-postgres. One-line migration.

### 7.2 Containerization

Docker introduced at M2 when FastAPI API layer is added. Multi-stage Dockerfile using uv for fast builds. Docker Compose orchestrates all services.

| Phase | Docker Scope |
|---|---|
| M0–M1 | No Docker. Local `uv run` only. |
| M2 | Dockerfile + docker-compose.yml (agent-api service only) |
| M3 | Add ChromaDB service to compose (if using server mode) |
| M4–M5 | Full stack: agent-api + chromadb + web (Next.js) |

### 7.3 Deployment

- **Frontend:** Vercel — zero-config for Next.js, global CDN, generous free tier.
- **Backend API:** Railway — Docker-native, auto-deploy from GitHub, persistent storage.
- **Alternative:** Any VPS with `docker compose up` (you have cloud-native experience).

---

## 8. Milestone Roadmap

Estimated timeline: ~16 weeks. Schedule: 3–4 evenings/week, 3–4 hours each (≈12 hrs/week). Each milestone produces a shippable increment.

| # | Milestone | Core Learning | Duration | Key Output |
|---|---|---|---|---|
| P0 | Python ecosystem + LLM API | uv, DeepSeek API, Tavily | 1 week | Scaffolding + search script |
| M1 | ReAct agent + tool use + CLI | LangGraph core | 2 weeks | Working CLI agent |
| M2 | Planning & reasoning + API | Sub-graphs, FastAPI | 2–3 weeks | Research reports + HTTP API |
| M3 | Memory & RAG | Checkpointing, ChromaDB | 2 weeks | Persistent memory agent |
| M4 | Multi-agent collaboration | Supervisor pattern | 2–3 weeks | Full multi-agent system |
| M5 | Web UI + deployment | React, Next.js, Tailwind | 3–4 weeks | Deployable full-stack app |

---

## 9. Repository Structure

```
deepresearch-agent/
├── src/
│   ├── agents/           # Agent definitions (M4: researcher, analyst, writer)
│   ├── graph/            # LangGraph state graphs and nodes
│   ├── tools/            # Tool implementations (search, fetch, memory)
│   ├── memory/           # RAG pipeline, vector store, checkpointing (M3)
│   ├── prompts/          # System prompts and prompt templates
│   ├── models/           # Pydantic models for state and messages
│   ├── api.py            # FastAPI application (M2+)
│   └── cli.py            # CLI entry point (M1+)
├── web/                  # Next.js frontend (M5)
│   ├── src/app/
│   ├── src/components/
│   └── package.json
├── tests/
├── docs/
│   ├── adr/              # Architecture Decision Records
│   └── til/              # Today I Learned notes
├── configs/
│   └── models.yaml       # Model / provider configuration
├── outputs/              # Generated research reports
├── docker-compose.yml    # (M2+)
├── Dockerfile            # (M2+)
├── pyproject.toml
├── .python-version       # Python 3.12+
├── .env.example
└── README.md
```

---

## 10. Working Agreements

- **Branch strategy:** main (protected) + feature branches. Squash merge.
- **Commit convention:** Conventional Commits (feat:, fix:, docs:, refactor:, chore:).
- **Issue workflow:** Backlog → Todo → In Progress → Done. Max 2 In Progress.
- **Definition of Done:** Tests passing, LangSmith trace verified, docs updated.
- **TIL notes:** After each spike, write a short TIL in docs/til/.
- **ADR format:** MADR template (context, decision, consequences).
- **Language:** Issues in English, documentation bilingual (EN/CN).
- **Project management:** Linear. Each milestone = one Cycle.
- **AI-assisted development:** Use Claude Code extensively for boilerplate, debugging, and learning.

---

## 11. Key Decision Rationale

### Why LangGraph over CrewAI?

LangGraph gives explicit control over state graphs, matching your architecture background. CrewAI is higher-level abstraction, faster to start but less insight into internals. LangGraph is the recommended path for learning agent orchestration deeply.

### Why DeepSeek V3 as default?

¥1/¥2 per MTok 极具性价比。强大的通用能力和 tool calling 支持。OpenAI 兼容 API 降低接入成本。已充值 ¥50，足够开发阶段使用。后续如需切换模型，架构已预留扩展点。

### Why Tavily over building search from scratch?

Web crawling + indexing is a billion-dollar infrastructure problem. Agent projects universally use third-party search APIs. Self-built web_fetch tool handles content extraction, which IS the part worth owning.

### Why no vector DB until M3?

LangChain's Open Deep Research and most similar projects don't use vector DB. Research results flow through agent state. ChromaDB is introduced in M3 specifically as a learning vehicle for RAG, and for the incremental research feature.

### Why Next.js for frontend?

LangGraph SDK provides official React hooks (useStream). GPT Researcher and all major agent templates use Next.js. shadcn/ui delivers high design quality. This is the industry-standard stack for agent frontends in 2026.

### Why SQLite before PostgreSQL?

Zero deployment overhead. LangGraph checkpointer supports both. Single-user dev scenario doesn't need concurrent write handling. Migration to PostgreSQL is a one-line config change when needed.
