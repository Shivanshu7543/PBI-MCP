# Query, QueryState & Projections — Deep Dive

This file explains how to bind data fields from a semantic model to a visual using the `query` object inside `visual.json`.

---

## The `query` Object

```json
"query": {
  "queryState": { ... },
  "sortDefinition": { ... },
  "options": { ... },
  "isDrillDisabled": false
}
```

| Field | Required | Description |
|---|---|---|
| `queryState` | **yes** | Maps role keys to field projections |
| `sortDefinition` | no | How the data is sorted |
| `options` | no | Visual-specific query options |
| `isDrillDisabled` | no | Disable drill (custom visuals only) |

---

## `queryState` — The Core of Data Binding

`queryState` is a dictionary where each **key is a role name** specific to the visual type, and each **value is a ProjectionState** containing the fields assigned to that role.

```json
"queryState": {
  "Category": {        ← role name (visual-type specific)
    "projections": [   ← list of fields assigned to this role
      { ... }
    ]
  },
  "Y": {
    "projections": [
      { ... }
    ]
  }
}
```

Role names vary per visual type — see `04_charts_fields.md` for the full list.

---

## `ProjectionState` Object

```json
{
  "showAll": false,
  "projections": [ ... ],
  "fieldParameters": [ ... ]
}
```

| Field | Required | Description |
|---|---|---|
| `projections` | **yes** | Array of `RoleProjection` objects |
| `showAll` | no | Show all values for every field in this role |
| `fieldParameters` | no | Field parameter references (advanced) |

---

## `RoleProjection` Object

This is where you specify the actual semantic model field:

```json
{
  "field": { ... },
  "queryRef": "Table.FieldName",
  "displayName": "My Label",
  "format": "#,0",
  "active": true,
  "hidden": false
}
```

| Field | Required | Type | Description |
|---|---|---|---|
| `field` | **yes** | QueryExpressionContainer | Reference to column or measure in semantic model |
| `queryRef` | **yes** | string | Unique name for this field per visual (`Table.Field`) |
| `displayName` | no | string | Override the field's display name in the visual |
| `format` | no | string | Format string e.g. `"#,0"`, `"0.00%"` (max 255 chars) |
| `active` | no | boolean | Is this field active (used in drill operations) |
| `hidden` | no | boolean | Hide this field (used in visual calculations) |

---

## The `field` — QueryExpressionContainer

### Referencing a Column (dimension/text/date field)

```json
"field": {
  "Column": {
    "Expression": {
      "SourceRef": { "Entity": "TableName" }
    },
    "Property": "ColumnName"
  }
}
```

### Referencing a Measure (DAX calculated value)

```json
"field": {
  "Measure": {
    "Expression": {
      "SourceRef": { "Entity": "TableName" }
    },
    "Property": "MeasureName"
  }
}
```

### `queryRef` convention
Always use format `"TableName.FieldName"` — this must be unique per visual:
```
"queryRef": "Sales.Total Revenue"
"queryRef": "Product.Category"
"queryRef": "Calendar.Year"
```

---

## `sortDefinition` Object

Controls how data is ordered in the visual.

```json
"sortDefinition": {
  "isDefaultSort": true,
  "sort": [
    {
      "field": {
        "Measure": {
          "Expression": { "SourceRef": { "Entity": "Sales" } },
          "Property": "Total Sales"
        }
      },
      "direction": "Descending"
    }
  ]
}
```

| Field | Description |
|---|---|
| `isDefaultSort` | `true` = Power BI can update sort automatically. `false` = user explicitly set it. |
| `sort` | Array of `QuerySort` — fields to sort by in order |

### `QuerySort` Object

| Field | Required | Description |
|---|---|---|
| `field` | **yes** | QueryExpressionContainer — the field to sort by |
| `direction` | **yes** | `"Ascending"` or `"Descending"` |

---

## `options` Object — Visual Query Options

Only relevant for specific visual types:

```json
"options": {
  "allowBinnedLineSample": true,
  "allowOverlappingPointsSample": false
}
```

| Option | Applies to | Description |
|---|---|---|
| `allowBinnedLineSample` | `lineChart`, `areaChart` | Better sampling for large datasets on line charts |
| `allowOverlappingPointsSample` | `scatterChart` | Better sampling for scatter charts with overlapping points |

---

## `expansionStates` — Drill/Hierarchy Expansion

Defines which specific data points are expanded in a hierarchy drill. Usually empty for new visuals.

```json
"expansionStates": [
  {
    "roles": ["Category"],
    "root": {
      "isToggled": false,
      "children": []
    },
    "levels": [
      {
        "queryRefs": ["Product.Category"],
        "isCollapsed": false
      }
    ]
  }
]
```

Leave `expansionStates` as an empty array `[]` or omit it entirely for new visuals.

---

## Complete Example — Bar Chart with Category + Measure + Sort

```json
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
    },
    "Series": {
      "projections": [
        {
          "field": {
            "Column": {
              "Expression": { "SourceRef": { "Entity": "Product" } },
              "Property": "Sub-Category"
            }
          },
          "queryRef": "Product.Sub-Category"
        }
      ]
    }
  },
  "sortDefinition": {
    "isDefaultSort": false,
    "sort": [
      {
        "field": {
          "Measure": {
            "Expression": { "SourceRef": { "Entity": "Sales" } },
            "Property": "Total Sales"
          }
        },
        "direction": "Descending"
      }
    ]
  }
}
```

---

## `syncGroup` — Slicer Sync (Slicers Only)

Only applies to `slicer`, `advancedSlicerVisual`, `textSlicer`:

```json
"syncGroup": {
  "groupName": "DateSyncGroup",
  "fieldChanges": true,
  "filterChanges": true
}
```

| Field | Required | Description |
|---|---|---|
| `groupName` | **yes** | Unique name — slicers with the same name sync together |
| `fieldChanges` | no | Sync when field selection changes |
| `filterChanges` | no | Sync when filter value changes |
