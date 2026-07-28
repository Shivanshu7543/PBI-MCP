# Visual Roles (queryState Keys) per Visual Type

Each visual type has specific **role names** that are used as keys in `queryState`.
These role names are fixed by Power BI — you must use the exact names shown below.

**Legend:**
- **Required** — visual will not render without this role
- **Optional** — adds extra functionality if provided
- `Column` — use a dimension/text/date field
- `Measure` — use a DAX measure or numeric column

---

## Comparison Visuals

### `barChart` — Horizontal Bar Chart
| Role Key | Required | Field Type | Description |
|---|---|---|---|
| `Category` | yes | Column | Y-axis categories (horizontal bars) |
| `Y` | yes | Measure | Bar length (value axis) |
| `Series` | no | Column | Split bars by a second dimension |
| `Tooltips` | no | Measure/Column | Extra fields shown in tooltip |

### `clusteredBarChart` — Clustered Horizontal Bar Chart
| Role Key | Required | Field Type | Description |
|---|---|---|---|
| `Category` | yes | Column | Y-axis categories |
| `Y` | yes | Measure | Bar values |
| `Series` | no | Column | Groups bars into clusters |
| `Tooltips` | no | Measure/Column | Tooltip fields |

### `columnChart` — Vertical Column Chart
| Role Key | Required | Field Type | Description |
|---|---|---|---|
| `Category` | yes | Column | X-axis categories |
| `Y` | yes | Measure | Column height |
| `Series` | no | Column | Split columns by dimension |
| `Tooltips` | no | Measure/Column | Tooltip fields |

### `clusteredColumnChart` — Clustered Column Chart
| Role Key | Required | Field Type | Description |
|---|---|---|---|
| `Category` | yes | Column | X-axis categories |
| `Y` | yes | Measure | Column values |
| `Series` | no | Column | Groups into clusters |
| `Tooltips` | no | Measure/Column | Tooltip fields |

### `hundredPercentStackedBarChart`
| Role Key | Required | Field Type | Description |
|---|---|---|---|
| `Category` | yes | Column | Y-axis categories |
| `Y` | yes | Measure | Values (shown as %) |
| `Series` | no | Column | Stack segments |
| `Tooltips` | no | Measure/Column | Tooltip fields |

### `hundredPercentStackedColumnChart`
| Role Key | Required | Field Type | Description |
|---|---|---|---|
| `Category` | yes | Column | X-axis categories |
| `Y` | yes | Measure | Values (shown as %) |
| `Series` | no | Column | Stack segments |
| `Tooltips` | no | Measure/Column | Tooltip fields |

---

## Trend Visuals

### `lineChart` — Line Chart
| Role Key | Required | Field Type | Description |
|---|---|---|---|
| `Category` | yes | Column | X-axis (usually a date) |
| `Y` | yes | Measure | Line value |
| `Series` | no | Column | Multiple lines |
| `Y2` | no | Measure | Secondary Y-axis value |
| `Tooltips` | no | Measure/Column | Tooltip fields |

### `areaChart` — Area Chart
| Role Key | Required | Field Type | Description |
|---|---|---|---|
| `Category` | yes | Column | X-axis |
| `Y` | yes | Measure | Area value |
| `Series` | no | Column | Multiple areas |
| `Tooltips` | no | Measure/Column | Tooltip fields |

### `stackedAreaChart` — Stacked Area Chart
| Role Key | Required | Field Type | Description |
|---|---|---|---|
| `Category` | yes | Column | X-axis |
| `Y` | yes | Measure | Stacked area values |
| `Series` | no | Column | Stack segments |
| `Tooltips` | no | Measure/Column | Tooltip fields |

### `hundredPercentStackedAreaChart`
| Role Key | Required | Field Type | Description |
|---|---|---|---|
| `Category` | yes | Column | X-axis |
| `Y` | yes | Measure | Values (shown as %) |
| `Series` | no | Column | Stack segments |
| `Tooltips` | no | Measure/Column | Tooltip fields |

---

## Combination Visuals

### `lineClusteredColumnComboChart`
| Role Key | Required | Field Type | Description |
|---|---|---|---|
| `Category` | yes | Column | Shared X-axis |
| `Y` | yes | Measure | Column bar values |
| `Y2` | no | Measure | Line values (secondary axis) |
| `Series` | no | Column | Column series |
| `Tooltips` | no | Measure/Column | Tooltip fields |

### `lineStackedColumnComboChart`
| Role Key | Required | Field Type | Description |
|---|---|---|---|
| `Category` | yes | Column | Shared X-axis |
| `Y` | yes | Measure | Stacked column values |
| `Y2` | no | Measure | Line values |
| `Series` | no | Column | Column series |
| `Tooltips` | no | Measure/Column | Tooltip fields |

---

## Part-to-Whole Visuals

### `pieChart` — Pie Chart
| Role Key | Required | Field Type | Description |
|---|---|---|---|
| `Category` | yes | Column | Pie slice labels |
| `Y` | yes | Measure | Slice size |
| `Tooltips` | no | Measure/Column | Tooltip fields |

### `donutChart` — Donut Chart
| Role Key | Required | Field Type | Description |
|---|---|---|---|
| `Category` | yes | Column | Slice labels |
| `Y` | yes | Measure | Slice size |
| `Tooltips` | no | Measure/Column | Tooltip fields |

### `treemap` — Treemap
| Role Key | Required | Field Type | Description |
|---|---|---|---|
| `Group` | yes | Column | Rectangles/grouping |
| `Values` | yes | Measure | Rectangle size |
| `Details` | no | Column | Sub-grouping |
| `Tooltips` | no | Measure/Column | Tooltip fields |

---

## Process / Distribution Visuals

### `funnel` — Funnel Chart
| Role Key | Required | Field Type | Description |
|---|---|---|---|
| `Category` | yes | Column | Stage labels |
| `Y` | yes | Measure | Stage values |
| `Tooltips` | no | Measure/Column | Tooltip fields |

### `waterfallChart` — Waterfall Chart
| Role Key | Required | Field Type | Description |
|---|---|---|---|
| `Category` | yes | Column | X-axis categories |
| `Y` | yes | Measure | Values (positive/negative) |
| `Breakdown` | no | Column | Breakdown dimension |
| `Tooltips` | no | Measure/Column | Tooltip fields |

### `ribbonChart` — Ribbon Chart
| Role Key | Required | Field Type | Description |
|---|---|---|---|
| `Category` | yes | Column | X-axis |
| `Y` | yes | Measure | Ribbon values |
| `Series` | yes | Column | Ribbon categories (ranked) |
| `Tooltips` | no | Measure/Column | Tooltip fields |

---

## Relationship Visuals

### `scatterChart` — Scatter Chart
| Role Key | Required | Field Type | Description |
|---|---|---|---|
| `X` | yes | Measure | Horizontal axis value |
| `Y` | yes | Measure | Vertical axis value |
| `Details` | no | Column | Data point label |
| `Series` | no | Column | Colour by dimension |
| `Size` | no | Measure | Bubble size |
| `PlayAxis` | no | Column | Animation axis |
| `Tooltips` | no | Measure/Column | Tooltip fields |

---

## KPI Visuals

### `cardVisual` — Card
| Role Key | Required | Field Type | Description |
|---|---|---|---|
| `Values` | yes | Measure | The value to display |
| `Tooltips` | no | Measure/Column | Tooltip fields |

### `kpi` — KPI Visual
| Role Key | Required | Field Type | Description |
|---|---|---|---|
| `Value` | yes | Measure | The KPI value |
| `Goal` | no | Measure | Target value |
| `TrendAxis` | no | Column | Trend line axis (usually date) |
| `Tooltips` | no | Measure/Column | Tooltip fields |

### `gauge` — Gauge / Radial Chart
| Role Key | Required | Field Type | Description |
|---|---|---|---|
| `Y` | yes | Measure | Current value |
| `MinValue` | no | Measure | Minimum value |
| `MaxValue` | no | Measure | Maximum value |
| `TargetValue` | no | Measure | Target/goal value |
| `Tooltips` | no | Measure/Column | Tooltip fields |

---

## Grid Visuals

### `tableEx` — Table
| Role Key | Required | Field Type | Description |
|---|---|---|---|
| `Values` | yes | Column/Measure | Table columns (add multiple) |
| `Tooltips` | no | Measure/Column | Tooltip fields |

### `pivotTable` — Matrix / Pivot Table
| Role Key | Required | Field Type | Description |
|---|---|---|---|
| `Rows` | yes | Column | Row headers |
| `Columns` | no | Column | Column headers |
| `Values` | yes | Measure | Cell values |
| `Tooltips` | no | Measure/Column | Tooltip fields |

---

## Filter Visuals

### `slicer` — Slicer
| Role Key | Required | Field Type | Description |
|---|---|---|---|
| `Field` | yes | Column | The field to filter by |

### `textSlicer` — Text/Search Slicer
| Role Key | Required | Field Type | Description |
|---|---|---|---|
| `Field` | yes | Column | The field to search/filter |

### `advancedSlicerVisual` — Advanced Slicer
| Role Key | Required | Field Type | Description |
|---|---|---|---|
| `Field` | yes | Column | The field to filter by |

---

## AI / Analytics Visuals

### `decompositionTreeVisual` — Decomposition Tree
| Role Key | Required | Field Type | Description |
|---|---|---|---|
| `Analyze` | yes | Measure | The metric to analyse |
| `Explain By` | no | Column | Dimensions to break down by |

### `keyDriversVisual` — Key Influencers
| Role Key | Required | Field Type | Description |
|---|---|---|---|
| `Analyze` | yes | Measure/Column | The metric to explain |
| `Explain By` | no | Column | Potential influencing factors |

### `aiNarratives` — Smart Narratives
| Role Key | Required | Field Type | Description |
|---|---|---|---|
| `Fields` | no | Measure/Column | Fields to summarise |

---

## Map Visuals

### `shapeMap` — Shape Map
| Role Key | Required | Field Type | Description |
|---|---|---|---|
| `Location` | yes | Column | Geographic region name |
| `Color saturation` | no | Measure | Colour intensity value |
| `Tooltips` | no | Measure/Column | Tooltip fields |

### `azureMap` — Azure Maps
| Role Key | Required | Field Type | Description |
|---|---|---|---|
| `Location` | yes | Column | Location (address, lat/long, region) |
| `Latitude` | no | Column | Latitude value |
| `Longitude` | no | Column | Longitude value |
| `Size` | no | Measure | Bubble size |
| `Color saturation` | no | Measure | Bubble colour intensity |
| `Tooltips` | no | Measure/Column | Tooltip fields |

---

## Complete queryState Example — Matrix (pivotTable)

```json
"queryState": {
  "Rows": {
    "projections": [
      {
        "field": {
          "Column": {
            "Expression": { "SourceRef": { "Entity": "Product" } },
            "Property": "Category"
          }
        },
        "queryRef": "Product.Category"
      },
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
  },
  "Columns": {
    "projections": [
      {
        "field": {
          "Column": {
            "Expression": { "SourceRef": { "Entity": "Calendar" } },
            "Property": "Year"
          }
        },
        "queryRef": "Calendar.Year"
      }
    ]
  },
  "Values": {
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
```
