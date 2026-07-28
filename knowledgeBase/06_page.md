# Page (`page.json`) — Deep Dive

Schema: `https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json`

File location: `definition/pages/<page-name>/page.json`

Defines a single report page — its size, scaling, page-level filters, formatting, and visual interactions.

---

## Structure

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json",
  "name": "ReportSection1",
  "displayName": "Page 1",
  "displayOption": "FitToPage",
  "height": 720,
  "width": 1280,
  "filterConfig": { ... },
  "pageBinding": { ... },
  "objects": { ... },
  "type": "Drillthrough",
  "visibility": "AlwaysVisible",
  "visualInteractions": [ ... ],
  "annotations": [ ... ],
  "howCreated": "Default"
}
```

---

## Required Fields

| Field | Type | Description |
|---|---|---|
| `$schema` | string | Must be the page 2.1.0 schema URL |
| `name` | string | Unique page identifier (max 50 chars). Used in `pageOrder`, drillthrough, etc. |
| `displayName` | string | User-facing page name shown on the tab |
| `displayOption` | enum | How the page scales — see below |

---

## Optional Fields

| Field | Type | Description |
|---|---|---|
| `height` | number | Page height in pixels (required unless `DeprecatedDynamic`) |
| `width` | number | Page width in pixels (required unless `DeprecatedDynamic`) |
| `filterConfig` | object | Page-level filters (applied on top of report filters) |
| `pageBinding` | object | Metadata for tooltip/drillthrough usage |
| `objects` | object | Page formatting (background, size, canvas settings) |
| `type` | enum | `Drillthrough` or `Tooltip` — special page usage |
| `visibility` | enum | `AlwaysVisible` or `HiddenInViewMode` |
| `visualInteractions` | array | How selecting a data point in one visual filters others |
| `annotations` | array | Comments / readme metadata |
| `howCreated` | enum | `Default`, `Copilot`, etc. |

---

## `displayOption` — Page Scaling (enum: PageDisplayOption)

| Value | Description |
|---|---|
| `FitToPage` | Scale so both width and height fit the viewport (most common) |
| `FitToWidth` | Scale width to fit; height adjusts to keep aspect ratio |
| `ActualSize` | No scaling; page centred on canvas |
| `ActualSizeTopLeft` | *(Deprecated)* No scaling; anchored top-left. Use `ActualSize`. |
| `DeprecatedDynamic` | *(Deprecated)* No fixed width/height. Avoid. |

---

## Standard Page Sizes (pixels)

| Layout | Width | Height |
|---|---|---|
| 16:9 (default) | 1280 | 720 |
| 4:3 | 960 | 720 |
| Letter | 816 | 1056 |
| Tooltip (default) | 320 | 240 |

---

## `visibility`

| Value | Description |
|---|---|
| `AlwaysVisible` | Page always shown in the pages list (default) |
| `HiddenInViewMode` | Page hidden when viewing report (still visible in edit) |

---

## `type` — Special Page Usage

| Value | Description |
|---|---|
| `Drillthrough` | Page used as a drillthrough target |
| `Tooltip` | Page used as a custom tooltip |

Omit `type` for a normal page.

---

## `visualInteractions` — Cross-Visual Filtering

Defines how selecting a data point in a **source** visual affects a **target** visual.

```json
"visualInteractions": [
  {
    "source": "3852e5607b224b8ebd1a",
    "target": "7df3763f63115a096029",
    "type": "HighlightFilter"
  }
]
```

| Field | Required | Description |
|---|---|---|
| `source` | yes | Name of the visual triggering the interaction |
| `target` | yes | Name of the visual receiving the interaction |
| `type` | yes | Interaction type — see below |

### Interaction types (VisualInteractionFilterType)

| Value | Description |
|---|---|
| `Default` | Target visual decides highlight vs filter |
| `DataFilter` | Selection applied as a filter to the target |
| `HighlightFilter` | Selection applied as a highlight |
| `NoFilter` | Selection ignored by the target |

---

## `objects` — Page Formatting (PageFormattingObjects)

Same expression-wrapper format as visual formatting (`{ "expr": { "Literal": { "Value": "..." } } }`).

Available formatting object keys:

| Object | Purpose |
|---|---|
| `pageInformation` | Page name, alt name, type, Q&A pod toggle |
| `pageSize` | Page size type, width, height |
| `background` | Page background colour/image/transparency |
| `displayArea` | Vertical alignment of the canvas |
| `outspace` | Wallpaper (area outside the page) |
| `outspacePane` | Filter pane styling |
| `filterCard` | Filter card styling |
| `pageRefresh` | Auto page refresh settings |
| `personalizeVisual` | Allow end users to personalise visuals |

### Example — page background

```json
"objects": {
  "background": [
    {
      "properties": {
        "color": { "solid": { "color": { "expr": { "Literal": { "Value": "'#FFFFFF'" } } } } },
        "transparency": { "expr": { "Literal": { "Value": "0D" } } }
      }
    }
  ]
}
```

---

## `pageBinding` — Tooltip / Drillthrough Binding

```json
"pageBinding": {
  "name": "DrillthroughBinding1",
  "type": "Drillthrough",
  "referenceScope": "Default",
  "acceptsFilterContext": "Default",
  "parameters": [
    {
      "name": "ProductParam",
      "boundFilter": "ProductFilter",
      "fieldExpr": {
        "Column": {
          "Expression": { "SourceRef": { "Entity": "Product" } },
          "Property": "Category"
        }
      }
    }
  ]
}
```

| Field | Required | Description |
|---|---|---|
| `name` | yes | Unique binding name across the report |
| `type` | yes | `Default`, `Drillthrough`, or `Tooltip` |
| `referenceScope` | no | `Default` (this report) or `CrossReport` |
| `acceptsFilterContext` | no | `Default` (flows filters) or `None` |
| `parameters` | no | Binding parameters (field/filter mappings) |

---

## `annotations` — Custom Metadata

```json
"annotations": [
  { "name": "author", "value": "Data Team" },
  { "name": "readme", "value": "Sales overview page" }
]
```

---

## Minimal Valid Page (blank)

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json",
  "name": "ReportSection1",
  "displayName": "Page 1",
  "displayOption": "FitToPage",
  "height": 720,
  "width": 1280
}
```

---

## Related Knowledge Base Files

- `05_page_order.md` — `pages.json` (page order + active page)
- `01_charts_basics.md` — visuals placed on the page
- `07_filters.md` — the `filterConfig` structure used at page and report level *(to be added)*
