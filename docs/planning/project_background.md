# DeepResearch Agent — Project Background

v1.0 · March 2026

---

## 1. Motivation

### 1.1 Why this project

AI agent technology is rapidly becoming a core competency for software engineers. The ability to design, build, and deploy autonomous systems that can reason, plan, use tools, and collaborate is no longer a niche skill — it is increasingly expected in backend engineering, platform engineering, and product development roles.

This project exists to bridge the gap between theoretical understanding of agent concepts and practical, hands-on ability to build production-grade agent systems. Rather than following tutorials in isolation, the goal is to construct a single, cohesive application that exercises every major agent capability, resulting in both deep learning and a tangible, deployable artifact.

### 1.2 Why a Deep Research Agent

Among the many possible agent applications (coding assistants, workflow automation, personal productivity), a deep research agent was chosen because it naturally requires all four core agent capabilities:

| Capability | What it means | How research demands it |
|---|---|---|
| Tool Use | Agent invokes external APIs and tools | Web search, page fetching, file writing, API calls |
| Planning & Reasoning | Decompose goals into steps, adapt on the fly | Break a vague question into research sub-tasks, replan when results are thin |
| Memory & RAG | Remember past interactions, retrieve relevant knowledge | Build on previous research, avoid redundant searches, incremental learning |
| Multi-Agent | Multiple specialized agents collaborate on a task | Planner, Researcher, Analyst, Writer each have distinct skills and tools |

This is not a toy demo. A deep research agent is a genuinely useful tool — it can be used for market analysis, technical research, competitive intelligence, literature review, and more. The project is designed to be both a learning vehicle and a product that delivers real value.

---

## 2. Project Goals

### 2.1 Primary goals

- **Learn agent fundamentals deeply:** Gain hands-on understanding of tool calling, ReAct loops, planning patterns, RAG pipelines, and multi-agent orchestration — not just by reading about them, but by implementing them from the ground up.
- **Build a production-grade system:** The end result should not be a Jupyter notebook or a demo script. It should be a well-engineered, tested, documented, containerized, and deployable application with a real UI.
- **Learn the modern Python AI ecosystem:** Gain practical experience with LangGraph, LangChain, FastAPI, uv, Ruff, and the broader Python toolchain as a Java engineer expanding into the AI/ML space.
- **Create a portfolio piece:** A publicly visible GitHub project with clean code, comprehensive docs, and a live demo that demonstrates competence in agent engineering.

### 2.2 Secondary goals

- **Learn React/Next.js:** Build a modern frontend from scratch, gaining experience with the dominant web framework ecosystem.
- **Practice architecture documentation:** Use ADRs (Architecture Decision Records) and TILs (Today I Learned) to document design decisions and learning throughout the project.
- **Explore model economics:** Gain practical understanding of LLM API pricing, cost optimization strategies (caching, batching, model tiering), and the trade-offs between different providers.

---

## 3. Non-Goals & Scope Boundaries

Equally important as what the project will do is what it will not do. These boundaries keep the project focused and completable.

- **Not a general-purpose agent framework:** This is a specific application (deep research), not a library or framework for building arbitrary agents. The code may be reusable, but that is a side effect, not a goal.
- **Not a commercial product:** There is no need for multi-tenancy, billing, rate limiting, or SOC 2 compliance. These are valid production concerns but out of scope for a learning project.
- **Not an LLM training project:** The project uses existing LLMs via API. Fine-tuning, RLHF, or model training are out of scope.
- **Not mobile:** The web UI targets desktop browsers. Responsive design is nice-to-have, not a requirement.
- **Not real-time collaborative:** Single-user design. No WebSocket-based multi-user collaboration, no shared sessions.

---

## 4. Target User Profile

While primarily a learning project, the agent is designed to be useful to a real audience:

### 4.1 Primary user: The developer (you)

A Java engineer with strong backend and architecture skills, expanding into the Python/AI agent space. Uses Claude Code daily. Familiar with Docker, CI/CD, cloud-native patterns. New to Python ecosystem tooling, LLM APIs, React/Next.js.

### 4.2 Secondary users: Open-source community

Developers who want to understand how agent systems work by reading well-documented source code. The project should serve as a reference implementation — not the simplest possible agent, but a thoughtfully architected one that shows how the pieces fit together.

### 4.3 End users of the deployed application

Anyone who needs to research a topic in depth: analysts, students, writers, engineers. They provide a question, the agent searches, analyzes, and produces a structured report with citations.

---

## 5. Reference & Learning Projects

The following open-source projects serve as references and learning resources for architecture, patterns, and implementation techniques.

| Project | Architecture | What We Learn From It |
|---|---|---|
| [Open Deep Research](https://github.com/langchain-ai/open-deep-research) | LangGraph, supervisor + parallel researchers | Reference architecture for LangGraph agent design. Uses Tavily, no vector DB. Model-agnostic config pattern. |
| [GPT Researcher](https://github.com/assafelovic/gpt-researcher) | LangGraph, multi-agent, Next.js frontend | Full-stack agent app pattern. Parallelism + citation tracking. Next.js + FastAPI integration. |
| [DeepSearcher](https://github.com/zilliztech/deep-searcher) | Milvus vector DB, private data focus | When and why to use a vector DB: private document corpus scenarios. |
| [RAGFlow](https://github.com/infiniflow/ragflow) | Elasticsearch, enterprise RAG engine | Enterprise-grade document processing pipeline design. Different scope (platform vs. agent) but instructive for RAG patterns. |
| [Local Deep Research](https://github.com/LearningCircuitsAI/local-deep-research) | Ollama, SearXNG, fully local | Privacy-first agent design. Demonstrates local LLM + self-hosted search is viable. |

### 5.1 What makes this project different (as a learning vehicle)

- **Pedagogical clarity:** Every design decision is documented with an ADR. The codebase is designed to be read and understood, not just run.
- **Progressive complexity:** Six clear milestones that build on each other. A newcomer can start at M1 and learn incrementally.
- **Model-agnostic by default:** DeepSeek V3 as the accessible default (~¥10–20/month), with other providers as drop-in alternatives. Lowers the barrier to entry.
- **Full-stack completeness:** From CLI to Web UI to cloud deployment. Most reference projects stop at the agent; this one goes all the way to a deployable product.

---

## 6. Constraints & Assumptions

### 6.1 Time constraints

The developer is working on this part-time: 3–4 evenings per week, 3–4 hours per session (~12 hours/week). The project plan is calibrated to this pace, with ~16 weeks total. Each milestone is designed to be completable in 1–4 weeks.

### 6.2 Budget constraints

LLM API costs should stay within a reasonable learning budget. DeepSeek V3 (¥1/¥2 per MTok) as the default model keeps monthly costs to ~¥10–20 during development. Tavily free tier (1,000 queries/month) covers early milestones. Total project cost estimated at ¥200–400 over 4 months.

### 6.3 Technical assumptions

- Developer has strong Java/backend engineering skills, transferable to Python
- Developer is experienced with Docker, CI/CD, and cloud-native patterns
- Developer uses Claude Code (Max x20 subscription) as an AI-assisted development tool
- Python ecosystem (uv, Ruff, FastAPI) is new but conceptually familiar from Java equivalents
- React/Next.js is entirely new territory; M5 schedule reflects this
- All development happens on a personal machine (macOS/Linux); no dedicated server until deployment

### 6.4 Dependencies on external services

| Service | Required from | Free tier | Risk |
|---|---|---|---|
| DeepSeek API | P0 | Pay-as-you-go (¥50 已充值) | Low — model-agnostic design, provider switching is a config change |
| Tavily Search API | P0 | 1,000/month | Low — Brave as backup |
| LangSmith | P0 | 5,000 traces/month | Low — optional, not blocking |
| GitHub | P0 | Free for public repos | Negligible |
| Vercel | M5 | Generous free tier | Negligible |
| Railway | M5 | $5 trial credits | Low — any VPS works |

---

## 7. Success Criteria

The project is considered successful when the following are all true:

### 7.1 Functional success

- A user can input a complex research question and receive a multi-section report with citations within **5 minutes**
- The agent demonstrates visible planning (sub-task decomposition), execution (search + analysis), and synthesis (structured report)
- Multiple specialized agents collaborate through a supervisor, visible in LangSmith traces
- The agent can recall and build on previous research sessions
- The system runs via CLI, HTTP API, and Web UI
- Report quality: **≥ 5 cited sources** per report, structured sections (intro, findings, conclusion)

### 7.2 Engineering success

- CI pipeline passes: lint (Ruff), type-check (mypy), tests (pytest) — **CI completes in < 2 minutes**
- Test coverage: **≥ 70%** line coverage for `src/` (measured by pytest-cov)
- `docker compose up` starts the complete system from scratch — **healthy within 30 seconds**
- Frontend deployed on Vercel, backend on Railway, both accessible via public URL
- README provides clear setup instructions; a new developer can get running in **< 5 minutes**
- **4+ ADRs** document key architectural decisions with context, rationale, and consequences
- Zero critical/high severity issues from `ruff check` and `mypy --strict`
- API response time: **< 500ms** for non-streaming endpoints (health, status, history)

### 7.3 Learning success

- Comfortable building LangGraph agents: can explain state graphs, nodes, edges, checkpointing
- Understands LLM tool calling: can implement and debug function calling across providers
- Can design multi-agent systems: supervisor pattern, agent handoff, parallel execution
- Familiar with RAG fundamentals: embedding, vector storage, retrieval, augmentation
- Can build and deploy a Next.js + React application with Tailwind CSS
- Practical understanding of LLM cost optimization: caching, batching, model tiering
- **Documented in TIL notes:** ≥ 1 TIL per milestone, capturing non-obvious learnings

---

## 8. Risks & Mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| DeepSeek tool calling unreliable in practice | Medium | Model-agnostic design. Switch to other providers with a config change. Document findings in TIL. |
| Scope creep: adding features beyond plan | High | Linear project management with defined milestones. If it's not in a milestone, it goes to backlog. Max 2 WIP. |
| Time investment drops off mid-project | Medium | Each milestone is independently shippable. Even M1 alone is a useful project. No wasted work. |
| LangGraph API changes / breaking updates | Low | Pin versions in uv.lock. LangGraph is production-stable with strong backwards compatibility. |
| React/Next.js learning curve steeper than expected | Medium | M5 has the most generous timeline (3–4 weeks). Claude Code helps with boilerplate. Community templates available as starting points. |
| API costs exceed budget | Low | DeepSeek default keeps costs to ~¥15/month. Set hard spending limits in API consoles. Batch API for tests. |

---

## 9. Related Documents

| Document | Path | Description |
|---|---|---|
| Technical Selection Document | [tech_selection.md](./tech_selection.md) | Detailed rationale for every technology choice: LLM provider, search API, vector store, dev tooling, frontend, infrastructure. |
| Project Plan (Linear Issues) | [../tools/linear_issues.json](../tools/linear_issues.json) | Linear-ready issue map: 6 milestones, ~75 issues with labels, priorities, estimates, and acceptance criteria. |
| ADR Template | [../adr/template.md](../adr/template.md) | MADR template for Architecture Decision Records. ADRs are created during each milestone. |

---

## 10. Glossary

| Term | Definition |
|---|---|
| Agent | An LLM-powered system that can perceive its environment, make decisions, and take actions autonomously to achieve a goal. |
| ReAct | Reasoning + Acting. A pattern where the LLM alternates between thinking about what to do and executing tools, observing results before deciding the next step. |
| Tool Calling | The ability of an LLM to invoke external functions, APIs, or tools in a structured way (also called function calling). |
| RAG | Retrieval-Augmented Generation. A pattern where the LLM's response is grounded in retrieved documents or data, reducing hallucination. |
| Embedding | A numerical vector representation of text that captures semantic meaning, enabling similarity search. |
| State Graph | LangGraph's core abstraction. A directed graph where nodes are functions and edges define the flow of execution and data. |
| Checkpointing | Saving the state of a LangGraph execution at each step, enabling pause/resume, debugging, and conversation persistence. |
| Supervisor Pattern | A multi-agent architecture where a central agent (supervisor) delegates tasks to specialized worker agents. |
| SSE | Server-Sent Events. A protocol for streaming data from server to client, used for real-time agent response streaming. |
| ADR | Architecture Decision Record. A short document capturing a significant design decision, its context, and consequences. |
| TIL | Today I Learned. A brief note capturing a specific insight or technique discovered during development. |
