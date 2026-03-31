---
name: run-agent
description: Run the research agent with a test query and verify the LangSmith trace for correctness
disable-model-invocation: true
---

# Run Agent & Verify Trace

Run the deep research agent with a test query and verify the execution is correct.

## Steps

1. **Run the agent** with the provided query (or a default test query):

```bash
# CLI mode
uv run python -m src.cli "<query or default: 'What are the latest advances in AI agents?'>"

# Or API mode (if FastAPI is running)
curl -X POST http://localhost:8000/research \
  -H "Content-Type: application/json" \
  -d '{"query": "<query>"}'
```

2. **Check the output** for:
   - [ ] Report was generated without errors
   - [ ] Report contains multiple sections
   - [ ] Citations are present and properly formatted
   - [ ] No hallucinated URLs or references

3. **Verify LangSmith trace** (if LANGSMITH_API_KEY is set):
   - Open the trace URL printed in the output
   - Verify the agent graph executed expected nodes
   - Check tool calls were made (web_search, web_fetch)
   - Verify no unnecessary LLM calls or loops

4. **Report results** to the user:
   - Execution time
   - Number of search queries made
   - Number of sources cited
   - Any errors or warnings
   - LangSmith trace URL (if available)
