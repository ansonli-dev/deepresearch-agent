---
name: new-til
description: Create a Today I Learned note in docs/til/ capturing a specific insight from the current development session
---

# Create New TIL Note

Create a short Today I Learned note capturing a specific insight or technique discovered during development.

## Steps

1. Check `docs/til/` for existing TIL notes
2. Ask the user what they learned (if not already provided as $ARGUMENTS)
3. Derive a short slug from the topic
4. Create the TIL file at `docs/til/<YYYY-MM-DD>-<slug>.md` using this template:

```markdown
# TIL: <Title>

**Date:** <YYYY-MM-DD>
**Milestone:** <current milestone, e.g., M1>
**Tags:** <comma-separated tags, e.g., langgraph, async, tool-calling>

## What I Learned

<1-3 paragraphs describing the insight>

## Example

<Code snippet or concrete example demonstrating the learning>

## References

- <Links to docs, Stack Overflow, or source code>
```

5. Create the `docs/til/` directory if it doesn't exist
6. Report the file path to the user
