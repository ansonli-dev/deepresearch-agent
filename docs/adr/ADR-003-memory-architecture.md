# ADR-003: Memory Architecture & Retention Policy

## Status

Accepted

## Date

2026-04-01

## Context

The M1–M2 agent is stateless — each research session starts from scratch. This creates two problems:

1. **Redundant work**: If a user researches "AI regulation in the EU" on Monday and "GDPR enforcement trends" on Wednesday, the agent re-searches overlapping information instead of building on prior findings.
2. **No session continuity**: If the agent is interrupted mid-research (timeout, crash, user closes CLI), all progress is lost.

The M3 milestone introduces persistent memory to solve both problems. But "memory" in an agent system is not monolithic — it serves multiple purposes with different storage requirements, access patterns, and retention policies.

Claude Code's architecture memo (§6, §8) highlights two key principles:
- **Knowledge should be loaded on demand**, not pre-stuffed into the system prompt
- **Task state should be persistent**, enabling cross-session recovery

The tech selection document (§4) defines a progressive memory strategy that avoids premature complexity: no vector DB before M3, SQLite before PostgreSQL.

## Decision

### 1. Two-memory-system architecture

The agent uses two distinct memory systems, each serving a different purpose:

| System | Technology | Purpose | Access Pattern | Lifecycle |
|--------|-----------|---------|---------------|-----------|
| **Conversation memory** | LangGraph Checkpointer + SQLite | Session state: message history, plan progress, partial results | Keyed by `thread_id` | Per-session, retained for resume |
| **Semantic memory** | ChromaDB | Research knowledge: past findings, extracted facts, source metadata | Similarity search by query embedding | Long-term, pruned by policy |

These are NOT redundant — they answer different questions:
- Conversation memory: "Where was I in this research session?" (exact recall)
- Semantic memory: "What do I already know about this topic?" (fuzzy retrieval)

### 2. Conversation memory via LangGraph Checkpointer

- **Backend**: SQLite (dev/single-user) → PostgreSQL (production, one-line migration via `langgraph-checkpoint-postgres`)
- **Granularity**: Checkpoint after every node execution (LangGraph default)
- **Keying**: Each research session gets a unique `thread_id`
- **Resume**: `graph.invoke(None, config={"configurable": {"thread_id": "existing-id"}})` resumes from last checkpoint
- **No custom code needed**: LangGraph Checkpointer is a built-in capability, not an add-on

### 3. Semantic memory via ChromaDB

- **Deployment**: In-process (`chromadb` Python package, zero infrastructure). Docker Compose server mode optional (M3-9).
- **Collection design**: One collection per knowledge domain initially. May split into `research_findings`, `source_metadata` if needed.
- **Embedding model**: Configurable (M3-10). Default: `text-embedding-3-small` (OpenAI, $0.02/MTok, 1536-dim). Free alternative: `all-MiniLM-L6-v2` (local, 384-dim).
- **Document schema**:
  ```
  {
    "id": "<hash of content>",
    "content": "<research finding text>",
    "metadata": {
      "source_url": "https://...",
      "query": "<original search query>",
      "session_id": "<thread_id>",
      "timestamp": "2026-04-01T12:00:00Z",
      "relevance_score": 0.85
    }
  }
  ```
- **Access as tools**: `memory_store` and `memory_recall` are LangGraph tools. The agent decides when to use them — this follows the "knowledge on demand" principle (Claude Code memo §6).

### 4. Retention policy

Unbounded memory growth degrades retrieval quality and increases storage costs. The policy:

| Rule | Threshold | Action |
|------|-----------|--------|
| **Collection size cap** | 10,000 documents per collection | Prune oldest documents when exceeded |
| **Age-based pruning** | 90 days | Documents older than 90 days are candidates for pruning |
| **Relevance floor** | Relevance score < 0.3 | Low-relevance documents pruned first |
| **Deduplication** | Content hash | Identical content is not stored twice (idempotent writes) |

Pruning is triggered by `memory prune` CLI command (M3-8), not automatically. This gives the user control over their knowledge base.

### 5. Integration with planner (M3-6)

The planner node in M2's planning sub-graph is enhanced to query semantic memory before generating a research plan:

```
user_query → memory_recall(query) → planner_node(query + prior_findings) → ...
```

If relevant prior findings exist, the planner can:
- Skip sub-tasks that are already well-covered
- Focus on gaps in existing knowledge
- Reference prior findings in the final report

### Considered Alternatives

#### Option A: Single unified memory (vector DB for everything)

Store both conversation state and research findings in ChromaDB.

- **Pro**: Single system to manage.
- **Con**: Vector stores are optimized for similarity search, not exact state recovery. Reconstructing conversation history from embeddings is lossy and slow. LangGraph's Checkpointer is purpose-built for state recovery.
- **Rejected because**: Using the wrong tool for conversation state. Two systems, each fit for purpose, is better than one system doing both jobs poorly.

#### Option B: PostgreSQL for everything

Use PostgreSQL for both checkpointing and vector search (via pgvector extension).

- **Pro**: Single database. Simpler deployment. pgvector is production-proven.
- **Con**: Adds PostgreSQL dependency in M3, which is premature — SQLite is sufficient for single-user dev. pgvector requires PostgreSQL server management. ChromaDB is zero-deployment.
- **Rejected because**: Violates the progressive complexity principle. PostgreSQL is the right choice for production multi-user (noted in tech_selection.md §7.1), but not for M3 learning and development.

#### Option C: No vector DB — use LLM long context as "memory"

With 128K context (DeepSeek V3), just prepend past research summaries to the prompt.

- **Pro**: Zero infrastructure. Simple.
- **Con**: Scales linearly with history — after 20 research sessions, the prompt is dominated by old findings. No semantic retrieval — the LLM must read everything to find what's relevant. Cost grows with each session.
- **Rejected because**: Doesn't scale beyond a few sessions. The ADR-005 context compression strategy addresses in-session context management; cross-session knowledge needs a proper retrieval system.

## Consequences

### Positive

- **Session resume works out of the box**: LangGraph Checkpointer handles the complexity of serializing/restoring graph state. The agent can crash and resume exactly where it left off.
- **Incremental research**: "Tell me more about X" can start from prior knowledge instead of from scratch. This is a significant UX improvement.
- **Zero-deployment for development**: Both SQLite (Checkpointer) and ChromaDB (in-process) require no external services during development.
- **Clean separation**: Conversation memory and semantic memory have different lifecycles, access patterns, and scaling needs. Separating them allows independent optimization.

### Negative

- **Two systems to understand**: Developers must understand both LangGraph Checkpointer semantics and ChromaDB embedding/retrieval. Mitigated by M3-1 spike task.
- **Embedding cost**: Storing research findings requires embedding each document. With `text-embedding-3-small` at $0.02/MTok, embedding 1,000 research findings (~500K tokens) costs ~$0.01. Negligible, but not zero.
- **Retention policy is manual**: Pruning requires the user to run `memory prune`. Automatic pruning could be added later but is out of M3 scope.

### Neutral

- **ChromaDB → Qdrant migration path**: If the project outgrows ChromaDB (unlikely for single-user), Qdrant is a drop-in upgrade with LangChain's vector store abstraction. The tech_selection.md notes this option.
- **Embedding model switching**: The configurable embedding model (M3-10) means switching from OpenAI to local embeddings changes the cost profile but not the architecture.

## References

- [LangGraph Persistence Documentation](https://langchain-ai.github.io/langgraph/concepts/persistence/) — Checkpointer API and usage
- [ChromaDB Documentation](https://docs.trychroma.com/) — collection management, embedding, and querying
- [Claude Code Architecture Memo §6](../memo/claude-code-architecture-memo.md) — Knowledge on demand (not pre-loaded)
- [Claude Code Architecture Memo §8](../memo/claude-code-architecture-memo.md) — Task persistence with dependency graphs
- [Tech Selection Document §4](../planning/tech_selection.md) — Progressive memory strategy and ChromaDB rationale
- [ADR-005](ADR-005-context-compression.md) — Context compression (in-session); this ADR covers cross-session memory
