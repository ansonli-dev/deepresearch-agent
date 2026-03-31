---
name: new-adr
description: Create a new Architecture Decision Record in docs/adr/ using MADR template with auto-numbering
---

# Create New ADR

Create a new Architecture Decision Record following the MADR (Markdown Any Decision Records) template.

## Steps

1. Check `docs/adr/` for existing ADRs and determine the next number (format: `ADR-NNN`)
2. Ask the user for:
   - **Title**: Brief description of the decision
   - **Context**: What is the issue that motivates this decision?
3. Create the ADR file at `docs/adr/adr-NNN-<slug>.md` using this template:

```markdown
# ADR-NNN: <Title>

**Status:** Proposed
**Date:** <today's date YYYY-MM-DD>
**Deciders:** Yuan Li

## Context

<What is the issue that we're seeing that motivates this decision or change?>

## Decision

<What is the change that we're proposing and/or doing?>

## Consequences

### Positive
- <list positive consequences>

### Negative
- <list negative consequences>

### Neutral
- <list neutral consequences>

## Alternatives Considered

### <Alternative 1>
- Pro: ...
- Con: ...

## Related
- <Links to related ADRs, issues, or documents>
```

4. Create the `docs/adr/` directory if it doesn't exist
5. Report the file path to the user
