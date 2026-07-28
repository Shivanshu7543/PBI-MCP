# Power BI Visual Configuration Schema — Deep Dive

Schema source: `https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualConfiguration/2.3.0/schema.embedded.json`

---

## Top-Level Structure of `visual.json`

Every visual on a report page is stored as a `visual.json` file with this structure:

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.10.0/schema.json",
  "name": "<VISUAL_ID>",
  "position": { ... },
  "visual": { ... }
}
```

### Top-level fields

| Field | Required | Type | Description |
|---|---|---|---|
| `$schema` | yes | string | Always `visualContainer/2.10.0/schema.json` |
| `name` | yes | string | Unique 20-char hex ID for this visual on the page |
| `position` | yes | object | Canvas placement (x, y, z, width, height, tabOrder) |
| `visual` | yes | object | Visual configuration — see below |

---

## The `position` Object

```json
"position": {
  "x": 0,
  "y": 0,
  "z": 1000,
  "height": 200,
  "width": 300,
  "tabOrder": 1000
}
```

| Field | Type | Description | Default |
|---|---|---|---|
| `x` | number | Horizontal offset from canvas left edge (pts) | 0 |
| `y` | number | Vertical offset from canvas top edge (pts) | 0 |
| `z` | number | Layer stacking order — higher = on top | 1000 |
| `height` | number | Visual height in points | 200 |
| `width` | number | Visual width in points | 300 |
| `tabOrder` | number | Keyboard accessibility tab order | 1000 |

**Canvas size:** 1280 × 720 pts (standard). Visuals must fit within these bounds.

---

## The `visual` Object

This is the core configuration. The full schema is `visualConfiguration/2.3.0`.

```json
"visual": {
  "visualType": "barChart",
  "autoSelectVisualType": false,
  "query": { ... },
  "expansionStates": [ ... ],
  "objects": { ... },
  "visualContainerObjects": { ... },
  "syncGroup": { ... },
  "drillFilterOtherVisuals": true
}
```

### Fields in `visual`

| Field | Required | Type | Description |
|---|---|---|---|
| `visualType` | **yes** | string | The visual type name e.g. `barChart`, `lineChart` |
| `autoSelectVisualType` | no | boolean | If true, Power BI picks the visual type automatically |
| `query` | no | Query object | Defines which data fields are bound to the visual |
| `expansionStates` | no | array | Which data points are expanded (hierarchy/drill) |
| `objects` | no | object | Visual-specific formatting (colours, data labels etc.) |
| `visualContainerObjects` | no | object | Container formatting (title, background, border etc.) |
| `syncGroup` | no | object | Slicer sync group (slicers only) |
| `drillFilterOtherVisuals` | no | boolean | Whether drill actions filter cross-visuals |

---

## Minimal Valid Visual

An empty visual with no data bound — only `visualType` is required inside `visual`:

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.10.0/schema.json",
  "name": "3852e5607b224b8ebd1a",
  "position": {
    "x": 0,
    "y": 0,
    "z": 1000,
    "height": 200,
    "width": 300,
    "tabOrder": 1000
  },
  "visual": {
    "visualType": "barChart",
    "drillFilterOtherVisuals": true
  }
}
```

---

## Visual with Data Bound (barChart example)

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.10.0/schema.json",
  "name": "3852e5607b224b8ebd1a",
  "position": {
    "x": 0,
    "y": 0,
    "z": 1000,
    "height": 200,
    "width": 300,
    "tabOrder": 1000
  },
  "visual": {
    "visualType": "barChart",
    "drillFilterOtherVisuals": true,
    "query": {
      "queryState": {
        "Category": {
          "projections": [
            {
              "field": {
                "Column": {
                  "Expression": { "SourceRef": { "Entity": "Product" } },
                  "Property": "Category"
                }
              },
              "queryRef": "Product.Category"
            }
          ]
        },
        "Y": {
          "projections": [
            {
              "field": {
                "Measure": {
                  "Expression": { "SourceRef": { "Entity": "Sales" } },
                  "Property": "Total Sales"
                }
              },
              "queryRef": "Sales.Total Sales"
            }
          ]
        }
      }
    }
  }
}
```

---

## Key Concepts

### `name` — Visual ID
- 20 lowercase hex characters
- Must be **unique per page** (not per report)
- Generate with: `import secrets; secrets.token_hex(10)`

### `queryRef` — Field Reference
- Format: `"TableName.FieldName"` e.g. `"Sales.Total Sales"`
- Must be unique **per visual**
- Used to reference fields in sort definitions and filters

### Field Expression Types
There are two ways to reference a field from the semantic model:

**Column** (dimension/attribute):
```json
{
  "Column": {
    "Expression": { "SourceRef": { "Entity": "Product" } },
    "Property": "Category"
  }
}
```

**Measure** (calculated value):
```json
{
  "Measure": {
    "Expression": { "SourceRef": { "Entity": "Sales" } },
    "Property": "Total Sales"
  }
}
```

---

## Related Knowledge Base Files

- `02_charts_data.md` — Deep dive on `query`, `queryState`, projections and sort
- `03_charts_look.md` — Deep dive on `visualContainerObjects` (title, border, background etc.)
- `04_charts_fields.md` — What `queryState` role keys each visual type uses
