# Dify KB Guide

Operator's guide for the Dify RAG knowledge base used by pbcpb-dify playbooks. Covers KB setup, content upload, MCP tool usage, and query guidance.

## System Overview

pbcpb-dify generates playbooks that query knowledge at runtime via the Dify MCP tool instead of maintaining a local JSON-based KB. Knowledge is gathered as markdown files, uploaded to Dify manually, and queried by Claude Code agents through MCP.

### Architecture

```
Knowledge gathered as .md files (by user)
  │
  ▼ (manual upload)
Dify Dataset (cloud-managed)
  │
  ▼ (MCP connection)
Claude Code ── mcp__dify-cognitive-kb__cognitive-research-kb-dify ──► Agent output
```

### MCP Tool

**Tool name:** `mcp__dify-cognitive-kb__cognitive-research-kb-dify`

**Parameter:** `query` (string) — the question or concept to retrieve

**When to invoke explicitly:**
Add an explicit MCP invocation step in a playbook phase ONLY when:
- (a) the phase requires domain knowledge lookup AND
- (b) the agent has no other deterministic signal to trigger retrieval naturally

**When to rely on natural behavior:**
If the phase context already implies KB retrieval (e.g., the agent is asked to analyze domain-specific requirements), do not add an explicit step — the agent will invoke MCP naturally.

**When in doubt:** Annotate with a comment in the playbook phase description rather than adding a hard invocation step.

## Creating a Dify Dataset

1. Log in to your Dify instance
2. Navigate to **Knowledge** → **Create Knowledge**
3. Set a descriptive dataset name matching your domain
4. Choose text segmentation settings appropriate for your content:
   - Segmentation: Automatic or by heading (`##` for markdown/HTML)
   - Chunk size: 500–1000 tokens recommended
5. Enable **Q&A matching** if your content includes explicit Q&A sections

## Supported File Formats

Dify accepts any of the following formats — use whatever format your knowledge already exists in:

`CSV` `DOCX` `TXT` `HTM` `HTML` `PDF` `MARKDOWN` `MDX` `MD` `XLSX` `XLS` `VTT` `PROPERTIES`

**Recommended format: Markdown (`.md`)** — easiest to write, review, and edit by hand; heading-based segmentation works well for retrieval. Use other formats when the content already exists in that format (e.g., upload a PDF spec directly rather than converting it).

## Gathering Knowledge

Content for the Dify KB follows the conventions defined in `KB-STRUCTURE.md`. The scaffold uses markdown, but any supported format can be uploaded alongside it.

**General conventions:**
- One concept per file — keep files focused
- Descriptive file names: `concept-name.md`, `reference-data.csv`, etc.
- For markdown/HTML: use `##` headings to mark major sections (Dify uses these for segmentation)
- Include concrete examples — they improve retrieval quality
- Keep files under ~2,000 words / ~50 rows for best retrieval performance

**Recommended frontmatter for markdown (optional):**
```markdown
---
topic: <topic-area>
subtopic: <subtopic>
tags: [tag1, tag2]
---
```

## Uploading Content to Dify

1. Prepare your markdown files following `KB-STRUCTURE.md` conventions
2. In Dify, open your dataset → **Add file**
3. Upload one or more `.md` files
4. Wait for indexing to complete (status shows "Available")
5. Test retrieval: use the **Retrieval Test** feature to verify content is accessible

**Batch upload:** Dify supports uploading multiple files at once. Group files by topic area for easier management.

## Querying the KB from Playbooks

When a pbcpb-dify-generated playbook requires KB retrieval, the agent uses:

```
mcp__dify-cognitive-kb__cognitive-research-kb-dify(query="<concept or question>")
```

Playbook phases annotated with `phase_mcp_guidance: explicit` include an explicit retrieval step. Phases annotated `natural` rely on the agent invoking MCP when context warrants it.

### Query Tips

- Use specific queries: `"subtractive synthesis filter cutoff range"` > `"synthesis"`
- If a query returns no results, check that relevant content has been uploaded and indexed in Dify
- If Dify is unavailable, annotate affected phases with `[KB-PENDING]` and proceed using the agent's training knowledge with appropriate caveats

## Maintaining the KB

**Adding content:** Upload new markdown files to the Dify dataset at any time. Content is available for retrieval immediately after indexing.

**Updating content:** Edit the source markdown file and re-upload. Delete the old version in Dify before uploading the updated file.

**Reviewing coverage:** Run a playbook phase that uses explicit MCP retrieval and check whether results are relevant. Gaps indicate missing content in the KB.

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| MCP_NOT_FOUND | Tool not in Claude Code MCP config | Verify Dify MCP server is running and registered |
| Query returns no results | Content not uploaded or not indexed | Upload relevant markdown files to Dify dataset |
| Retrieval quality poor | Files too large or too broad | Split into smaller, focused files; one concept per file |
| [KB-PENDING] annotations in playbook | KB not populated before playbook run | Upload content to Dify, then re-run phase |
| Agent not using MCP naturally | Phase needs explicit annotation | Change `phase_mcp_guidance` from `natural` to `explicit` for that phase |
