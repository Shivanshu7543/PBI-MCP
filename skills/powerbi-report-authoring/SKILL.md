---
name: powerbi-report-authoring
description: >-
  Create and edit Power BI reports through the MCP server (Fabric REST API).
  Use when the user wants to: (1) implement an approved design brief, (2) add
  or edit pages, visuals, filters, slicers, bookmarks, DAX measures, or
  formatting via MCP tools. For open-ended visual design, read
  `powerbi-report-design` first. Triggers: "create Power BI report",
  "add page", "add visual", "add filter", "add bookmark",
  "implement report spec", "bind field to visual".
metadata:
  version: 0.1.0
---

> **CRITICAL NOTES**
> 1. To find the workspace details (including its ID) from workspace name: list all workspaces and, then, use JMESPath filtering
> 2. To find the item details (including its ID) from workspace ID, item type, and item name: list all items of that type in that workspace and, then, use JMESPath filtering

# Power BI Report Authoring Skill (PBIR/PBIP Format)

This skill enables reading, editing, and creation of Power BI report
definition files in the **PBIR (Power BI Report)** format used by **PBIP
(Power BI Project)** files.

## Must/Prefer/Avoid

### MUST

- Use MCP tools (`add_visual`, `add_field_to_visual`, `add_page`, `add_categorical_filter`, `add_dax_measure`, `add_bookmark`) to create and modify all report artifacts.
- Read `powerbi://skills/powerbi-report-authoring/references/{ref}` before specifying visual roles, formatting objects, enum values, or field expressions.
- Always call `list_semantic_models` and `list_semantic_model_columns` before creating a report or binding fields.
- Start from an approved `Design Brief:` from `powerbi://skills/powerbi-report-design` for greenfield builds.
- Verify every MCP tool call by calling the corresponding list tool (`list_pages`, `list_visuals`, `list_filters`, `list_dax_measures`) and confirming the artifact exists with the expected properties. If a tool call returns an error, read the error message, fix the input, and retry. If two retries fail, report the error to the user.
- MCP tool responses and MCP resources are the **source of truth** — do not infer IDs, role names, field names, or schemas from memory.

### PREFER

- Start from an approved `Design Brief:` in `/memories/session/report-spec.md` for greenfield report builds.
- Route visual-design uncertainty to `powerbi-report-design` before writing files.
- Use `list_semantic_model_columns` to discover available tables and fields instead of guessing column or measure names.
- For semantic model changes (adding tables, columns, measures, relationships), use a semantic-model authoring skill or Power BI Modeling MCP — not this skill. This skill is for **report-level** artifacts only.

### AVOID

- Do not guess visual roles, field names, or formatting properties without first reading the relevant `powerbi://skills/powerbi-report-authoring/references/{ref}` resource.
- Do not use only this skill for open-ended design, report planning, or Fabric report item CRUD; pair it with `powerbi-report-design`, `powerbi-report-planning`, or `powerbi-report-management`.

## Quick Start Workflow

0. **Design routing** → for greenfield builds, read `powerbi://skills/powerbi-report-design`
   first; use the `Design Brief:` YAML block from `/memories/session/report-spec.md` (or an
   approved inline `Design Brief:` block in the conversation) as the implementation spec.
1. **Discover workspace** → call `list_semantic_models(workspace_id)` to find
   the semantic model ID, and `list_reports(workspace_id)` for existing reports.
2. **Understand the model** → call `list_semantic_model_columns(workspace_id, semantic_model_id)`
   to enumerate tables, columns, and measures before binding any fields.
3. **Read the relevant resource** → use the [MCP Resources](#mcp-resources) table below
   to pick the reference for the visual type or operation you are about to perform.
   Do not infer roles, property names, or enum values from memory.
4. **Check pitfalls** → read [Anti-Patterns and Pitfalls](#anti-patterns-and-pitfalls)
   before creating visuals, binding fields, or applying formatting.
5. **Build incrementally via MCP tools** → use `create_empty_report`, `add_page`,
   `add_visual`, `add_field_to_visual`, `add_categorical_filter`,
   `add_dax_measure`, and `add_bookmark` to build the report step by step.
   Verify each page has data-bound visuals before moving on.
6. **Verify** → after every logical batch, call `list_pages`, `list_visuals`,
   `list_filters`, and `list_dax_measures` to confirm artifacts exist and have
   correct bindings. If a visual shows 0 fields, re-read the MCP resource and
   retry `add_field_to_visual` with the correct role name. See [Verification](#verification).
7. **Report back** → give the user a concise summary of what was built and any
   issues encountered (major and minor).

## MCP Resources

Read the relevant resource before calling any MCP tool:

| MCP Resource | When to read |
|------|-------------|
| [`authoring.md`](powerbi://skills/powerbi-report-authoring/references/authoring) | Adding/modifying pages, visuals, drillthrough, interactions — includes complete JSON examples |
| [`formatting-overview.md`](powerbi://skills/powerbi-report-authoring/references/formatting-overview) | **Read first for appearance changes** — cascade model, encoding rules, selectors, routing to other formatting files |
| [`formatting.md`](powerbi://skills/powerbi-report-authoring/references/formatting) | Editing `visual.json` appearance — selectors, VCOs, encoding mechanics, background-image routing, cascade |
| [`color-strategy.md`](powerbi://skills/powerbi-report-authoring/references/color-strategy) | Chart data point colors — theme `dataColors` vs `dataPoint.defaultColor` vs `dataPoint.fill` with selectors, cross-visual measure-color consistency |
| [`conditional-formatting.md`](powerbi://skills/powerbi-report-authoring/references/conditional-formatting) | Data-driven formatting — color gradients (FillRule), rules-based, icon sets, data bars, web URL, field value |
| [`page-formatting.md`](powerbi://skills/powerbi-report-authoring/references/page-formatting) | Editing `page.json` appearance — canvas background, wallpaper, page background images |
| [`filter-pane.md`](powerbi://skills/powerbi-report-authoring/references/filter-pane) | Filter pane (`outspacePane`) and filter card (`filterCard`) chrome — Applied/Available state styling, pane width, search/checkbox colors |
| [`theming.md`](powerbi://skills/powerbi-report-authoring/references/theming) | Creating or editing `theme.json` — dataColors, textClasses, visualStyles, style presets, ThemeDataColor reference |
| [`re-theming.md`](powerbi://skills/powerbi-report-authoring/references/re-theming) | **Switching themes on a report with existing visuals** — re-theming workflow (color mapping + bulk sweep), dark mode checklist, dark↔light polarity changes. Pair with `theming.md` when changing colors on a report with per-visual overrides. |
| [`expressions.md`](powerbi://skills/powerbi-report-authoring/references/expressions) | Building field references (Column, Measure, Aggregation, Hierarchy) and sort definitions |
| [`filters.md`](powerbi://skills/powerbi-report-authoring/references/filters) | Adding/modifying filters — includes complete JSON examples |
| [`slicers.md`](powerbi://skills/powerbi-report-authoring/references/slicers) | **Read first** when adding/modifying slicers or slicer selections — agent workflow, JSON templates, selection config |
| [`cartesian.md`](powerbi://skills/powerbi-report-authoring/references/cartesian) | Adding bar, column, line charts — families, roles, query patterns (multi-measure, drill hierarchy, date hierarchy), formatting |
| [`map.md`](powerbi://skills/powerbi-report-authoring/references/map) | Adding map visuals — template, roles, geocoding workflow, handling render failures |
| [`card.md`](powerbi://skills/powerbi-report-authoring/references/card) | Adding or formatting KPI/card visuals — `cardVisual`, id selectors, callout/value sizing, accent bars |
| [`table.md`](powerbi://skills/powerbi-report-authoring/references/table) | Adding or formatting tables/matrices — `tableEx`, `pivotTable`, grow-to-fit columns, row banding |
| [`image.md`](powerbi://skills/powerbi-report-authoring/references/image) | Adding image visuals — local resources, URLs, data-bound images, ImageUrl validation/refusal workflow; also plot area background images for chart visuals |
| [`shape.md`](powerbi://skills/powerbi-report-authoring/references/shape) | Adding shape visuals — containers, dividers, backgrounds, reference-image matching |
| [`textbox.md`](powerbi://skills/powerbi-report-authoring/references/textbox) | Adding static or dynamic textbox visuals — paragraphs, text runs, and bound value expressions |
| [`version-control.md`](powerbi://skills/powerbi-report-authoring/references/version-control) | Git branching, committing, reverting — read when the task involves version control or safe rollback planning |

### Greenfield / Design Handoff

> This skill owns PBIR file mechanics once the work is concrete: page/visual
> JSON, bindings, filters, slicers, themes, formatting, navigation, bookmarks,
> validation, Desktop reloads, and screenshots.
>
> Use `powerbi-report-planning` before authoring for new report/dashboard
> requests, requirements gathering, dependency checks, approval, or end-to-end
> build sequencing. Use `powerbi-report-design` for open-ended visual design,
> redesign/restyle, brand/theme direction, chart selection, or layout critique.
> Return here once there is an approved spec/design brief or a concrete PBIR
> edit to implement — see Quick Start step 0 for how to consume the brief.

### Large Build Execution

For full report/PBIP builds, do **not** delegate complete PBIP generation to a
subagent — the owning agent must keep the design brief, model inventory,
cross-page consistency, validation loop, and Desktop verification coordinated.

When delegation is useful, split by page or visual family. Give each sub-task the relevant brief excerpt, exact fields/measures, and layout contract; collect results centrally and push via MCP tools.

## MCP Tools Available

Use these MCP tools to build reports via the Fabric REST API. MCP tool
responses are the **source of truth** for IDs, names, and current report state —
do not cache or infer these values from memory across calls.

| Tool | Purpose |
|------|---------|
| `create_empty_report` | Create a new blank report bound to a semantic model |
| `list_reports` / `get_report` | List or inspect existing reports |
| `update_report_metadata` | Update report display name and/or description |
| `delete_report` | Permanently delete a report from a workspace |
| `get_report_definition` | Fetch and decode the full PBIR-Legacy definition (all parts) |
| `add_page` / `update_page` / `delete_page` | Manage report pages |
| `list_pages` / `reorder_pages` | Audit and reorder pages |
| `add_visual` / `delete_visual` | Add or remove a visual on a page |
| `list_visuals` | List all visuals on a page with their IDs and field count |
| `update_visual_title` / `update_visual_position` | Update visual display and layout |
| `add_field_to_visual` / `remove_field_from_visual` | Bind or unbind a column/measure to a visual role |
| `list_filters` / `add_categorical_filter` / `remove_filter` | List, add, or remove filters at report or page level |
| `list_dax_measures` / `add_dax_measure` / `update_dax_measure` / `delete_dax_measure` | List, add, update, or delete report-level DAX measures |
| `list_bookmarks` / `add_bookmark` / `delete_bookmark` | List, add, or delete bookmarks |
| `list_semantic_models` | Discover semantic model IDs in a workspace |
| `list_semantic_model_columns` | Enumerate tables, columns, and measures |
| `connect_report_to_semantic_model` | Rebind a report to a different semantic model |


## PBIR File Layout

A PBIP project on disk looks like this:

```text
<Report>.pbip                              # Project manifest
├── <Report>.Report/
│   ├── .platform                          # Fabric metadata (type, logicalId)
│   ├── definition.pbir                    # Report → SemanticModel binding
│   ├── definition/
│   │   ├── version.json                   # Format version (e.g. "2.0.0")
│   │   ├── report.json                    # Report-level: themes, settings, resources
│   │   └── pages/
│   │       ├── pages.json                 # Page order + active page name
│   │       └── <pageId>/
│   │           ├── page.json              # Page: displayName, size, type, filters
│   │           └── visuals/
│   │               └── <visualId>/
│   │                   └── visual.json    # Visual: type, position, query, formatting
│   ├── CustomVisuals/                     # Third-party .pbiviz packages
│   └── StaticResources/
│       ├── SharedResources/BaseThemes/    # Built-in base themes
│       └── RegisteredResources/           # User images, custom theme JSON
└── <Report>.SemanticModel/                # OUT OF SCOPE
```

### Key Files

| File | Purpose | Agent rule |
|------|---------|------------|
| `.platform` | Fabric/PBIP report item metadata | Keep it with the `.Report` folder |
| `definition.pbir` | Report → semantic model binding via `byPath` or `byConnection` | Preserve schema/version unless intentionally migrating |
| `version.json` | PBIR format metadata | Preserve the full scaffolded file, including `$schema` |
| `report.json` | Report-level settings, themes, resources | Edit through references and validate after changes |
| `pages.json` | Page order and active page | Add every new page to `pageOrder`; preserve `activePageName` |
| `page.json` | Page metadata, size, filters | Preserve dimensions unless resizing is approved |
| `visual.json` | Visual type, position, query, formatting | Read `powerbi://skills/powerbi-report-authoring/references/authoring` for role and formatting rules |
| `localSettings.json` | User-local settings | Do not commit or rely on it |

Schema URLs use the prefix `developer.microsoft.com/json-schemas/fabric/item/report/definition/`.
The suffixes are versioned PBIR contracts that Power BI Desktop bumps with most
releases (e.g. `visualContainer/2.9.0`, `page/2.1.0`, `report/3.3.0` at the
time of writing — newer values may appear in any user's PBIP). When editing,
**always preserve the existing `$schema` value**; when adding a new file, copy
the `$schema` URL from an existing file of the same type in the same report.
Do not invent or bump versions on your own.

---

## Visual Type and Formatting Reference

Read the relevant MCP resource **before** specifying visual roles, formatting
properties, field expressions, or filter structures. Do not infer these from memory.

| What you need | Resource to read |
|---|---|
| Visual roles and cardinality | `powerbi://skills/powerbi-report-authoring/references/authoring` |
| Formatting properties and selectors | `powerbi://skills/powerbi-report-authoring/references/formatting` |
| Formatting overview / cascade model | `powerbi://skills/powerbi-report-authoring/references/formatting-overview` |
| Filter JSON structure | `powerbi://skills/powerbi-report-authoring/references/filters` |
| Field expression encoding | `powerbi://skills/powerbi-report-authoring/references/expressions` |
| Bar / column / line charts | `powerbi://skills/powerbi-report-authoring/references/cartesian` |
| Card visuals | `powerbi://skills/powerbi-report-authoring/references/card` |
| Table / matrix visuals | `powerbi://skills/powerbi-report-authoring/references/table` |
| Slicer visuals | `powerbi://skills/powerbi-report-authoring/references/slicers` |
| Map visuals | `powerbi://skills/powerbi-report-authoring/references/map` |


## Visual Capability Guardrails

Use these as pre-edit safety rails. Always confirm exact roles, formatting objects, properties, enum values, and selectors by reading the relevant MCP resource before calling a tool.

### Prefer modern visual types

Never create legacy visual types. If repairing an existing legacy visual, migrate to the modern type and rebuild roles/formatting from the relevant MCP resource.

| Do not create | Use instead |
|---|---|
| `card` | `cardVisual` |
| `multiRowCard` | `cardVisual` — use multi-value `cardVisual` (multiple projections in `Data`) for multiple KPIs |
| `table` | `tableEx` |
| `matrix` | `pivotTable` |
| `map`, `filledMap` | `azureMap` |

### Instance Selectors

Some formatting objects need `{ id: ... }` selectors. Run `formatting
list-objects` and `formatting describe-object`; follow `_selectorHint` and the
dual-entry pattern in `powerbi://skills/powerbi-report-authoring/references/formatting`.

## MCP Build Loop

Follow this loop when building or modifying a report via MCP tools:

```text
┌─────────────────────────────────────────────────────────┐
│  1. Read relevant MCP resource(s) for the operation     │
│  2. Discover IDs   → list_pages / list_visuals          │
│  3. Call MCP tool  → add_visual / add_field_to_visual   │
│  4. Verify result  → list_visuals to confirm the change │
│  5. Handle errors  → fix input and retry (max 2)        │
│  6. Report back    → summarise what was built           │
└─────────────────────────────────────────────────────────┘
```

**Rules:**
- Always call `list_pages` to get the internal page name before any page or visual operation.
- Always call `list_visuals` to get the visual ID before binding fields or updating properties.
- Role names passed to `add_field_to_visual` must match exactly what the MCP resource specifies.
- Set `is_measure=True` for DAX measures and aggregated numeric fields; `is_measure=False` for text, date, or key columns.
- Page scaffolding is not completion — every requested page needs data-bound visuals.

**Error handling:**

| MCP tool error / symptom | Likely cause | Action |
|---|---|---|
| Tool returns HTTP 400 / validation error | Invalid parameter (wrong ID, bad role name, unsupported visual type) | Read the error message, re-read the relevant MCP resource, fix the input, retry once |
| Tool returns HTTP 404 | Workspace, report, page, or visual ID does not exist | Re-run the corresponding `list_*` tool to get the current ID, retry |
| Tool returns HTTP 401 / 403 | Authentication expired or insufficient permissions | Ask the user to verify credentials and workspace access |
| Tool returns HTTP 429 | Rate limit exceeded | Wait briefly, then retry once. If it persists, report to the user |
| Tool succeeds but `list_visuals` shows visual with 0 fields | Wrong role name or `is_measure` flag | Re-read MCP resource for the visual type, verify the exact role name and field type, call `add_field_to_visual` again |
| Tool succeeds but visual does not appear in `list_visuals` | Wrong page name or stale page ID | Re-call `list_pages` to get current page names, retry `add_visual` on the correct page |
| Two retries fail for the same operation | Persistent API or configuration issue | Stop, report the exact error to the user, do not continue building on a broken artifact |


## Verification

After building or modifying report artifacts via MCP tools, verify the result.
Do not report completion until all checks pass.

### Presence checks
- Call `list_pages` — confirm all expected pages exist and `pageOrder` is correct.
- Call `list_visuals` on each page — confirm every requested visual is present.
- Call `list_filters` — confirm filters are registered at the correct scope (report / page / visual).
- Call `list_dax_measures` — confirm all created measures appear.
- Call `list_bookmarks` — confirm bookmarks if any were created.

### Binding and correctness checks
- For each visual, verify the field count returned by `list_visuals` is > 0. A visual with 0 fields means `add_field_to_visual` either was not called or used a wrong role name.
- If a visual shows 0 fields: re-read the MCP resource for that visual type, verify the exact role name (e.g., `"Data"` not `"Fields"` for `cardVisual`), and call `add_field_to_visual` again.
- Confirm `is_measure` was set correctly: `True` for DAX measures and aggregated numeric fields, `False` for text, date, or key columns. Incorrect `is_measure` produces silent binding failures.
- For filters, verify the filter values match what was requested — `list_filters` returns the current filter state.

### Failure gate
- If any check fails after two fix attempts, stop and report the specific failure to the user.
- Do not proceed to the next page or visual group until the current batch passes verification.


---

## Anti-Patterns and Pitfalls

| Pitfall | Consequence | Fix |
|---------|-------------|-----|
| Using `"Entity"` inside filter `Where` conditions | Filter silently fails | Use `"Source"` with the alias from `From` |
| Omitting `nativeQueryRef` | Visual calculations may break | Always include `nativeQueryRef` |
| Reusing visual/filter names | Unpredictable behavior | Generate unique IDs |
| Setting `visualType` to invalid string | Visual renders as error box | Run `powerbi://skills/powerbi-report-authoring/references/authoring` |
| Wrong role name for visual type | Field is ignored; visual blank | Match role names from `powerbi://skills/powerbi-report-authoring/references/authoring` |
| Mixing `Column` and `Measure` types | Query fails; visual error | Columns use `Column`, measures use `Measure` |
| Forgetting to add page to `pages.json` | Page invisible | Add to `pageOrder` array |
| Booleans without correct format | Wrong type | `"true"` / `"false"` (no suffix, unquoted in Value) |
| Numbers without type suffix | Type mismatch | `D` for decimals, `L` for integers |
| Editing `$schema` version | PBI Desktop may reject | Preserve existing version |
| Stringified JSON in `paragraphs` | Textbox shows nothing | `paragraphs` is a native JSON array |
| Using textbox as a thin line/divider | Renders ~24px tall regardless of `height` | Use a `shape` visual (rectangle) instead — shapes respect small dimensions |
| `visualContainerObjects` as sibling of `visual` | Schema validation error in PBI Desktop | Must be **inside** `visual` object, as sibling of `objects` |
| Using `tableEx` with dimension columns and measures all in `Values` | Headers render but no data rows even when DAX confirms data exists | Use `pivotTable`; put dimensions in `Rows` and measures in `Values` |
| Using PowerShell `ConvertTo-Json` to edit visual JSON | Property reordering, nesting depth truncation (`-Depth` default is 2) | Use Node.js for JSON manipulation, or always pass `-Depth 20` and verify structure |
| Using regex or string replacement to modify JSON files | Corrupts nesting structure — properties end up inside sibling values, braces misalign | Read file → `JSON.parse` → modify object → `JSON.stringify` → write back. Or use the `edit` tool with exact old/new string matching |
| `dataPoint.fill` without a selector on single-series charts | Bars/columns invisible despite data in tooltips | Use `dataPoint.defaultColor` for a base color without a selector; `fill` requires a `metadata` selector |
| Using `dataPoint.defaultColor` on multi-series charts | All series/categories get the same color — no visual differentiation | Use theme `dataColors` for consistent palette across visuals, or `dataPoint.fill` with `metadata` selectors for per-series overrides — see [color-strategy.md § Color Strategy Quick Reference](powerbi://skills/powerbi-report-authoring/references/color-strategy#color-strategy-quick-reference) |
| Clustered bar/column chart colors collapse into one legend color | The visual has a Series role but all bars and legend markers share the same hue | Use per-series `dataPoint.fill` selectors or a theme `dataColors` palette; do not use `defaultColor` on clustered charts |
| Relying on theme `dataColors` alone for cross-visual measure consistency | Same measure gets different colors on different visuals (index-based assignment varies with projection order) | Maintain a measure→color mapping and apply explicit `dataPoint.fill`/`defaultColor` per visual — see [color-strategy.md § Cross-Visual Measure-Color Consistency](powerbi://skills/powerbi-report-authoring/references/color-strategy#pattern-cross-visual-measure-color-consistency) |
| Using `ThemeDataColor` for explicit per-measure `dataPoint.fill` with metadata selectors | Colors silently resolve to white or black instead of expected palette color | Use `Literal` hex values for explicit color assignments with metadata selectors — `ThemeDataColor` is unreliable in this context |
| Choosing bar/series colors without checking background contrast | Bars or lines invisible against page/card background (e.g., white bars on white canvas) | Always pick saturated, mid-to-dark hues that contrast with the page and VCO background colors |
| `show` property on page-level `background` | Schema error — page `background` only supports `color`, `image`, `transparency` | Only VCO `background` (on visuals) has `show`; page background is always visible |
| Copying property names from doc examples without verifying | Warnings or silent failures — property names vary by visual type | Always run `powerbi://skills/powerbi-report-authoring/references/formatting` for exact property names |
| Guessing which object a property belongs to | Wasted calls checking wrong objects one by one | Run `powerbi://skills/powerbi-report-authoring/references/formatting` to grep across all objects at once |
| Formatting property has no effect (no error) | Setting `show: false` on cardVisual outline without an id selector — validates but renders unchanged | Check `powerbi://skills/powerbi-report-authoring/references/formatting` for `_selectorHint`; use the dual-entry pattern (static + id selector entries) |
| Using `cardCalloutArea` on a single-value card | Properties validate but have no visible effect — `cardCalloutArea` only renders on multi-value cards (2+ measures in Data) | Use `outline`/`accentBar`/`fillCustom` with `{ id: "default" }` selector for single-value cards. For multi-value cards, `cardCalloutArea` controls per-callout tile styling — see [card.md § Multi-Value Formatting](powerbi://skills/powerbi-report-authoring/references/card#multi-value-formatting) |
| Using `"Fields"` as the `queryState` role for `cardVisual` | Cards render empty — PBI Desktop cannot resolve the binding. Validator reports `Unknown role "Fields"` and `Required role "Data" missing` | `cardVisual`'s only data role is `"Data"`. `"Fields"` is the legacy `card` visual's role name — never carry it over. Always verify role names with `powerbi://skills/powerbi-report-authoring/references/card` — see [card.md § Single-Value Template](powerbi://skills/powerbi-report-authoring/references/card#single-value-template) |
| Creating separate single-value `cardVisual` instances for multiple related KPIs | Wastes canvas space and misuses the visual type — `cardVisual` natively supports multiple projections in one tile | Default to one multi-value `cardVisual` with all measures as `Data` projections when ≥2 related KPIs are requested. Only use separate cards when per-card styling differences are required — see [card.md § When to Consolidate vs. Keep Separate](powerbi://skills/powerbi-report-authoring/references/card#when-to-consolidate-vs-keep-separate) |
| Adding multiple fields to button slicer Values or Label roles | Slicer breaks or shows unexpected results — each role accepts only 1 field | Put one field in Values, one in Label; additional fields go to Tooltips |
| Looking at `filterConfig` on other visuals to understand slicer selections | Slicer selections live **only** inside the slicer's own `visual.json` via `expansionStates` + `objects.general.filter`. Always read `powerbi://skills/powerbi-report-authoring/references/slicers` first when modifying slicers |
| Creating an image visual without prompting for the source type | Wrong visual structure — URL vs local file vs data field each have different schemas and expression types | Always ask the user for the image source (local file / URL / data field) before creating the visual — see [image.md § Source Types Overview](powerbi://skills/powerbi-report-authoring/references/image#source-types-overview) |
| Creating a data-bound image visual with a field that lacks `dataCategory: ImageUrl` | Visual renders blank or error | **Warn the user first** — the visual will render blank without `dataCategory: ImageUrl`. Present alternatives (other ImageUrl fields, local file, URL) and confirm before creating — see [image.md § Select from data](powerbi://skills/powerbi-report-authoring/references/image#3-select-from-data) |
| Placing background image on page canvas instead of visual plot area | User asks for "background image" alongside a visual (e.g., "column chart with background image") but image is placed on `page.json → objects.background` instead of `visual.objects.plotArea` | When a background image is requested in the context of a specific visual, default to `plotArea.image`. Only use page-level `background.image` when the user explicitly says "page background" / "canvas background" or no visual context exists — see [image.md § Plot Area Background Image](powerbi://skills/powerbi-report-authoring/references/image#plot-area-background-image-plotareaimage) |
| Creating a `multiRowCard` visual | Legacy multi-row card — deprecated; the MCP verification steps warns with `PBIR_VISUAL_TYPE_DEPRECATED`. Often triggered by user phrases like "multi-card", "cards for each metric", or "card per measure" | Always use `cardVisual`. For multiple KPIs, use a single multi-value `cardVisual` with all measures as projections in the `Data` role — see [card.md](powerbi://skills/powerbi-report-authoring/references/card#multi-value-template) |
| Using `map` or `filledMap` instead of `azureMap` for map visuals | Legacy Bing Maps visuals — deprecated and must not be created; the MCP verification steps warns with `PBIR_VISUAL_TYPE_DEPRECATED` | Always use `azureMap` — see [map.md](powerbi://skills/powerbi-report-authoring/references/map). If the map fails to render or geocode, debug the fields, try alternative geographic columns/coordinates, or ask the user — do **not** silently substitute a non-map visual without consulting the user first |
| Creating `tableEx`/`pivotTable` without `columnAdjustment: growToFit` | Columns shrink-wrap to content, leaving unused whitespace | Always set `columnHeaders.columnAdjustment` to `growToFit` and `autoSizeColumnWidth` to `true` — see [table.md](powerbi://skills/powerbi-report-authoring/references/table#default-rule--grow-to-fit) |
| Custom table/matrix row colors with no effect (white background) | Default style preset overrides `objects`-level `backColorPrimary`/`backColorSecondary` | Set `stylePreset` VCO to `'None'` on every `tableEx`/`pivotTable` with custom colors — see [table.md § Style Presets](powerbi://skills/powerbi-report-authoring/references/table#style-presets-for-tables) |
| Table cells white despite dark VCO background | `visualContainerObjects.background` only controls outer container — table cells paint on top | Set dark colors in `objects.values.backColorPrimary/Secondary` and `objects.columnHeaders.backColor`, not in VCO — see [re-theming.md § Dark Mode Checklist](powerbi://skills/powerbi-report-authoring/references/re-theming#dark-mode-authoring-checklist) |
| Dark theme applied but cards/tables/slicers still white | Dark mode triggers every formatting trap simultaneously | Follow the full [re-theming.md § Dark Mode Authoring Checklist](powerbi://skills/powerbi-report-authoring/references/re-theming#dark-mode-authoring-checklist) — covers stylePreset, fillCustom+id selector, objects vs VCO, and contrast audit |
| Placing `sortDefinition` inside `visual` or at root of `visual.json` | Schema validation error; sort silently ignored — chart falls back to alphabetical | `sortDefinition` is a property of **`query`** — use `visual.query.sortDefinition`. Supported since `visualConfiguration/2.2.0` |
| Container shape fill doesn't match reference | Text invisible or wrong background color | Match the fill color and transparency to the reference image. If the page background already provides the color, skip the shape entirely. If the shape must be invisible, verify text color still contrasts with the page canvas — see [shape.md § Container Shapes](powerbi://skills/powerbi-report-authoring/references/shape#container-shapes) |
| Shape text invisible after re-theme | Shape `text` object has no explicit `fontColor` — text inherits theme foreground, but when `fill` is a light color (e.g., white pill/button) on a light page canvas, inherited dark foreground may not render or the fill blends with canvas making text vanish | Always set explicit `fontColor` on shape `text` objects (in the `{ selector: { id: "default" } }` entry). During re-theming, audit all shapes with `text.show: true` — bulk hex-replacement misses shapes that need a *new* `fontColor` property added |
| Enabling `logAxisScale` on data with zero or negative values | PBI Desktop silently falls back to linear scale with a warning — log of zero/negative is undefined | **Warn the user before applying.** Use `ask_user` to present alternatives (filter negatives, switch measure, use `labelDisplayUnits`). Apply `logAxisScale: true` only after the user resolves negative values or confirms all bound values are positive — see [cartesian.md § Log Scale](powerbi://skills/powerbi-report-authoring/references/cartesian#log-scale-logaxisscale) |
| Changing theme without sweeping inline overrides | Old colors remain on shapes, page backgrounds, nav buttons, textboxes — theme-only change has no effect on hardcoded `Literal` hex values at Priority 2 in the cascade | When the report has per-visual color overrides, follow [re-theming.md § Re-theming Workflow](powerbi://skills/powerbi-report-authoring/references/re-theming#re-theming-an-existing-report) Steps 0–3: build a color mapping, update theme JSON, then bulk-sweep `definition/` files for old hex values before reload |
| Changing only `dataColors` in theme without sweeping | Shapes, accent bars, nav button borders retain old accent colors — they use hardcoded Literal hex from the old `dataColors` array, not `ThemeDataColor` references | Sweep ALL old `dataColors[N]` hex values across `definition/` files. Even same-polarity "just change the accent/data colors" requests need the full sweep — shapes and nav elements commonly hardcode `dataColors[0]` as accent fills/outlines. |

## References

All visual, formatting, field, and filter details are available as MCP resources under `powerbi://skills/powerbi-report-authoring/references/{ref}`. Read `powerbi://skills/list` for the full index.
