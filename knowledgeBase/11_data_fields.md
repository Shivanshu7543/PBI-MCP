# Semantic Query — Deep Dive

Schema: `https://developer.microsoft.com/json-schemas/fabric/item/report/definition/semanticQuery/1.4.0/schema.json`

This schema defines the **shared query and filter grammar** used everywhere in a report definition — visual data bindings (`query`/`queryState`), filter definitions (`filterConfig.filters[].filter` / `field`), sorting, and grouping. Understanding `QueryExpressionContainer` is the key to building any data-bound content.

---

## The Core Type: `QueryExpressionContainer`

An expression container holds **exactly one** expression, plus optional metadata. It is used anywhere a "field" or scalar expression is expected.

```json
{
  "Column": {
    "Expression": { "SourceRef": { "Entity": "Product" } },
    "Property": "Category"
  }
}
```

### Optional metadata (allowed on any container)

| Field | Description |
|---|---|
| `Name` | Name by which the expression is referenced |
| `NativeReferenceName` | Name for referencing in native (DAX) expressions |
| `Annotations` | Auxiliary metadata; may include `customTotalMetadata.baseQueryName` |

### The expression (exactly one of these — enforced by `oneOf`)

**References**
- `SourceRef` — reference to a source table. Two forms:
  - `StandaloneSourceRef`: `{ "Entity": "Product", "Schema"?: "..." }` (used at the top of a Column/Measure)
  - `QuerySourceRef`: `{ "Source": "p" }` (references a `From` alias)
- `Column` — `{ Expression: <SourceRef>, Property: "ColumnName" }`
- `Measure` — `{ Expression: <SourceRef>, Property: "MeasureName" }`
- `Hierarchy` / `HierarchyLevel`
- `PropertyVariationSource`
- `RoleRef` — reference a visual Role by name
- `SelectRef` — reference a named item in the Select clause
- `GroupRef`, `ResourcePackageItem`, `AllRolesRef`, `SummaryValueRef`

**Aggregations**
- `Aggregation` — `{ Function: <QueryAggregateFunction>, Expression: <container> }`
- `Min` / `Max` — `{ IncludeAllTypes: <n>, Expression }`
- `Percentile` — `{ Expression, K, Exclusive? }`

**Boolean / filter operators** (used inside `Where` conditions)
- `And` / `Or` — `{ Left, Right }` (QueryBinaryExpression)
- `Not` — `{ Expression }`
- `Comparison` — `{ ComparisonKind, Left, Right }`
- `Between` — `{ Expression, LowerBound, UpperBound }`
- `In` — `{ Expressions[], Values[][], Table? }`
- `Contains` / `StartsWith` — `{ Left, Right }`
- `Exists` — `{ Expression }` (must be a SourceRef)

**Literals & values**
- `Literal` — `{ Value: "..." }` (see Literal formats below)
- `DefaultValue` — model default (only as Right of an Equal Comparison)
- `AnyValue` — wildcard match (only as Right of an Equal Comparison)
- `Now`

**Date / arithmetic**
- `DateSpan` — `{ TimeUnit, Expression }`
- `DateAdd` — `{ Amount, TimeUnit, Expression }`
- `Arithmetic` — `{ Left, Right, Operator }`
- `Floor` — `{ Expression, Size, TimeUnit? }`
- `Discretize` — `{ Expression, Count }`

**Advanced / native**
- `Subquery` — `{ Query: <QueryDefinition> }`
- `ScopedEval` — `{ Expression, Scope[] }`
- `FilteredEval` — `{ Expression, Filters[] }`
- `Conditional` — `{ Cases[], DefaultValue? }`
- `NativeMeasure` / `NativeColumn` / `NativeVisualCalculation` — DAX expressions
- `TransformTableRef` / `TransformOutputRoleRef`
- `SparklineData` — `{ Measure, Groupings[], PointsPerSparkline?, ApplyCalculationGroupTo? }`
- `FillRule`, `ThemeDataColor` — `{ ColorId, Percent }`
- `VisualTopN` — `{ ItemCount }`

---

## Common Expression Building Blocks

### Column reference
```json
{ "Column": { "Expression": { "SourceRef": { "Entity": "Sales" } }, "Property": "Amount" } }
```

### Measure reference
```json
{ "Measure": { "Expression": { "SourceRef": { "Entity": "Sales" } }, "Property": "Total Revenue" } }
```

### Aggregation (Sum of a column)
```json
{
  "Aggregation": {
    "Function": 0,
    "Expression": { "Column": { "Expression": { "SourceRef": { "Entity": "Sales" } }, "Property": "Amount" } }
  }
}
```

---

## Enumerations (numeric constants)

### QueryAggregateFunction (`Aggregation.Function`)
| Value | Function |
|---|---|
| 0 | Sum |
| 1 | Average |
| 2 | Distinct count |
| 3 | Min |
| 4 | Max |
| 5 | Count (non-null) |
| 6 | Median |
| 7 | StandardDeviation |
| 8 | Variance |

### QueryComparisonKind (`Comparison.ComparisonKind`)
| Value | Meaning |
|---|---|
| 0 | Equal |
| 1 | GreaterThan |
| 2 | GreaterThanOrEqual |
| 3 | LessThan |
| 4 | LessThanOrEqual |

### ArithmeticOperatorKind (`Arithmetic.Operator`)
| Value | Op |
|---|---|
| 0 | Add |
| 1 | Subtract |
| 2 | Multiply |
| 3 | Divide |

### TimeUnit (`DateSpan`/`DateAdd`/`Floor`)
| Value | Unit |
|---|---|
| 0 | Day |
| 1 | Week |
| 2 | Month |
| 3 | Year |
| 4 | Decade |
| 5 | Second |
| 6 | Minute |
| 7 | Hour |

### SortDirection (`QuerySortClause.Direction`)
| Value | Direction |
|---|---|
| 1 | Ascending |
| 2 | Descending |

### IncludeAllTypes (`Min`/`Max`)
| Value | Behaviour |
|---|---|
| 0 | Exclude non-numeric types on mixed values |
| 1 | Include non-numeric if supported, else fallback |
| 2 | Include non-numeric, error if unsupported |

---

## Literal Value Formats (`Literal.Value`)

The `Value` is always a **string**, encoded per type:

| Type | Format | Example |
|---|---|---|
| Boolean | `"true"` / `"false"` | `"true"` |
| DateTime | `datetime'YYYY-MM-DDThh:mm:ss.ffffff'` | `"datetime'2024-01-01T00:00:00'"` |
| Decimal | number + `M` | `"2.4M"` |
| Double | number + `D` | `"2.4D"` |
| Integer | number + `L` | `"24L"` |
| Null | `"null"` | `"null"` |
| String | single-quoted | `"'some value'"` |

---

## `FilterDefinition` (the `filter` body of a FilterContainer)

A partial query defining what to filter.

```json
{
  "Version": 2,
  "From": [ { "Name": "p", "Entity": "Product", "Type": 0 } ],
  "Where": [
    {
      "Condition": {
        "Comparison": {
          "ComparisonKind": 1,
          "Left": { "Measure": { "Expression": { "SourceRef": { "Source": "p" } }, "Property": "Sales" } },
          "Right": { "Literal": { "Value": "1000L" } }
        }
      }
    }
  ]
}
```

| Field | Required | Description |
|---|---|---|
| `Version` | no | Query version, const `2` |
| `From` | **yes** | `EntitySource[]` — tables in scope |
| `Where` | **yes** | `QueryFilter[]` — conditions |

### QueryFilter
| Field | Required | Description |
|---|---|---|
| `Condition` | **yes** | A `QueryExpressionContainer` evaluating to boolean |
| `Target` | no | Expressions the condition applies to |
| `Annotations` | no | Auxiliary metadata |

### EntitySource (`From` entries)
| Field | Required | Description |
|---|---|---|
| `Name` | **yes** | Alias used in the query (e.g. `"p"`) |
| `Entity` | no | Table name in the model |
| `Schema` | no | Schema (omit for default) |
| `Expression` | no | Table-producing expression (when `Type` = 2) |
| `Type` | no | `0` model table, `1` presentation object, `2` expression-produced |

---

## `QueryDefinition` (a full query — used in `Subquery` and visual queries)

| Field | Required | Description |
|---|---|---|
| `From` | **yes** | `EntitySource[]` |
| `Select` | **yes** | `QueryExpressionContainer[]` — projected expressions |
| `Where` | no | `QueryFilter[]` |
| `OrderBy` | no | `QuerySortClause[]` (`{ Expression, Direction }`) |
| `GroupBy` | no | `QueryExpressionContainer[]` |
| `Transform` | no | `QueryTransform[]` |
| `VisualShape` | no | `Axis[]` metadata |
| `Top` | no | Row limit |
| `Version` | no | const `2` |

---

## Related Knowledge Base Files

- `10_filters.md` — `filterConfig` / FilterContainer (uses `field` + `filter` from this schema)
- `02_charts_data.md` — how visuals reference these expressions in `queryState`/projections
- `01_charts_basics.md` — visual data bindings
