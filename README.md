# DeepResearch Agent

An autonomous research agent that searches the web, analyzes information,
and produces structured research reports with citations.
Built with LangGraph + Python 3.12.

## Tech Stack

| Layer             | Technology                          |
|-------------------|-------------------------------------|
| Agent framework   | LangGraph (LangChain ecosystem)     |
| Language          | Python 3.12+                        |
| Package manager   | uv (Astral)                         |
| Lint / Format     | Ruff                                |
| Type checker      | mypy (strict mode)                  |
| Testing           | pytest                              |
| LLM (default)     | DeepSeek V3 (`deepseek-chat`)       |
| LLM (premium)     | DeepSeek Reasoner (`deepseek-reasoner`) |
| Search            | Tavily                              |
| Observability     | LangSmith                           |

## Prerequisites

- **uv** installed — `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Python 3.12** — uv manages this automatically
- API keys: [DeepSeek](https://platform.deepseek.com/), [Tavily](https://tavily.com/), [LangSmith](https://smith.langchain.com/) (optional)

## Setup

```bash
git clone https://github.com/ansonli-dev/deepresearch-agent.git
cd deepresearch-agent
uv sync
cp .env.example .env
# Edit .env and add your API keys
uv run pre-commit install
```

## Verify Installation

```bash
# Test LLM call
uv run python -m src.hello_llm

# Test LLM call with LangSmith tracing
uv run python -m src.hello_llm --traced

# Test search → LLM summary pipeline
uv run python -m src.tavily_example "What is LangGraph?"

# Run all tests
uv run pytest
```

## Development

```bash
uv run ruff check .       # lint
uv run ruff format .      # format
uv run mypy src/          # type check
uv run pytest             # test
```

## Project Structure

```
src/
├── models/       # Pydantic models and config
├── agents/       # Agent definitions (M4)
├── graph/        # LangGraph state graphs and nodes (M1+)
├── tools/        # Tool implementations (M1+)
├── memory/       # RAG pipeline, vector store (M3)
├── prompts/      # System prompts and templates (M1+)
├── tracing.py    # LangSmith observability config
├── hello_llm.py  # Hello-world LLM call
├── tavily_example.py       # Search → LLM summary pipeline
├── tool_calling_example.py # Tool calling with calculator
├── cli.py        # CLI entry point (M1+)
└── api.py        # FastAPI application (M2+)
configs/
└── models.yaml   # Model/provider configuration
docs/
├── planning/     # Project background, tech selection
├── adr/          # Architecture Decision Records
└── til/          # Today I Learned notes
```

## Milestone Roadmap

| Milestone | Description                             | Status      |
|-----------|-----------------------------------------|-------------|
| P0        | Scaffolding, tooling, hello-world LLM   | Complete    |
| M1        | ReAct agent + CLI                       | In Progress |
| M2        | FastAPI + planning sub-graphs           | Planned     |
| M3        | Memory + RAG                            | Planned     |
| M4        | Multi-agent collaboration               | Planned     |
| M5        | Next.js web UI + deployment             | Planned     |

## Further Reading

- [Project Background](docs/planning/project_background.md) — motivation, goals, and success criteria
- [Technical Selection](docs/planning/tech_selection.md) — rationale for every technology choice
