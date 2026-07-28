# Bookmark (`bookmark.json`) — Deep Dive

Schema: `https://developer.microsoft.com/json-schemas/fabric/item/report/definition/bookmark/1.0.0/schema.json`

File location: `definition/bookmarks/<bookmark-name>.bookmark.json`

A bookmark captures a snapshot of report state (active page, filters, visual configuration, formatting, cross-highlights) that can be re-applied later.

---

## Top-Level Structure

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/bookmark/1.0.0/schema.json",
  "name": "Bookmark1",
  "displayName": "Sales Overview",
  "options": { ... },
  "explorationState": { ... }
}
```

### Required Fields

| Field | Type | Description |
|---|---|---|
| `$schema` | string | The bookmark 1.0.0 schema URL |
| `name` | string | Unique bookmark identifier across the report |
| `displayName` | string | User-facing bookmark name |
| `explorationState` | object | The captured report state (see below) |

`options` is optional. `additionalProperties: false`.

---

## `options` — BookmarkOptions

Controls how much of the state is applied when the bookmark runs.

| Field | Type | Description |
|---|---|---|
| `applyOnlyToTargetVisuals` | boolean | Apply changes only to the captured selected visuals |
| `targetVisualNames` | string[] | Specific visual names the bookmark applies to |
| `suppressActiveSection` | boolean | Don't switch the active page |
| `suppressData` | boolean | Don't apply data changes (filters/sort) — a "display-only" bookmark |
| `suppressDisplay` | boolean | Don't apply display/formatting changes — a "data-only" bookmark |

---

## `explorationState` — ExplorationState

The core captured state. **Required**: `version`, `activeSection`, `sections`.

```json
"explorationState": {
  "version": "1.0",
  "activeSection": "ReportSection1",
  "filters": { ... },
  "sections": { "ReportSection1": { ... } },
  "objects": { ... },
  "dataSourceVariables": "..."
}
```

| Field | Required | Description |
|---|---|---|
| `version` | **yes** | Bookmark version string |
| `activeSection` | **yes** | Name of the page active when captured |
| `sections` | **yes** | Map of page-name → `SectionState` |
| `filters` | no | Report-level `FiltersState` |
| `objects` | no | Report-level formatting changes (`DataViewObjectDefinitionUpdates`) |
| `dataSourceVariables` | no | DirectQuery data-source variable overrides |

---

## `FiltersState`

Groups filter-container states by how they are identified.

| Field | Description |
|---|---|
| `byName` | Map of name → `FilterContainerState` |
| `byExpr` | Array of `FilterContainerState` identified by expression |
| `byType` | Array identified by filter type |
| `byTransientState` | Array of transient filter containers |

### FilterContainerState (only `name` required)
Same meaning as the filters defined outside a bookmark (see `10_filters.md`).

| Field | Description |
|---|---|
| `name` | Filter name |
| `type` | Filter type string |
| `filter` | A `FilterDefinition` (semantic query) |
| `expression` | A `QueryExpressionContainer` |
| `restatement` | Custom restatement text |
| `howCreated` | Numeric origin `0–7` |
| `precedence` | Filter precedence (const `0` currently) |
| `isTransient` | boolean |
| `cachedDisplayNames` | array |
| `filterExpressionMetadata` | metadata |

---

## `SectionState` (per page in `sections`)

**Required**: `visualContainers`.

| Field | Description |
|---|---|
| `filters` | Page-level `FiltersState` |
| `visualContainers` | Map of visual-name → `VisualContainerState` |
| `visualContainerGroups` | Map of group-name → `VisualContainerGroupState` |

### VisualContainerState
| Field | Description |
|---|---|
| `filters` | Visual-level `FiltersState` |
| `singleVisual` | `SingleVisualConfigState` — visual config |
| `highlight` | `HighlightState` — cross-highlight selections |

### SingleVisualConfigState (key fields)
| Field | Description |
|---|---|
| `visualType` | Name of the visual |
| `autoSelectVisualType` | Can visual type change with data |
| `targetType` / `targetAutoSelectVisualType` | Change visual type (personalize) |
| `objects` | Formatting changes (`DataViewObjectDefinitionUpdates`) |
| `orderBy` | Updated `QuerySortClause[]` ordering |
| `activeProjections` / `projections` | `ProjectionState` — fields used |
| `parameters` | `ParameterStateByRole` — field parameter state |
| `display` | `VisualContainerDisplayState` |
| `expansionStates` | Matrix/hierarchy expansion changes |
| `isDrillDisabled` | Disable drill |

### VisualContainerDisplayState
`mode` (**required**) — `VisualContainerDisplayMode`:

| Value | Meaning |
|---|---|
| `maximize` | Visual shown full screen |
| `spotlight` | Visual spotlighted, others dimmed |
| `elevation` | Visual shown with elevation |
| `hidden` | Visual hidden |

Plus `maximizedOptions.dataTable` (`accessible` / `normal`).

### VisualContainerGroupState
| Field | Description |
|---|---|
| `isHidden` | Is the group hidden |
| `children` | Nested map of child group states |

---

## Formatting Updates — DataViewObjectDefinitionUpdates

Used in `objects` (report and visual level).

| Field | Description |
|---|---|
| `merge` | Object definitions merged with the target (`formattingObjectDefinitions`) |
| `remove` | Array of `DataViewObjectPropertyIdWithSelector` to delete |

`DataViewObjectPropertyIdWithSelector` (all required): `object`, `property`, `selector`.

---

## Minimal Valid Bookmark

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/bookmark/1.0.0/schema.json",
  "name": "Bookmark1",
  "displayName": "Default View",
  "explorationState": {
    "version": "1.0",
    "activeSection": "ReportSection1",
    "sections": {
      "ReportSection1": {
        "visualContainers": {}
      }
    }
  }
}
```

---

## Related Knowledge Base Files

- `13_bookmark_list.md` — `bookmarks.json` (order + groups)
- `10_filters.md` — FilterContainer (same semantics as FilterContainerState)
- `11_data_fields.md` — `FilterDefinition`, `QueryExpressionContainer`, `QuerySortClause`
