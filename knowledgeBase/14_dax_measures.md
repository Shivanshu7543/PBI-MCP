# Report Extensions & DAX (`reportExtensions.json`) — Deep Dive

Schema: `https://developer.microsoft.com/json-schemas/fabric/item/report/definition/reportExtension/1.0.0/schema.json`

File location: `definition/reportExtensions.json`

This is the **only place you author DAX directly in a report definition**. A report extension adds **report-level measures** (DAX measures that live in the report, not the semantic model) onto existing model entities. Useful for LiveConnect reports where you can't edit the shared semantic model.

> DAX also appears inline inside visual/filter queries via `NativeMeasure`, `NativeColumn`, and `NativeVisualCalculation` — see `11_data_fields.md`. This file is for named, reusable report-level measures.

---

## Top-Level Structure

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/reportExtension/1.0.0/schema.json",
  "name": "extension",
  "entities": [ ... ]
}
```

### Required Fields

| Field | Type | Description |
|---|---|---|
| `$schema` | string | The reportExtension 1.0.0 schema URL |
| `name` | string | Name of the extension (default `"extension"`) |

`entities` is optional. `additionalProperties: false`.

---

## `entities` — ReportExtensionEntity[]

Each entity extends a table that already exists in the semantic model.

| Field | Required | Description |
|---|---|---|
| `name` | **yes** | Must match a table/entity name in the semantic model |
| `measures` | no | Report-level measures to add to this entity |

```json
"entities": [
  {
    "name": "Sales",
    "measures": [ ... ]
  }
]
```

---

## `measures` — ReportExtensionMeasure

The DAX measure definition. **Required**: `name`, `dataType`, `expression`.

```json
{
  "name": "Profit Margin",
  "dataType": "Decimal",
  "expression": "DIVIDE(SUM(Sales[Profit]), SUM(Sales[Revenue]))",
  "formatString": "0.00%",
  "hidden": false,
  "description": "Profit as a percentage of revenue",
  "displayFolder": "KPIs",
  "dataCategory": "",
  "annotations": [ { "name": "author", "value": "Data Team" } ],
  "references": { ... }
}
```

| Field | Required | Description |
|---|---|---|
| `name` | **yes** | Unique across the semantic model + other extension measures |
| `dataType` | **yes** | `PrimitiveTypeName` (see enum) |
| `expression` | **yes** | **The DAX expression** for the measure |
| `dataCategory` | no | Extended data category |
| `hidden` | no | Hide the measure |
| `formatString` | no | VBA-style format string (e.g. `"0.00%"`, `"#,0"`, `"$#,0.00"`) |
| `description` | no | Measure description |
| `displayFolder` | no | Display folder in the fields list |
| `measureTemplate` | no | `{ daxTemplateName, version }` if created from a template |
| `annotations` | no | `{ name, value }[]` metadata |
| `references` | no | `ExpressionReferences` — other measures used in the DAX |

### PrimitiveTypeName (`dataType` enum)

`Binary`, `Boolean`, `Date`, `DateTime`, `DateTimeZone`, `Decimal`, `Double`, `Duration`, `Integer`, `Json`, `None`, `Null`, `Text`, `Time`, `Variant`

For most numeric measures use `Decimal` or `Double`; for counts use `Integer`.

---

## `references` — ExpressionReferences

Declares which other measures the DAX expression depends on. Helps the engine resolve dependencies.

| Field | Description |
|---|---|
| `unrecognizedReferences` | `false` if all references resolve |
| `measures` | Array of `MeasureReference` |

### MeasureReference (required: `entity`, `name`)

| Field | Description |
|---|---|
| `schema` | Leave empty for model measures; use the extension name for other extension measures |
| `entity` | Entity (table) name of the referenced measure |
| `name` | Name of the referenced measure |

```json
"references": {
  "unrecognizedReferences": false,
  "measures": [
    { "entity": "Sales", "name": "Total Revenue" },
    { "entity": "Sales", "name": "Total Profit" }
  ]
}
```

---

## Complete Example — a report-level DAX measure

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/reportExtension/1.0.0/schema.json",
  "name": "extension",
  "entities": [
    {
      "name": "Sales",
      "measures": [
        {
          "name": "Profit Margin %",
          "dataType": "Decimal",
          "expression": "DIVIDE([Total Profit], [Total Revenue])",
          "formatString": "0.00%",
          "displayFolder": "KPIs",
          "references": {
            "unrecognizedReferences": false,
            "measures": [
              { "entity": "Sales", "name": "Total Profit" },
              { "entity": "Sales", "name": "Total Revenue" }
            ]
          }
        }
      ]
    }
  ]
}
```

Once defined, reference this measure in a visual exactly like a model measure:

```json
{ "Measure": { "Expression": { "SourceRef": { "Entity": "Sales" } }, "Property": "Profit Margin %" } }
```

---

## Where DAX lives — quick map

| Location | Schema / file | Use |
|---|---|---|
| Report-level named measures | `reportExtensions.json` (this file) | Reusable DAX measures on model entities |
| Inline native measure | `NativeMeasure` in `11_data_fields.md` | One-off DAX measure inside a query (`Language: "dax"`) |
| Inline native column | `NativeColumn` in `11_data_fields.md` | DAX-defined column in a query |
| Visual calculations | `NativeVisualCalculation` in `11_data_fields.md` | DAX evaluated in visual calc context |

---

## Related Knowledge Base Files

- `11_data_fields.md` — inline DAX (`NativeMeasure` / `NativeColumn` / `NativeVisualCalculation`) and how to reference measures
- `07_report.md` — `report.json` (the report the extension attaches to)
