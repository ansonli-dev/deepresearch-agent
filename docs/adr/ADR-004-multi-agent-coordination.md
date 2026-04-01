# ADR-004: Multi-Agent Coordination, Context Isolation & Tool Routing

## Status

Accepted

## Date

2026-04-01

## Context

By M4, the single-agent system (M1 ReAct loop + M2 planning + M3 memory) is functional but has scaling limitations:

1. **Role confusion**: A single agent prompt must simultaneously be good at searching, analyzing, and writing. The prompt becomes bloated and the LLM struggles to context-switch between roles.
2. **Context pollution**: Search results from one sub-task leak into another's context, causing the agent to conflate findings from unrelated topics.
3. **Sequential bottleneck**: Sub-tasks execute one at a time, even when they're independent.

Claude Code's architecture memo (§5) identifies the solution: **subagents with independent context**. Each subagent has its own `messages[]`, receives only the context it needs, and returns structured results. The memo emphasizes that context isolation is not optional — it's the mechanism that prevents pollution.

The project background document identifies the multi-agent capability as one of the four core agent capabilities the project must demonstrate: "Planner, Researcher, Analyst, Writer each have distinct skills and tools."

## Decision

### 1. Adopt the Supervisor pattern

A central supervisor agent orchestrates specialized worker agents:

```
user_query → supervisor_node → [delegate to workers] → aggregate_results → report_node → END
                    ↑                                          |
                    └──────────────────────────────────────────┘
                              (more work needed)
```

The supervisor:
- Receives the research plan (from M2's planner, now elevated to the supervisor role)
- Assigns sub-tasks to specialized workers
- Collects and aggregates results
- Decides when sufficient data has been gathered
- Delegates final report writing to the Writer agent

### 2. Define four agent roles

| Role | Responsibility | Input | Output |
|------|---------------|-------|--------|
| **Supervisor** | Orchestrate, delegate, aggregate | User query + memory context | Final research report |
| **Researcher** | Web search + content extraction | Sub-task description + relevant prior findings | Raw findings with source URLs |
| **Analyst** | Synthesize, compare, identify patterns | Gathered findings from researchers | Structured analysis with insights |
| **Writer** | Produce final report | Analysis results + report format spec | Formatted Markdown report with citations |

### 3. Enforce context isolation via handoff protocol

Each worker agent starts with a **clean message history**. The supervisor controls what context each worker receives through a strict handoff protocol:

**SubagentInput** (what the supervisor sends):
```python
class SubagentInput(BaseModel):
    task_id: str                    # Unique task identifier
    task_description: str           # What to do (natural language)
    context: str                    # Relevant context subset (NOT full history)
    output_format: str              # Expected output structure
    constraints: list[str]          # Boundaries (max sources, focus areas)
```

**SubagentOutput** (what workers return):
```python
class SubagentOutput(BaseModel):
    task_id: str                    # Matching task identifier
    findings: list[Finding]         # Structured findings
    sources: list[Source]           # Deduplicated source list
    confidence: float               # Self-assessed confidence (0-1)
    token_usage: TokenUsage         # Cost tracking
    summary: str                    # One-paragraph summary for supervisor
```

**Key rule**: The supervisor calls `prepare_subagent_context(full_state, task)` to extract only the relevant subset of context for each worker. Workers never see the full conversation history or other workers' raw outputs.

**Result aggregation**: `aggregate_results(outputs: list[SubagentOutput])` merges findings from multiple workers, deduplicates sources by URL, and produces a unified findings object for the Analyst or Writer.

### 4. Implement per-role tool subsets

Each agent role has access only to tools relevant to its function. This follows Claude Code's dynamic tool selection principle (memo §3):

| Role | Available Tools | Rationale |
|------|----------------|-----------|
| **Supervisor** | `delegate_task` | Delegates, doesn't execute. No search or analysis tools. |
| **Researcher** | `web_search`, `web_fetch`, `memory_recall` | Gathers information from the web and prior research. |
| **Analyst** | `memory_recall`, `memory_store` | Works with already-gathered data. No web access — prevents re-searching. |
| **Writer** | (none) | Receives pre-compiled findings as input. Produces text output only. |

Tool assignment is configured in `configs/agents.yaml`, not hardcoded. A `get_tools_for_role(role: str) -> list[BaseTool]` utility reads the config and returns the appropriate tool subset when creating each sub-graph.

**Benefits of tool restriction**:
- Reduces LLM decision space → more reliable tool selection
- Prevents cross-role confusion (Analyst can't accidentally search the web)
- Makes LangSmith traces clearer (each agent's tool calls match its role)

### 5. Support parallel execution

Independent researcher sub-tasks execute concurrently via LangGraph's `Send` API:

```python
# Supervisor dispatches multiple researchers in parallel
def route_to_researchers(state):
    return [
        Send("researcher", SubagentInput(task_id=t.id, ...))
        for t in state.plan.pending_tasks
        if t.can_parallelize
    ]
```

The supervisor waits for all parallel workers to complete before proceeding to aggregation. Max parallel workers: 3 (configurable, balances speed vs. API rate limits).

### Considered Alternatives

#### Option A: Swarm pattern (peer-to-peer handoff)

Agents hand off work to each other directly, without a central coordinator.

- **Pro**: More flexible. Agents self-organize. Can handle emergent workflows.
- **Con**: Hard to debug (who handed off to whom and why?). No natural aggregation point. Difficult to cap iterations or enforce completion. LangSmith traces become a tangled graph.
- **Rejected because**: Research is a structured process (search → analyze → write) that benefits from central coordination. Swarm's flexibility is not needed and adds debugging complexity.

#### Option B: Network pattern (any-to-any routing)

Any agent can call any other agent. A router decides who handles each request.

- **Pro**: Most flexible topology. Can handle complex agent interactions.
- **Con**: Highest complexity. Routing logic is opaque. Hard to reason about context flow. Overkill for a 4-agent research pipeline.
- **Rejected because**: The research workflow has a clear sequential structure (plan → research → analyze → write). Network topology adds complexity without proportional benefit.

#### Option C: No context isolation (shared state)

All agents share the same LangGraph state and message history.

- **Pro**: Simplest implementation. No handoff protocol needed.
- **Con**: Context pollution — the Writer sees all of the Researcher's raw search results, the Analyst sees the Writer's formatting prompts. As the number of agents and sub-tasks grows, each agent's context becomes dominated by irrelevant information from other agents. This directly degrades output quality.
- **Rejected because**: Claude Code's architecture demonstrates that independent context is essential for multi-agent quality. The handoff protocol cost is worth the isolation benefit.

## Consequences

### Positive

- **Role clarity**: Each agent has a focused prompt and toolset. The Researcher prompt is optimized for search; the Writer prompt is optimized for report formatting. No role confusion.
- **Context quality**: Workers receive only relevant context, improving LLM output quality and reducing token waste.
- **Parallel speedup**: Independent research sub-tasks run concurrently, reducing total research time by up to 3x for multi-topic queries.
- **Debuggability**: LangSmith traces show which agent did what, with what tools, in what order. Each agent's trace is a clean, focused narrative.
- **Progressive enhancement**: The M1 ReAct agent becomes the Researcher's inner loop (ADR-001 immutability). M2's planning becomes the Supervisor's strategy. No prior work is wasted.

### Negative

- **Handoff overhead**: Each subagent dispatch involves serializing context, creating a new graph invocation, and deserializing results. For simple queries, this overhead may exceed the benefit. Consider a fast-path that skips multi-agent for simple questions.
- **Aggregation complexity**: Merging findings from multiple researchers requires deduplication, conflict resolution, and source reconciliation. This is non-trivial and must be tested thoroughly.
- **Tool config maintenance**: `configs/agents.yaml` must be kept in sync with tool implementations. A misconfigured tool assignment can silently degrade an agent's capability.

### Neutral

- **LangSmith trace depth increases**: Multi-agent traces have nested sub-traces. This is more information, not necessarily more complexity, but requires learning to navigate nested traces.
- **Cost per query increases**: Multiple agents = multiple LLM calls. At DeepSeek V3 pricing, a 4-agent research query costs ~¥0.05–0.10, still very affordable. Cost tracking (M1-12) makes this visible.

## References

- [LangGraph Multi-Agent Supervisor tutorial](https://langchain-ai.github.io/langgraph/tutorials/multi_agent/agent_supervisor/) — official implementation pattern
- [LangGraph Send API](https://langchain-ai.github.io/langgraph/concepts/low_level/#send) — parallel agent dispatch
- [Claude Code Architecture Memo §5](../memo/claude-code-architecture-memo.md) — Subagent independent context
- [Claude Code Architecture Memo §3](../memo/claude-code-architecture-memo.md) — Dynamic tool selection
- [Project Background §1.2](../planning/project_background.md) — Four core agent capabilities
- [ADR-001](ADR-001-langgraph-agent-loop.md) — Agent loop immutability: M1 ReAct becomes Researcher's inner loop
- [ADR-002](ADR-002-planning-strategy.md) — Planning strategy: M2 planner elevates to Supervisor role
