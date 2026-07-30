# Page Plan — Executive Overview

**Purpose:** Give leadership a concise, at-a-glance view of the key performance trend over time to support tracking and decision-making.

**Internal page name:** (auto-generated on creation)

## Planned visuals

1. **Total Sales (KPI)** (cardVisual) — Hero metric giving the current headline number at a glance.
   - Values: Sales[Total Sales] (measure)
2. **Sales Trend** (lineChart) — Answers how the metric is trending over time; continuous time axis.
   - Category: Date[Date] (column)
   - Y: Sales[Total Sales] (measure)

## Slicers

- Date range / Year slicer (top-right filter rail)

## Notes

Bound to Contoso Sample Report semantic model (c54a8f89-7a72-4acc-92d6-9f1a8ff0e1ca) for report Test_SN_MCP (8ce4dc28-f26d-4f55-96cd-452e8e1969e2, workspace a0f458be-e2a3-47c8-85f7-75d7b7f6034f). Schema discovery via list_semantic_model_columns is currently returning HTTP 400 on executeQueries (likely missing Build permission or XMLA endpoint disabled) - table/field names above are placeholders based on the well-known Contoso sample schema and must be confirmed before calling add_field_to_visual. Layout: KPI card top-left, line chart spanning remaining width - standard executive hero-metric + trend composition. Avoid scatter, box plot, histogram, matrix, gauge, 3D, dual-axis on executive pages.

## Approval

- [ ] Approved by user before calling any authoring tool (`add_page` / `add_visual` / `add_field_to_visual`).
