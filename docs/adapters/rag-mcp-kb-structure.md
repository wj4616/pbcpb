# KB-STRUCTURE.md

Knowledge base scaffold for the Dify dataset. Use this as a guide for gathering and organizing domain knowledge before uploading to Dify.

**Supported upload formats:** CSV, DOCX, TXT, HTM, HTML, PDF, MARKDOWN, MDX, MD, XLSX, XLS, VTT, PROPERTIES — upload whatever format your content already exists in. This scaffold uses markdown as the default, but any supported format is accepted.

## How to Use This File

1. For each topic area below, gather content covering that domain (in any supported format)
2. Follow the file naming and structure conventions in each section
3. Upload the completed files to your Dify dataset
4. See `DIFY-KB-GUIDE.md` for upload instructions and format guidance

**File naming convention:** `concept-name.md` (lowercase, hyphens, no spaces)
**Content convention:** One concept per file, `##` headings for major sections, concrete examples

---

## Topic Area: [TODO — Domain Topic 1]

**What belongs here:** [Describe what knowledge goes in this area]
**Example file names:** `concept-a.md`, `concept-b.md`

### Subtopic: [TODO]

> Placeholder — replace with a markdown file covering this subtopic
> 
> Example content structure:
> ```markdown
> ## Summary
> [1-2 sentence overview]
> 
> ## Detail
> [Full explanation]
> 
> ## Examples
> [Concrete examples]
> ```

---

## Topic Area: [TODO — Domain Topic 2]

**What belongs here:** [Describe what knowledge goes in this area]
**Example file names:** `concept-c.md`, `concept-d.md`

### Subtopic: [TODO]

> Placeholder — replace with a markdown file covering this subtopic

---

## Topic Area: [TODO — Domain Topic 3]

**What belongs here:** [Describe what knowledge goes in this area]

### Subtopic: [TODO]

> Placeholder — replace with a markdown file covering this subtopic

---

## Upload Instructions

1. Create markdown files for each topic area above
2. Name files descriptively: `filter-cutoff-ranges.md`, not `notes.md`
3. Keep each file focused on one concept
4. Open Dify → your dataset → **Add file**
5. Upload files (batch upload supported)
6. Wait for indexing status to show **Available**
7. Test with **Retrieval Test** before running playbooks

## Quality Checklist

Before uploading each file, verify:
- [ ] File covers exactly one concept (not a dump of notes)
- [ ] `##` headings mark major sections (improves Dify segmentation)
- [ ] At least one concrete example included
- [ ] File is under ~2,000 words
- [ ] File name describes the concept
