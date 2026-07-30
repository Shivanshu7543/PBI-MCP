---
name: powerbi-report-planning
description: >-
  Build a guided requirements-to-implementation workflow for new Power BI
  reports and dashboards on the PowerBI MCP server (Fabric REST API based —
  no local PBIP/Desktop/TMDL access). Use when the user wants to: (1) plan
  then implement a report, (2) define audience, scope, page plan, design
  direction, dependencies, and delivery target, (3) create a locked report
  spec with approval before calling any MCP authoring tool. For direct edits
  to an existing report, use `powerbi-report-authoring`. For design-only
  critique or redesign, use `powerbi-report-design`. Triggers: "build me a
  dashboard", "create a new report", "plan then implement", "define and build
  Power BI report", "walk me through creating a report".
metadata:
  version: 0.2.0
---

# Power BI Report Planning Skill

This skill orchestrates the full lifecycle for a new Power BI report built
through this MCP server:

**Define -> Inspect -> Spec -> Approve -> Build -> Verify**

It is intentionally broader than a pure requirements-gathering flow: it captures
the report spec **and** continues into implementation after the user approves.
This server has no local/draft mode — every report created with `create_empty_report`
exists live in the target Fabric workspace immediately, so there is no separate
"publish" phase once building starts.

## MCP Server Resources

This skill is one of three skill resources exposed by this server. Read the
others as needed instead of duplicating their guidance here:

- `powerbi://skills/list` — index of all skill resource URIs
- `powerbi://skills/powerbi-report-planning` — this skill (Rounds 0-4, spec, approval, build sequence)
- `powerbi://skills/powerbi-report-design` — tone, archetypes, chart selection, layout, color, typography, Design Brief contract
- `powerbi://skills/powerbi-report-authoring` — available MCP tools, visual types, field-role rules, formatting, anti-patterns
- `powerbi://visuals/list` and `powerbi://visuals/{visual_type}` — valid visual type names and per-visual schemas

## Must/Prefer/Avoid

### MUST

- Use this skill for broad report creation workflows that need requirements, dependency checks, approval, and build sequencing.
- Ask focused clarification questions one at a time and stop after the required decision is clear.
- Lock `_brief/report-spec.md` and get approval before calling any authoring tool.
- Route design decisions through the `powerbi://skills/powerbi-report-design` resource and file/tool mechanics through the `powerbi://skills/powerbi-report-authoring` resource.

### PREFER

- Infer obvious answers from the prompt, the inspected semantic model, existing reports in the workspace, or earlier rounds instead of re-asking.
- Inspect the semantic model with `list_semantic_model_columns` before finalizing page scope or visual recommendations.
- Confirm the target Fabric workspace before Round 4, since building immediately creates a live report there.

### AVOID

- Do not use this skill for a small, surgical edit to an existing report (use `powerbi-report-authoring` directly).
- Do not build before the user approves the locked report spec.
- Do not duplicate detailed visual-design or authoring-tool guidance that belongs to the companion skill resources.
- Do not reference `powerbi-modeling-mcp`, `powerbi-report-management`, local PBIP/PBIR files, TMDL, Power BI Desktop, or Node.js generators — none of those are available on this server.

## Examples of When to Use

Use this skill when the user wants to create a new Power BI report and needs
both:

1. A guided requirements workflow.
2. A path to implementation after approval.

Examples:

- "Let's create a new Power BI report from this semantic model."
- "Help me define and then build a Power BI report."
- "Use the report playbook to start a new report."
- "Create a reusable workflow for new Power BI reports."

Do **not** use this skill for a small edit to an existing report page. For
direct report-authoring tasks, use the `powerbi-report-authoring` resource. For
visual critique or greenfield design guidance **without the full guided workflow**
(a one-off "redesign this" or "what should this look like?"), use the
`powerbi-report-design` resource directly. This skill *uses* the design skill
during Rounds 3–4 — it does not replace it.

## Required Operating Rules

1. **Ask one question at a time.** Use `ask_user` for each clarification.
2. **Run 3-5 clarification rounds maximum.** Each round may have one primary
   question and, only if absolutely necessary, one follow-up.
3. **Inspect the semantic model before locking the spec.** Call `list_semantic_models`
   to discover candidates and `list_semantic_model_columns` to enumerate tables,
   columns, and data types before finalizing scope or field bindings.
4. **Check dependencies explicitly.** Do not assume a semantic model already
   contains every needed measure/column — this server can only add
   report-level DAX measures via `add_dax_measure`; it cannot create or edit
   model-level TMDL measures, calculated columns, or relationships.
5. **Produce one locked `_brief/report-spec.md` before building.**
6. **Ask for approval before implementation.** Do not call any authoring tool
   (`create_empty_report`, `add_page`, `add_visual`, etc.) until the user
   explicitly approves.
7. **When approved, build end-to-end with MCP tools.** Create/rebind the
   report, add pages and visuals, bind fields, add filters and report-level
   measures, then verify with the `list_*` tools.
8. **There is no local draft mode.** Once `create_empty_report` runs, the
   report exists live in the target Fabric workspace — confirm the workspace
   and delivery target before building, not after.
9. **Do not re-ask known answers.** If the original prompt, inspected model, or
   a prior round already provides audience, page count, delivery target, scope,
   or design direction, capture it in working notes and move on. Ask only for
   genuine ambiguity or risky tradeoffs.

## Dependency Checklist

Before implementation, capture this status:

| Dependency | Purpose | Required When |
|---|---|---|
| Fabric workspace access (bearer token via `DefaultAzureCredential`) | Call any MCP tool against the Fabric REST API | Always |
| An existing semantic model in the workspace | Bind the new/updated report to data | Always — discover with `list_semantic_models` |
| `list_semantic_model_columns` result | Know exact table/column names for `add_field_to_visual` | Always before authoring |
| `powerbi-report-design` resource | Tone, archetype routing, Design Brief contract | Always for page/visual design |
| `powerbi-report-authoring` resource | Tool inventory, visual roles, formatting rules | Always before calling authoring tools |
| `add_dax_measure` | Report-level DAX measures only (reportExtensions.json) | Only if the model is missing a measure and a report-level measure is acceptable |

If a dependency is unavailable (e.g. no semantic model exists yet, or a needed
measure requires a model-level change this server cannot make), continue
planning and mark the affected phase as blocked/manual. Do not pretend it is
available.

## Round Structure

### Round 0 — Setup and Dependency Check

Goal: identify the semantic model, workspace, and report target.

Ask only what cannot be inspected automatically:

> What semantic model or dataset should this report use?

Recommended choices should be concrete if candidates are discoverable. Call
`list_semantic_models(workspace_id)` to enumerate existing Fabric semantic
models in scope, then present them as options and mark the best match as
recommended. Example:

- `<DiscoveredSemanticModelName>` (Recommended)
- Another existing Fabric semantic model in the workspace
- A different workspace/model the user names

Then inspect/check:

- Call `list_reports(workspace_id)` to see if a matching report already exists (update vs. create new).
- Call `list_semantic_model_columns(workspace_id, semantic_model_id)` to confirm the model is reachable and has a usable schema.
- Whether the user wants to create a new report or update/extend an existing one.
- Whether the target workspace_id is already known or needs to be asked for.

Output working notes:

```markdown
Dependency status:
- Workspace:
- Semantic model:
- Existing report (if any):
- Schema reachable via list_semantic_model_columns:
- Create new vs. update existing:
```

### Round 1 — Audience and Job

Goal: understand who the report is for and what decision/job it supports.

If both audience and job-to-be-done are already clear from the prompt, summarize
the inferred answer instead of asking. Otherwise ask for the missing piece(s),
one at a time.

Ask when audience is unclear:

> Who is this report primarily for?

Recommended choices:

1. Executives / leadership — concise KPIs, trends, risks, decisions
2. Analysts — exploration, drilldowns, comparisons, tables
3. Operators — monitoring, exceptions, status, action queues
4. External audience — polished story, guided narrative, minimal slicers
5. Enthusiasts / fans — magazine-style narrative, rich visuals, rankings

Then ask only if the job-to-be-done is still unclear:

> What should the report help them do?

Recommended choices:

1. Understand the overall story
2. Track performance
3. Find outliers or opportunities
4. Compare entities or segments
5. Explore individual records/profiles
6. Prepare for a recurring business review

Capture:

```markdown
Audience:
Primary purpose:
Tone:
Success criteria:
```

### Round 2 — Model Inventory and Scope

Goal: inspect the model and define the first-build scope boundary without
re-asking for scope the user already gave.

Call `list_semantic_model_columns(workspace_id, semantic_model_id)` to enumerate
tables and columns (via DAX `INFO.COLUMNS()`). This is read-only schema
discovery — this server cannot create or edit model-level measures, calculated
columns, or relationships. If a required measure does not exist in the model,
note it as a model-owner dependency; the only measure this skill can add itself
is a report-level DAX measure via `add_dax_measure`.

Summarize:

```markdown
Facts:
- table, grain, keys, useful measures

Dimensions:
- date/time, geography, entity, category, owner, status, segment

Existing measures:
- core available measures

Likely missing model work:
- measures
- calculated columns
- relationship fixes
- sort columns
- helper fields for slicers/search

Risks:
- nulls/sparsity
- inactive relationships
- high-cardinality slicers
- fields that will not filter as expected
```

After inspection, infer the first-build scope from the original request and
prior answers. Do not ask a standalone scope question if the user already gave a
page count, report type, or content boundary (for example, "build a 4 page
dashboard"). Instead, summarize the boundary in working notes:

```markdown
First-build scope:
- <focused first build / standard report / operational app / narrative report>
- inferred from: <user prompt | prior answer | model shape>
- included now:
- deferred:
```

Ask a scope question only when the boundary is unclear, too broad, or risky. If
asking, present tailored choices from the inspected model rather than generic
first-build options. Example:

> The model supports sales, products, geography, discounts, and profitability.
> For this first build, should we keep it focused on executive performance, or
> include a deeper product/customer exploration too?

### Round 3 — Narrative and Page Plan

Goal: turn the model and scope into page architecture.

Invoke or explicitly consult `powerbi-report-design` for page-level archetype
routing and composition guidance. The design skill owns visual routing; do not
duplicate its routing table here. Use the data shape from Round 2 to surface
2-3 report shape options for user sign-off.

The five archetypes the design skill ships are: **Executive Summary**,
**Operational Monitor**, **Analytical Canvas**, **Narrative Story**,
**Comparative Benchmark**. Use the design skill's archetype and composition
guidance for layout variants, multi-archetype reports, and cross-page variant
rotation.

Ask only after applying the inferred first-build scope from Round 2:

> Which report shape should we use?

Present 2–3 named compositions (e.g., *Executive landing + Analytical
exploration + Comparative ranking* for a multi-domain ask, or *Single
executive landing* for a focused ask). Recommend one based on Rounds 1–2
and mark it `(Recommended)`.

Draft page list in the answer after the user chooses:

```markdown
Proposed pages:
1. <Page> — archetype — purpose — core visuals — fields/measures
2. <Page> — archetype — purpose — core visuals — fields/measures
<repeat for each approved page>
```

Capture slicers and interactions:

- Global slicers
- Page-specific slicers
- Search/prefix slicers for high-cardinality dimensions
- Drillthrough/profile pages
- Bookmarks/navigation if needed

### Round 4 — Design Identity, Accessibility, and Delivery

Goal: lock the design identity, accessibility baseline, and delivery target.

Invoke or explicitly consult `powerbi-report-design` for design identity and
theme direction. Design identity (tone + signature) is owned by the design skill
— do not invent a parallel vocabulary here. Use the design skill's identity
guidance to pick a tone+signature combination, then surface it to the user.

Ask:

> What should this report feel like?

Present 2–3 concrete identity options adapted to the audience and domain from
Rounds 1–2. Each option names a report feel and the one signature visual move
it implies. Recommend one and mark it `(Recommended)`.

If the user has brand guidelines, make one option brand-forward rather than
picking a generic tone.

Then ask delivery only if unclear:

> Where should the finished report end up?

Recommended choices:

1. Create a new report in an existing Fabric workspace (`create_empty_report`)
2. Update/extend an existing Fabric report in place (`add_page`/`add_visual` on a resolved `report_id`)
3. Rebind an existing report to a different semantic model (`connect_report_to_semantic_model`)

Note: this server has no local-only mode — whichever option is chosen creates
or mutates the report live in the target Fabric workspace as soon as building
starts.

Design defaults (these come from the design skill's gotchas + base theme;
applied automatically unless the user overrides):

- Use accessible contrast (WCAG AA minimum on every text/background pair).
- Avoid red-on-red and low-contrast palettes.
- Prefer Azure Map over deprecated map/filledMap visuals.
- Add alt text to every chart.
- Use searchable dropdown slicers for high-cardinality fields.
- Use tile/list slicers only for short categorical fields.
- Place detailed tables near the bottom of the page.
- Keep report interactions predictable and consistent.

## Design Contract Gate

Before producing `_brief/report-spec.md` for approval, get a canonical
`Design Brief:` YAML block from `powerbi-report-design`. The planner may provide
requirements, model inventory, page goals, and user constraints to the design
skill, but the planner must not author a competing detailed design skeleton.

The canonical design block must include:

- `generated_by: powerbi-report-design`
- `contract_version`
- one `pages[]` entry for every page in the page plan
- `pages[].layout_contract.canvas`
- `pages[].layout_contract.grid.regions`
- `pages[].layout_contract.placements`
- `pages[].layout_contract.space_audit`
- one `page_title` textbox placement with non-empty title text per page
- slicer placements in a top-right `filters` region or a justified filter rail
- no bare single-value `cardVisual` occupying the largest/dominant hero region
  unless the design marks it as a composite KPI treatment with context and
  rationale
- no unresolved placeholders, ellipses, or prose-only wireframes

If the block is missing these items, stop and revise the design contract before
asking for approval or invoking `powerbi-report-authoring`.

## Locked Report Spec Output

After Rounds 0-4, produce one file and save it under `./_brief/` in the
current working directory:

- `./_brief/report-spec.md` — the single source of truth for approval and
  implementation handoff.

`report-spec.md` has two layers:

1. **Markdown sections** for user approval and readable context.
2. A fenced `yaml` block containing the exact `Design Brief:` returned by
   `powerbi-report-design` — the canonical implementation contract that
   `powerbi-report-authoring` consumes.

If Markdown prose and the embedded YAML disagree, fix `report-spec.md` before
building. Do not ask the authoring agent to choose between conflicting
instructions.

If the agent runtime exposes a dedicated session/scratch folder (for example a
`session-state` path injected by the harness), you may also write a copy there
for user visibility, but the canonical implementation handoff file remains
`./_brief/report-spec.md` unless every later authoring step carries the alternate
absolute path explicitly.

### `report-spec.md` template

The user-approval doc and agent handoff contract. The Markdown captures
sign-off granularity; the embedded YAML captures exact implementation intent.

````markdown
# Report Spec

## Report identity
- Report name:
- Semantic model:
- Audience:
- Primary purpose:
- Delivery target:

## User decisions and constraints
- Scope:
- Page count:
- Interactivity:
- Design direction:
- Delivery target (create new / update existing / rebind):
- Workspace / semantic model IDs:
- Model edit limitations: report-level DAX measures only via `add_dax_measure`
- Accessibility:
- Data caveats:

## Narrative
- Core story:
- Audience promise:
- Key questions answered:

## Design identity (from `powerbi-report-design` Step 1)
- Tone: <named entry from tone-catalog, e.g. "Editorial Newsroom">
- Signature: <one defining move, e.g. "tabular numerals + display serif headlines">
- Brownfield delta (if applicable): <current_tone → target_tone>

## Page plan (archetypes from `powerbi-report-design` Step 3)
1. Page name
   - Archetype:                      <Executive Summary | Analytical Canvas | …>
   - Layout variant (A/B/C):         <plus one-sentence variant_rationale>
   - Purpose:
   - Visuals:
   - Fields/measures:
   - Slicers/interactions:

## Design system summary
- Theme name + base palette (1–2 lines):
- Color semantics (which measure → which color, 1–2 lines):
- Typography pairing (display + body):
- Layout pattern (grid + gutter + density):
- Accessibility commitments:

## Model requirements
- Existing measures (from `list_semantic_model_columns` / known model schema):
- New report-level DAX measures (`add_dax_measure` — reportExtensions.json only):
- Model-level gaps out of scope for this server (calculated columns, relationships, TMDL measures — flag for the model owner):

## Canonical design contract

Paste the exact fenced `yaml` block produced by `powerbi-report-design` here.
Do not rewrite it from planner memory and do not replace its mechanical
`layout_contract` with a freeform ASCII wireframe.

The YAML block is authoritative for implementation. `powerbi-report-authoring`
must implement this block; surrounding prose is context and conflict detection.

## Implementation notes

- Model gaps (report-level measure vs. needs model owner):
- Report authoring plan (tool call order):
- Verification (`list_*` tool checks):
- Risks:
````

### Required acceptance checks before approval

Before writing the approval question, verify the spec meets all of the
following. If any check fails, fix `report-spec.md` and the embedded
`Design Brief:` block before asking for approval.

- The block begins with `Design Brief:`.
- It includes `generated_by: powerbi-report-design` and `contract_version`.
- Every Markdown page has a matching `pages[]` entry.
- Every page has `layout_contract.canvas`, `layout_contract.grid.regions`, and
  `layout_contract.placements`.
- Every page has `layout_contract.space_audit` with empty `unplaced_regions`
  and an explicit empty-space/balance rationale.
- Every page has a `page_title` textbox placement with non-empty title text.
- Slicers are in a top-right `filters` region or a justified filter rail; no
  data visual starts under a slicer/header-band region.
- No bare single-value `cardVisual` is the largest/dominant hero region unless
  the YAML explicitly describes a composite KPI treatment with context.
- The approved YAML has no ellipses (`...`), unresolved placeholders, or
  pages/visuals promised in Markdown but omitted from the YAML.

## Approval Gate

After writing `report-spec.md`, ask exactly one approval question:

> Approve this report spec so I can start building?

Recommended choices:

1. Approve — start building
2. Revise audience/purpose
3. Revise scope/page plan
4. Revise design/delivery

Do not call any authoring tool until the user approves.

## Implementation After Approval

When the user approves, execute this sequence using this server's MCP tools
(read `powerbi://skills/powerbi-report-authoring` first for exact role names,
visual types, and formatting properties):

1. Re-read the approved canonical report spec (normally `_brief/report-spec.md`,
   or the explicitly carried alternate absolute path) and extract the embedded
   `Design Brief:` YAML block. Verify it has `generated_by:
   powerbi-report-design`, `contract_version`, one populated `layout_contract`
   per page, and `space_audit` per page before authoring. For greenfield, verify
   the canvas is FHD (`1920 x 1080`) unless the user chose another size, and
   verify the largest/dominant region is not a bare single-value `cardVisual`.
2. Mark the first implementation todo as in progress.
3. Resolve `workspace_id` and `semantic_model_id` (via `list_semantic_models`
   if not already captured in Round 0).
4. Call `list_semantic_model_columns(workspace_id, semantic_model_id)` to
   confirm the exact table/column names before binding any field.
5. Create or resolve the target report:
   - New report: `create_empty_report(workspace_id, display_name, semantic_model_id)`.
   - Existing report: `list_reports`/`get_report` to resolve `report_id`; call
     `connect_report_to_semantic_model` only if the spec calls for rebinding.
6. For each page in the approved page plan: call `add_page`, then `list_pages`
   to capture the internal `page_name` before adding visuals to it.
7. For each visual on a page: call `add_visual`, then `list_visuals` to capture
   `visual_id`, then `add_field_to_visual` for every role specified in the
   Design Brief's `layout_contract.placements`, using role names exactly as
   named in the authoring reference.
8. Apply filters/slicers from the Design Brief with `add_categorical_filter`.
9. Add report-level DAX measures with `add_dax_measure` only for measures the
   model is missing; anything requiring a model-level measure, calculated
   column, or relationship change is out of scope for this server — record it
   in Implementation notes for the model owner instead of attempting it.
10. Add bookmarks with `add_bookmark` if the page plan calls for saved
    views/navigation.
11. Apply formatting/positioning per the `layout_contract.placements` with
    `update_visual_title` and `update_visual_position`.
12. Verify: call `list_pages`, `list_visuals`, `list_filters`,
    `list_dax_measures`, and `list_bookmarks` and confirm counts and bindings
    match the approved spec; call `get_report_definition` to confirm the
    definition parses and every page has data-bound visuals.
13. Report back the `workspace_id`/`report_id` and a summary. There is no
    separate publish step — the report already exists live in the target
    Fabric workspace.

## Report Creation & Update Rules

This server has no separate publishing skill or step — `create_empty_report`
and `connect_report_to_semantic_model` act directly against the live Fabric
workspace. Respect these rules when calling them:

- Resolve `workspace_id`, `report_id`, and `semantic_model_id` dynamically via
  `list_semantic_models`/`list_reports`/`get_report`; never hardcode IDs.
- Confirm with the user before calling `delete_report`, `delete_page`, or
  `delete_visual` — these mutate a live Fabric report and are not easily
  reversible.
- Use `connect_report_to_semantic_model` only when the approved spec calls for
  rebinding to a different model; it changes the report's data source.
- Use `update_report_metadata` to rename/re-describe a report; it does not
  change the model binding.
- Include every field/role required by the Design Brief when calling
  `add_field_to_visual` for a visual — a partially bound visual is not done.

## Validation Standards

A report is not complete until:

- `get_report_definition` returns a definition where all JSON parses.
- The report is bound to the expected semantic model (verify via
  `get_report`/`connect_report_to_semantic_model` result).
- `list_pages` returns the expected page count and names.
- `list_visuals` returns the expected visual count per page, and every visual
  has fields bound (no scaffolded/empty visuals).
- `list_filters` matches the slicers/filters in the approved spec.
- `list_dax_measures` includes every report-level measure the spec called for.
- `list_bookmarks` includes every bookmark the spec called for, if any.

## Anti-Patterns and Pitfalls

- Always call `list_pages`/`list_visuals` to get the current `page_name`/
  `visual_id` before mutating — do not reuse IDs from an earlier step once
  another `add_page`/`add_visual` call has run.
- Role names passed to `add_field_to_visual` must match the authoring skill's
  role tables exactly (e.g. `Category`, `Y`, `Series`, `Values`).
- Set `is_measure=True` for DAX measures and aggregated numeric fields;
  `is_measure=False` for text, date, or key columns.
- `add_dax_measure` only creates report-level measures (reportExtensions.json)
  — it cannot add model-level TMDL measures, calculated columns, or fix
  relationships. Do not claim a model-level gap is resolved when only a
  report-level workaround was added.
- Treat `delete_report`, `delete_page`, and `delete_visual` as destructive;
  confirm before calling them.
- Every page must end up with data-bound visuals — scaffolding a page without
  bound fields is not "done".
