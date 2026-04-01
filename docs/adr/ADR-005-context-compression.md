# ADR-005: Context Compression Strategy & Token Budget Management

## Status

Accepted

## Date

2026-04-01

## Context

A research agent accumulates context rapidly. Each web search returns 5–10 results (~2K tokens each), and each `web_fetch` extracts full page content (~5K–20K tokens). A research session with 5 searches and 3 full-page fetches can easily reach 50K–80K tokens — within DeepSeek V3's 128K context window, but consuming budget that should be reserved for reasoning, planning, and synthesis.

Without active compression, two failure modes emerge:

1. **Context overflow**: The context window fills with raw search results, leaving insufficient room for the LLM to reason about findings and generate a coherent report.
2. **Attention dilution**: Even within the context window, the LLM's attention degrades as message history grows. Key findings from early searches are "forgotten" — buried under later results.

Claude Code addresses this with a three-layer compression strategy (architecture memo §7):

| Layer | Trigger | Action |
|-------|---------|--------|
| Layer 1 | Context reaches threshold | Rolling summary of early findings |
| Layer 2 | Summary itself grows large | Compress the summary |
| Layer 3 | Extreme case | Retain only key decisions and current task state |

For the research agent, the question is not *whether* to compress, but *when* and *how* — and crucially, what to preserve vs. discard.

## Decision

### 1. Implement a `summarize_findings` node in the M2 research graph

A dedicated graph node performs context compression. It is triggered by a conditional edge based on token count, not by the LLM's discretion:

```
tool_node → token_check_edge → [over threshold?]
                                      |
                              yes → summarize_findings → agent_node
                              no  → agent_node (direct)
```

This is a graph-orchestrated mechanism (ADR-002 boundary principle): the graph decides *when* to compress; the LLM decides *how* to compress (what to keep, what to discard).

### 2. Define the token budget model

The agent's context window is divided into budget zones:

| Zone | Allocation | Purpose |
|------|-----------|---------|
| **System prompt** | ~2K tokens (fixed) | Role definition, tool descriptions |
| **Research plan** | ~1K tokens (fixed) | Current plan and progress |
| **Findings** | 60% of remaining capacity | Accumulated research results |
| **Reasoning headroom** | 40% of remaining capacity | LLM thinking + response generation |

**Compression trigger**: When the findings zone exceeds its allocation (60% of remaining context capacity), route through `summarize_findings`.

For DeepSeek V3 (128K context):
- System + plan: ~3K tokens
- Findings budget: ~75K tokens (60% of 125K remaining)
- Reasoning headroom: ~50K tokens
- **Trigger**: Compress when accumulated findings exceed ~75K tokens

### 3. Preserve citations, discard boilerplate

The summarization prompt instructs the LLM to:

**Preserve**:
- Source URLs (essential for citations in final report)
- Key facts, data points, statistics
- Direct quotes that support findings
- Contradictions between sources (important for analysis)
- Metadata: source credibility indicators, publication dates

**Discard**:
- Navigation text, cookie banners, footer content (should be cleaned by `web_fetch`, but may leak through)
- Repeated information across multiple sources
- Tangential content not relevant to the current research question
- Verbose explanations when a concise summary suffices

### 4. State design

```python
class ResearchState(TypedDict):
    # ... existing fields ...
    raw_findings: list[dict]        # Full tool outputs (preserved for debugging)
    findings_summary: str           # Compressed findings (used for reasoning)
    total_findings_tokens: int      # Running token count
    compression_count: int          # How many times compression has occurred
```

- `raw_findings`: Append-only list of all tool outputs. Not sent to the LLM after compression. Preserved for debugging, LangSmith trace inspection, and potential re-processing.
- `findings_summary`: The compressed version. After compression, this replaces raw findings in the LLM's context.
- Each compression cycle updates `findings_summary` — if the summary itself grows too large (Layer 2), it gets re-compressed.

### 5. Progressive compression across milestones

| Milestone | Compression Capability |
|-----------|----------------------|
| **M2** | Layer 1: `summarize_findings` node with token threshold trigger |
| **M3** | Layer 1 + persistent memory: compressed findings can be stored in ChromaDB for cross-session retrieval |
| **M4** | Layer 1 + per-subagent compression: each worker agent independently compresses its findings before returning to supervisor |

Layer 2 (compress the summary) and Layer 3 (extreme compression) are implemented as needed — if M2 testing shows Layer 1 is sufficient for typical research sessions, Layers 2-3 are deferred.

### Considered Alternatives

#### Option A: No compression — rely on large context window

DeepSeek V3 has 128K context. Just use all of it.

- **Pro**: Zero implementation effort. No information loss.
- **Con**: 128K is large but not infinite. 10 web searches with full-page fetches can reach 100K+. More importantly, LLM attention quality degrades with context length — even within the window, the model performs worse on information buried in the middle of a long context.
- **Rejected because**: "It fits" is not the same as "it works well." Compression improves reasoning quality, not just capacity.

#### Option B: Aggressive up-front filtering

Only keep the top-3 most relevant results from each search. Discard everything else immediately.

- **Pro**: Keeps context small throughout. Simple.
- **Con**: Relevance judgment at search time is unreliable — a result that seems marginal may become critical when combined with later findings. Information discarded early cannot be recovered.
- **Rejected because**: Premature filtering loses information that may prove valuable. Compression after accumulation is safer — the LLM sees all results before deciding what's important.

#### Option C: Model-driven compression (LLM decides when to compress)

Give the agent a `compress_context` tool and let it decide when to use it.

- **Pro**: Model knows best when it's struggling with context length.
- **Con**: LLMs rarely self-diagnose context overload. They degrade gradually — outputs get worse without the model "noticing." By the time the model might decide to compress, quality has already suffered.
- **Rejected because**: Compression timing should be graph-orchestrated (proactive, based on measurable thresholds), not model-driven (reactive, based on subjective judgment). This aligns with ADR-002's graph-vs-model boundary.

## Consequences

### Positive

- **Longer research sessions**: The agent can perform 10-20+ searches per session without hitting context limits, enabling deeper research than the raw context window would support.
- **Better reasoning quality**: By keeping the context focused on distilled findings rather than raw noise, the LLM's synthesis and report generation improves.
- **Cost efficiency**: Compressed context means fewer input tokens in subsequent LLM calls. For a 10-step research session, compression can reduce total token consumption by 30-50%.
- **Foundation for M4**: Per-subagent compression means each worker returns a concise summary to the supervisor, keeping the supervisor's context clean.

### Negative

- **Information loss**: Compression is inherently lossy. Key details may be summarized away. Mitigated by preserving `raw_findings` for debugging and re-processing.
- **Compression cost**: Each compression cycle is an LLM call (~2K output tokens). At DeepSeek V3 pricing, this is ~¥0.004 per compression — negligible.
- **Added latency**: The compression step adds one LLM call's worth of latency (~1-3 seconds) each time it triggers.

### Neutral

- **Token counting accuracy**: Different tokenizers produce different counts. Using `tiktoken` for OpenAI-compatible models is a reasonable approximation for DeepSeek V3. The 60% threshold has enough buffer to absorb tokenizer variance.

## References

- [Claude Code Architecture Memo §7](../memo/claude-code-architecture-memo.md) — Three-layer context compaction strategy
- [ADR-001](ADR-001-langgraph-agent-loop.md) — Agent loop immutability: compression is an outer-layer node
- [ADR-002](ADR-002-planning-strategy.md) — Graph-orchestration vs. model-strategy boundary
- [ADR-003](ADR-003-memory-architecture.md) — Cross-session memory (ChromaDB); this ADR covers in-session compression
- [Tech Selection Document §2](../planning/tech_selection.md) — DeepSeek V3: 128K context, cost model
