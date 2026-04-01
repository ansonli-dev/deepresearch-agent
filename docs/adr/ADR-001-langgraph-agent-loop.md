# ADR-001: LangGraph Choice + Agent Loop Immutability Principle

## Status

Accepted

## Date

2026-04-01

## Context

The DeepResearch Agent needs an agent orchestration framework to manage the reasoning-acting-observing loop, tool dispatch, state management, and eventually multi-agent coordination (M4). The core agent loop — the mechanism by which the LLM reasons, calls tools, observes results, and decides next steps — is the most fundamental architectural decision in the project.

Three requirements constrain this choice:

1. **Learning depth**: The project is a learning vehicle for agent engineering. The framework should expose internals, not hide them behind high-level abstractions.
2. **Progressive complexity**: The architecture must support P0's simple scripts, M1's single ReAct agent, M2's planning sub-graphs, M3's checkpointing/RAG, and M4's multi-agent supervisor — without rewriting the core loop at each stage.
3. **Model-agnostic design**: The agent loop must work with any LLM provider (DeepSeek, OpenAI, Anthropic) through a uniform interface.

Additionally, Claude Code's architecture (studied in the project's architecture memo) demonstrates a key principle: **the agent loop itself never changes**. All new capabilities (planning, sub-agents, context compression) are layered on top as outer mechanisms, never injected as conditional logic inside the loop. This "Harness Engineering" philosophy — where the code provides tools, knowledge, and boundaries while the model provides intelligence — should guide our design.

## Decision

### 1. Use LangGraph as the agent orchestration framework

LangGraph provides explicit state graph abstractions (nodes, edges, conditional routing) that match the project's need for transparency and progressive complexity.

### 2. Enforce the Agent Loop Immutability Principle

The core ReAct loop is defined once in M1 and never modified in subsequent milestones:

```
agent_node → [conditional: tool_use?] → tool_node → agent_node
                                      → END (text response)
```

All M2–M5 extensions are implemented as **outer-layer additions**, not inner-loop modifications:

| Milestone | Extension | Implementation |
|-----------|-----------|----------------|
| M2 | Planning | New `planner_node` and `replanner_node` before/after the ReAct loop |
| M2 | Context compression | New `summarize_findings` node, triggered by conditional edge based on token count |
| M2 | Deviation detection | Conditional edge after `tool_node` that routes through a reminder injection node |
| M3 | Checkpointing | LangGraph Checkpointer wraps the entire graph — zero changes to loop |
| M3 | Memory/RAG | New tools (`memory_store`, `memory_recall`) registered with the agent — loop unchanged |
| M4 | Multi-agent | Supervisor graph contains M1 ReAct loop as a sub-graph — loop unchanged |

**The rule**: if implementing a feature requires adding `if-else` inside `agent_node` or `tool_node`, the design is wrong. Find an outer-layer approach.

### Considered Alternatives

#### Option A: Raw LangChain AgentExecutor

LangChain's `AgentExecutor` provides a ready-made ReAct loop with tool dispatch.

- **Pro**: Fewer lines of code for M1. Built-in error handling and iteration limits.
- **Con**: Opaque loop internals. Hard to add planning nodes, conditional routing, or sub-graphs. No first-class state graph — customization requires monkey-patching or subclassing. LangChain docs themselves recommend migrating to LangGraph for new projects.
- **Rejected because**: Cannot support M2 sub-graphs or M4 multi-agent without significant workarounds.

#### Option B: LlamaIndex Workflows

LlamaIndex's Workflows module provides event-driven agent orchestration.

- **Pro**: Event-driven model is elegant. Good for RAG-heavy applications.
- **Con**: Smaller community and fewer multi-agent examples. Less mature than LangGraph for stateful agent orchestration. Tighter coupling with LlamaIndex's own retrieval stack.
- **Rejected because**: LangGraph's explicit state graph model better matches the project's learning goals and progressive complexity requirements.

#### Option C: Custom loop (no framework)

Build the ReAct loop from scratch with plain Python.

- **Pro**: Maximum transparency. No framework lock-in. Educational.
- **Con**: Must re-implement state management, checkpointing, streaming, tool dispatch, error handling — all of which LangGraph provides out of the box. Significantly more work for M2–M4 features.
- **Rejected because**: The learning value of building a framework is outweighed by the learning value of building a sophisticated agent application on top of a good framework.

## Consequences

### Positive

- **M2–M5 features are additive, not invasive**: New capabilities never break existing agent loop behavior. The M1 ReAct agent continues to work exactly as built, even after M4 wraps it in a supervisor.
- **Testability**: The core loop can be tested in isolation with `FakeListLLM`. Outer-layer features (planning, compression) are tested independently.
- **LangGraph ecosystem**: Native support for checkpointing (M3), sub-graphs (M2/M4), streaming (M1+), and LangSmith tracing (P0+). These are not add-ons — they're designed to work with the state graph model.
- **Learning transfer**: LangGraph's explicit graph model teaches state machine thinking that transfers to any agent framework.

### Negative

- **LangGraph learning curve**: LangGraph's state graph abstraction requires understanding nodes, edges, state reducers, and conditional routing before writing the first agent. This is mitigated by M1-1 (spike task).
- **Framework coupling**: Switching away from LangGraph after M1 would be expensive. This is acceptable because LangGraph is production-stable with strong backwards compatibility, and the project's milestone structure means we validate the choice early.
- **Immutability discipline**: Enforcing "no changes to the core loop" requires discipline. Future developers might be tempted to add a quick `if` inside `agent_node` rather than designing a proper outer-layer node. Code review and this ADR serve as guardrails.

### Neutral

- **LangSmith dependency**: LangGraph's tracing is deeply integrated with LangSmith. This is acceptable for the project's observability goals (LangSmith free tier: 5,000 traces/month).
- **Python-only**: LangGraph is Python-only, which aligns with the project's tech stack.

## References

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/) — concepts, tutorials, API reference
- [LangGraph vs AgentExecutor migration guide](https://python.langchain.com/docs/how_to/migrate_agent/) — LangChain's official recommendation to use LangGraph
- [Claude Code Architecture Memo §1–§2](../memo/claude-code-architecture-memo.md) — Harness Engineering philosophy and Agent Loop design
- [Tech Selection Document §1](../planning/tech_selection.md) — LangGraph rationale
- [Project Background §5](../planning/project_background.md) — Reference projects comparison
