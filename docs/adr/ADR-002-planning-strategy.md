# ADR-002: Planning Strategy, Replanning Heuristics & Deviation Detection

## Status

Accepted

## Date

2026-04-01

## Context

The M1 ReAct agent handles simple queries well — it searches, reads, and responds. But for complex research questions ("Compare the economic policies of BRICS nations in 2025"), a single ReAct loop tends to either:

1. **Tunnel-vision**: Fixate on the first search result and miss important dimensions
2. **Wander**: Chase interesting tangents without converging on a comprehensive answer
3. **Overflow**: Accumulate so many tool results that the context window is consumed before synthesis

Claude Code's architecture memo (§4) confirms this with a clear principle: **"没有计划的 Agent 会漫无目的地游荡"** (an agent without a plan wanders aimlessly). Claude Code solves this with a TodoWrite mechanism — the agent creates a plan, executes it step by step, and gets reminded when it deviates.

The M2 milestone must introduce structured planning that decomposes research questions into sub-tasks, adapts when results are thin, and stays focused on the original question.

Additionally, there is an important **architectural boundary** to define: what does the graph orchestrate vs. what does the model decide?

## Decision

### 1. Adopt the Plan-and-Execute pattern with replanning

The research graph introduces three new node types around the existing M1 ReAct loop:

```
user_query → planner_node → executor_node (M1 ReAct loop) → replanner_node
                                ↑                                  |
                                └──────────────────────────────────┘
                                         (more sub-tasks remain)
                                                   |
                                            (all done) → report_node → END
```

- **Planner node**: Decomposes the research question into 3–7 sub-tasks with expected outcomes
- **Executor node**: Runs the M1 ReAct agent (as a sub-graph) for each sub-task
- **Replanner node**: After each sub-task, evaluates what was found, adjusts remaining plan if needed

### 2. Implement plan deviation detection & reminder

During executor_node execution, the agent may encounter interesting but off-topic information and chase it. To prevent this:

- State tracks `current_plan_step: int` and `deviation_count: int`
- After each tool call, a lightweight check compares the tool result's topic against the current sub-task's goal
- When deviation is detected, a system message is injected: *"Reminder: you are executing step N: [description]. Focus on this sub-task before moving on."*
- After 3 consecutive deviations, the executor yields control back to the replanner for re-evaluation

Implementation: a conditional edge after `tool_node` that routes through a `deviation_check_node` before returning to `agent_node`. This respects ADR-001's immutability principle — no changes to the core loop, only an outer-layer insertion.

### 3. Define the graph-orchestration vs. model-strategy boundary

This is a key architectural distinction:

| Layer | Responsibility | Examples |
|-------|---------------|----------|
| **Graph orchestration** (code) | Controls *phases* and *flow* | "First plan, then research, then replan, then synthesize" |
| **Model strategy** (LLM) | Controls *tactics* within each phase | "Which keywords to search", "Which source to read deeper", "When enough data has been gathered" |

The graph defines *when* to plan, research, and synthesize. The model decides *how* to do each. This means:

- The graph does NOT hardcode search keywords or analysis dimensions
- The graph DOES enforce that planning happens before research, and synthesis happens after
- The replanner is model-driven (the LLM evaluates progress), not rule-driven
- Deviation detection uses a lightweight heuristic (keyword overlap), not deep semantic analysis — the goal is a nudge, not a hard constraint

### 4. Cap iterations to prevent runaway execution

- **Max sub-tasks per plan**: 7 (configurable)
- **Max replan cycles**: 3 (if the agent replans 3 times, force synthesis with available data)
- **Max tool calls per sub-task**: 10 (prevents single sub-task from consuming all budget)

### Considered Alternatives

#### Option A: Pure ReAct (no planning)

Keep the M1 ReAct loop and rely on the LLM to self-organize.

- **Pro**: Simpler. Fewer nodes. Works for simple questions.
- **Con**: Fails on complex questions (wandering, tunnel-vision). No way to show research progress to the user. No natural point for context compression.
- **Rejected because**: Complex research questions require explicit structure.

#### Option B: Fixed pipeline (plan once, execute all, never replan)

Plan upfront, execute all sub-tasks sequentially, generate report.

- **Pro**: Predictable. Easy to implement.
- **Con**: Cannot adapt when early results change the research direction. Cannot recover when a sub-task returns nothing useful.
- **Rejected because**: Research is inherently exploratory. Rigid plans fail when reality differs from expectations.

#### Option C: Fully autonomous (model decides everything including when to plan)

Give the model a `create_plan` tool and let it decide when to use it.

- **Pro**: Maximum flexibility. Model can plan, abandon plan, replan at will.
- **Con**: Unpredictable behavior. Hard to show progress to users. Difficult to set iteration caps. LLMs often skip planning when given the option.
- **Rejected because**: Violates the graph-orchestration principle — planning is a phase the graph enforces, not an optional tool.

## Consequences

### Positive

- **Research quality**: Sub-task decomposition ensures multiple dimensions of a question are explored, not just the first search result
- **User transparency**: The plan is visible to the user (M2-9: progress callback), giving them confidence the agent is working systematically
- **Cost predictability**: Iteration caps prevent runaway API costs
- **Foundation for M4**: The plan-and-execute structure maps cleanly onto M4's supervisor pattern — the supervisor becomes the planner, specialized agents become executors
- **Deviation resilience**: The reminder mechanism catches tangent-chasing early, before it consumes significant tokens

### Negative

- **Overhead on simple queries**: A question like "What is the capital of France?" doesn't need a 5-step research plan. Need a fast-path for simple questions (detect and skip planning)
- **Replanning cost**: Each replan cycle costs an LLM call. With DeepSeek V3 pricing this is cheap (~¥0.002 per replan), but it adds latency
- **Deviation detection false positives**: Keyword-overlap heuristic may flag legitimate exploratory moves as deviations. The 3-deviation threshold before hard intervention provides buffer

### Neutral

- **State complexity increases**: `ResearchPlan`, `SubTask`, `current_plan_step`, `deviation_count` add state fields. This is managed via Pydantic models (M2-7) and is necessary complexity

## References

- [LangGraph Plan-and-Execute tutorial](https://langchain-ai.github.io/langgraph/tutorials/plan-and-execute/plan-and-execute/) — official LangGraph implementation
- [Claude Code Architecture Memo §4](../memo/claude-code-architecture-memo.md) — Plan Mode and deviation reminder
- [Claude Code Architecture Memo §1](../memo/claude-code-architecture-memo.md) — Harness Engineering: graph orchestrates, model decides
- [ADR-001](ADR-001-langgraph-agent-loop.md) — Agent Loop Immutability: deviation detection is an outer-layer node, not an inner-loop modification
- [Tech Selection Document §8](../planning/tech_selection.md) — Milestone roadmap, M2 scope
