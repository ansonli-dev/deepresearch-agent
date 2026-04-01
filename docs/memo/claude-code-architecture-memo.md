# Claude Code 架构学习备忘录

> **用途**：为 Deep Research Agent 项目提取可借鉴的架构模式
> **日期**：2026-04-01
> **当前阶段**：M1（ReAct Agent + 工具调用 + CLI）

---

## 一、核心理念：Harness Engineering

Claude Code 的架构哲学可以总结为一句话：**模型就是 Agent，代码只是 Harness（骨架/支架）。**

所谓 Harness，就是给模型提供的"手、眼睛和工作台"——工具、知识、上下文管理和权限边界。工程师的工作不是编写智能，而是构建模型运行的世界。

```
Harness = Tools + Knowledge + Observation + Action Interfaces + Permissions
```

**对 Deep Research Agent 的启示**：不要试图用代码逻辑硬编排研究流程（先搜这个、再分析那个），而是给模型足够的工具和上下文，让模型自己决定研究策略。LangGraph 的 state graph 应该是一个灵活的骨架，而非死板的 pipeline。

> **相关 ADR**：[ADR-001](../adr/ADR-001-langgraph-agent-loop.md)（LangGraph 选型 + Agent Loop 不可变性）、[ADR-002](../adr/ADR-002-planning-strategy.md)（graph orchestration vs. model strategy 边界）

---

## 二、Agent Loop：一切的基础

Claude Code 的核心是一个极简循环：

```
用户消息 → LLM → 返回响应
                    |
          stop_reason == "tool_use"?
         /                          \
       是                            否
        |                             |
  执行工具、追加结果               返回文本给用户
  回到循环起点 ←───────────
```

**关键原则**：循环本身永远不变。所有新功能（规划、子代理、压缩）都是在循环外层叠加机制，而非修改循环内部。

**M1 落地**：在 LangGraph 中，这对应 `agent_node → tool_node → agent_node` 的基本循环。确保这个循环从 Day 1 就是干净的——所有扩展通过 state 和新 node 实现，不要在循环内部塞 if-else。

> **相关 ADR**：[ADR-001](../adr/ADR-001-langgraph-agent-loop.md)（Agent Loop 不可变性原则）

---

## 三、工具系统：统一注册，按需调度

Claude Code 有 40+ 个工具，每个工具实现为独立模块，定义三要素：

| 要素 | 说明 | Deep Research Agent 对应 |
|------|------|------------------------|
| Input Schema | Zod schema 定义输入参数 | Pydantic model 定义 tool 输入 |
| Permission Model | 该工具是否需要用户确认 | 区分"安全操作"和"副作用操作" |
| Execution Logic | `call()` 方法执行具体逻辑 | LangGraph tool function |

**工具调度模式**：不是把所有工具一次性塞进 prompt，而是根据当前任务上下文动态选择工具子集。

**M1 落地**：
- 定义统一的 Tool 接口（name, description, input_schema, execute）
- M1 工具：`web_search`（Tavily）、`web_fetch`（httpx + trafilatura）
- M3 新增：`save_to_chromadb`（语义检索存储）
- 后续扩展时只需注册新 handler，循环不变

> **相关 ADR**：[ADR-001](../adr/ADR-001-langgraph-agent-loop.md)（工具注册模式）、[ADR-004](../adr/ADR-004-multi-agent-coordination.md)（M4 per-role 工具子集）

---

## 四、规划模式（TodoWrite / Plan Mode）

Claude Code 的经验是：**没有计划的 Agent 会漫无目的地游荡。**

实现方式：让 LLM 先输出一个 todo list（任务计划），然后逐条执行，每完成一条更新状态。还有一个"提醒机制"——如果 Agent 偏离计划，系统会在 prompt 中注入提醒。

```
用户输入研究问题
  → Agent 输出研究计划（搜索哪些关键词、分析哪些维度、输出什么格式）
  → 用户确认（或 Agent 自动执行）
  → 逐步执行，标记完成状态
  → 偏离时提醒回到计划
```

**M2 落地**：
- 在 LangGraph state 中增加 `research_plan: list[dict]` 字段
- Planning sub-graph：第一个节点让 LLM 分解研究问题为子任务
- 后续节点按计划执行，每步更新 plan 状态
- 最终节点基于所有收集到的信息生成结构化研究报告（引言、发现、结论 + 引用）

> **相关 ADR**：[ADR-002](../adr/ADR-002-planning-strategy.md)（规划策略、重规划、偏离检测）

---

## 五、子代理（Subagent）模式

核心原则：**大任务拆小，每个子任务获得干净的上下文。**

Claude Code 的做法：
- 主 Agent 通过 Task 工具生成子代理
- 每个子代理拥有**独立的 messages[]**——不继承主对话的全部历史
- 子代理完成后，结果汇总回主 Agent
- 子代理可以在独立的 git worktree 中工作，避免互相干扰

**为什么需要独立上下文？**  
如果让一个 Agent 在同一个对话中又搜索又分析又写报告，上下文会很快被污染。子代理的独立 messages[] 保证每个子任务看到的上下文都是干净的、只包含它需要的信息。

**M4 落地**：
- Supervisor 模式：中央 supervisor agent 分配任务给 Researcher、Analyst、Writer
- LangGraph subgraph 天然支持子代理模式
- 设计 `spawn_subagent(task, context_subset)` 函数
- 明确定义主代理和子代理之间的数据传递接口（传什么、不传什么）
- 支持并行研究执行（多个 researcher 同时工作）
- 考虑失败回退策略

> **相关 ADR**：[ADR-004](../adr/ADR-004-multi-agent-coordination.md)（Supervisor 模式、上下文隔离、工具路由）

---

## 六、知识按需加载（Skill Loading）

Claude Code 的做法是：**需要时加载知识，而非一开始全塞进 system prompt。**

具体实现：把领域知识（SKILL.md 文件）作为工具结果注入，而非写死在系统提示里。Agent 知道有哪些知识可用，需要时主动拉取。

```
❌ 错误做法：把所有 RAG 结果塞进 system prompt
✅ 正确做法：Agent 先规划，再通过工具按需检索
```

**M3 落地**：
- ChromaDB 检索结果作为 tool_result 返回，不是预加载
- system prompt 只包含角色定义和可用工具列表
- 让模型决定何时需要检索更多信息
- 嵌入模型：`text-embedding-3-small`（OpenAI）或本地 `all-MiniLM-L6-v2`

> **相关 ADR**：[ADR-003](../adr/ADR-003-memory-architecture.md)（知识按需加载、ChromaDB 作为 tool_result）

---

## 七、上下文压缩（Context Compaction）

随着对话增长，context window 会被填满。Claude Code 的三层压缩策略：

| 层级 | 触发条件 | 做法 |
|------|---------|------|
| 第一层 | 上下文达到阈值 | 对早期对话做 rolling summary |
| 第二层 | summary 也太长 | 对 summary 再次压缩 |
| 第三层 | 极端情况 | 只保留关键决策和当前任务状态 |

压缩时保留的"记忆"包括：关键决策、用户偏好、当前任务目标。丢弃的是：中间过程的详细工具输出、已完成任务的具体步骤。

**M2 落地**：
- 在 LangGraph state 中设计 `context_summary: str` 字段
- 当搜索结果累积过多时，先让 LLM 总结已有发现，再继续搜索
- 最终报告生成节点接收的是压缩后的研究摘要，而非原始搜索结果全文

> **相关 ADR**：[ADR-005](../adr/ADR-005-context-compression.md)（三层压缩策略、token budget 管理）

---

## 八、任务系统（Task Persistence）

Claude Code 将大目标拆解为小任务，持久化到磁盘，支持依赖关系图：

```
Task A (完成) → Task B (进行中) → Task D (待开始)
                                ↗
Task C (完成) ────────────────
```

每个任务有 ID、状态、依赖列表。跨 session 也能恢复。

**M3 落地**：
- LangGraph Checkpointer + SQLite：会话持久化，支持中断后恢复
- 对于长时间运行的深度研究，将研究进度持久化
- 用 JSON 文件记录：已搜索的关键词、已分析的来源、待深入的方向
- 支持中断后恢复研究

> **相关 ADR**：[ADR-003](../adr/ADR-003-memory-architecture.md)（两套记忆系统、保留策略、Checkpointer）

---

## 九、权限治理模型

Claude Code 的四级权限：

| 模式 | 说明 | Research Agent 对应 |
|------|------|-------------------|
| Default | 每次工具调用都需确认 | 用户确认每次搜索（不推荐） |
| Plan | 先看计划再批准 | 用户确认研究计划后自动执行 ✅ |
| Auto | 全自动 | 完全自主研究 |
| Bypass | 跳过所有检查 | 开发/测试阶段 |

**M2 落地**：推荐 Plan 模式——用户确认研究计划后，Agent 自动执行所有搜索和分析步骤。

---

## 十、成本追踪与可观测性

Claude Code 内置 OpenTelemetry 追踪和 token 消耗统计。

**M1 落地**（基础版，随里程碑逐步增强）：
- 在每个 LangGraph 节点上加 callback，记录：
  - LLM 调用次数和 token 消耗
  - 搜索 API 调用次数
  - 每个节点的执行时间
- LangSmith tracing 从 M1 开始集成
- 用简单的 JSON log 或 SQLite 存储，方便后续分析哪个环节最费 token

---

## 参考仓库

| 仓库 | 用途 | 地址 |
|------|------|------|
| 架构拆解教程（强烈推荐） | 12 个 session 逐步讲解 harness 机制 | https://github.com/shareAI-lab/learn-claude-code |
| 源码镜像 | TypeScript 原始代码（学习用） | https://github.com/instructkr/claude-code |
| Python 重写 | clean-room Python 实现 | https://github.com/instructkr/clawd-code |
| DeepWiki 架构分析 | 自动生成的架构文档 | https://deepwiki.com/instructkr/claude-code |
| Claude Code 使用教程 | 实践指南和模板 | https://github.com/luongnv89/claude-howto |

---

## 学习优先级（按项目阶段）

### P0 —— 工程基础搭建
1. ✅ Python 生态工具链（uv, Ruff, mypy, pytest）
2. ✅ LLM API 和搜索 API 验证

### M1（当前）—— ReAct Agent + 工具调用 + CLI
3. Agent Loop 基本循环
4. 工具统一注册模式
5. 成本追踪 callback（LangSmith 基础版）

### M2 —— 规划推理 + HTTP API
6. 研究计划模式（Plan Mode / Planning sub-graph）
7. 上下文压缩基础版
8. 权限治理模型

### M3 —— 记忆与 RAG
9. 知识按需加载（ChromaDB）
10. 任务持久化（Checkpointer）
11. 上下文压缩进阶版

### M4 —— 多代理协作
12. 子代理编排（Supervisor 模式）
13. 异步邮箱通信（team protocol）
14. 任务自动领取（autonomous agents）
15. Worktree 隔离执行

### M5 —— Web UI + 部署
16. SSE 流式传输到前端
17. 研究历史 UI（基于 M3 记忆）
