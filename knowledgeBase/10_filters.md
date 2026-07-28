# Filter Configuration (`filterConfig`) — Deep Dive

Schema: `https://developer.microsoft.com/json-schemas/fabric/item/report/definition/filterConfiguration/1.3.0/schema.json`

Used by: `report.json` (report-level), `page.json` (page-level), and each `visual.json` (visual-level) via their `filterConfig` property.

Defines the set of filters applied at a given scope.

---

## Top-Level Structure

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/filterConfiguration/1.3.0/schema.json",
  "filters": [ ... ],
  "filterSortOrder": "Ascending"
}
```

| Field | Required | Type | Description |
|---|---|---|---|
| `$schema` | **yes** | string | The filterConfiguration 1.3.0 schema URL |
| `filters` | no | FilterContainer[] | The filter definitions |
| `filterSortOrder` | no | enum | `Ascending` / `Descending` / `Custom` |

> When embedded inside another file (page/visual), `$schema` may be omitted — it's only required when `filterConfig` is a standalone file.

### `filterSortOrder`
- `Ascending` — sort by field display name ascending
- `Descending` — sort by field display name descending
- `Custom` — sort by each filter's `ordinal`; filters without `ordinal` go last, then by display name

---

## FilterContainer (each entry in `filters`)

Only `name` is required.

```json
{
  "name": "Filter_Category",
  "displayName": "Category",
  "ordinal": 0,
  "field": { "Column": { "Expression": { "SourceRef": { "Entity": "Product" } }, "Property": "Category" } },
  "type": "Categorical",
  "filter": { ... },
  "restatement": "...",
  "howCreated": "User",
  "isHiddenInViewMode": false,
  "isLockedInViewMode": false,
  "objects": { ... }
}
```

| Field | Required | Description |
|---|---|---|
| `name` | **yes** | Unique filter name across the whole report definition |
| `displayName` | no | Alternate label; defaults to field display name |
| `ordinal` | no | Sort order (only when `filterSortOrder` = `Custom`) |
| `field` | no | The data field filtered — a `QueryExpressionContainer` (Column/Measure/etc.) |
| `type` | no | Filter type — see below |
| `filter` | no | The actual filter body — a `FilterDefinition` (see semantic query KB) |
| `restatement` | no | Custom text; only for `Passthrough` type (others auto-generate) |
| `howCreated` | no | How the filter originated — see below |
| `isHiddenInViewMode` | no | Hide filter when viewing |
| `isLockedInViewMode` | no | Prevent value change when viewing |
| `objects` | no | Filter card formatting |

---

## `type` — Filter Types

| Value | Meaning |
|---|---|
| `Categorical` | Basic list of selected values (In filter) |
| `Range` | Numeric between/greater/less |
| `Advanced` | And/Or of conditions (contains, starts with, comparisons) |
| `Passthrough` | Opaque filter with a manual `restatement` |
| `TopN` | Top/Bottom N by a measure |
| `Include` | Include selected data points |
| `Exclude` | Exclude selected data points |
| `RelativeDate` | Relative date (last/next N days/months/years) |
| `Tuple` | Multi-column tuple filter |
| `RelativeTime` | Relative time window |
| `VisualTopN` | Visual-level Top N limiting data points |

---

## `howCreated` — Filter Origin

| Value | Meaning |
|---|---|
| `Auto` | Auto-created when a field is added to a visual |
| `User` | User added a field not used in the visual |
| `Drill` | Created by drilling down on a data point |
| `Include` | Created by including a data point |
| `Exclude` | Created by excluding a data point |
| `Drillthrough` | Applied from a drill-through action on another page |

---

## `objects` — Filter Card Formatting (FilterContainerFormattingObjects)

Only the `general` object is supported, with two properties:

| Property | Purpose |
|---|---|
| `requireSingleSelect` | Force single-select in the filter card |
| `isInvertedSelectionMode` | Invert the selection (select-all-except) |

```json
"objects": {
  "general": [
    {
      "properties": {
        "requireSingleSelect": { "expr": { "Literal": { "Value": "true" } } }
      }
    }
  ]
}
```

---

## The `filter` Body (FilterDefinition)

The `filter` property is a partial query — a `FilterDefinition` from the semantic query schema:

```json
"filter": {
  "Version": 2,
  "From": [ { "Name": "p", "Entity": "Product", "Type": 0 } ],
  "Where": [
    {
      "Condition": {
        "In": {
          "Expressions": [ { "Column": { "Expression": { "SourceRef": { "Source": "p" } }, "Property": "Category" } } ],
          "Values": [ [ { "Literal": { "Value": "'Bikes'" } } ] ]
        }
      }
    }
  ]
}
```

- `From` (**required**) — tables (`EntitySource[]`), each `{ Name, Entity, Type }`
- `Where` (**required**) — array of `QueryFilter` (`{ Target?, Condition, Annotations? }`)
- See `11_data_fields.md` for the full expression grammar (In, Comparison, Between, Contains, etc.).

---

## Complete Example — Categorical filter on Product[Category] = Bikes

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/filterConfiguration/1.3.0/schema.json",
  "filters": [
    {
      "name": "Filter_Category",
      "type": "Categorical",
      "howCreated": "User",
      "field": {
        "Column": {
          "Expression": { "SourceRef": { "Entity": "Product" } },
          "Property": "Category"
        }
      },
      "filter": {
        "Version": 2,
        "From": [ { "Name": "p", "Entity": "Product", "Type": 0 } ],
        "Where": [
          {
            "Condition": {
              "In": {
                "Expressions": [ { "Column": { "Expression": { "SourceRef": { "Source": "p" } }, "Property": "Category" } } ],
                "Values": [ [ { "Literal": { "Value": "'Bikes'" } } ] ]
              }
            }
          }
        ]
      }
    }
  ]
}
```

---

## Related Knowledge Base Files

- `11_data_fields.md` — `QueryExpressionContainer`, `FilterDefinition`, all expression types
- `07_report.md` / `06_page.md` / `01_charts_basics.md` — where `filterConfig` is used
