# Visual Container Formatting — Deep Dive

The `visualContainerObjects` field inside `visual` controls all formatting of the **visual container** — the wrapper around the visual including title, background, border, shadow, tooltip, and header buttons.

---

## Structure

```json
"visualContainerObjects": {
  "title": [ { "properties": { ... } } ],
  "subTitle": [ { "properties": { ... } } ],
  "divider": [ { "properties": { ... } } ],
  "spacing": [ { "properties": { ... } } ],
  "background": [ { "properties": { ... } } ],
  "padding": [ { "properties": { ... } } ],
  "lockAspect": [ { "properties": { ... } } ],
  "general": [ { "properties": { ... } } ],
  "border": [ { "properties": { ... } } ],
  "dropShadow": [ { "properties": { ... } } ],
  "visualLink": [ { "properties": { ... } } ],
  "visualTooltip": [ { "properties": { ... } } ],
  "stylePreset": [ { "properties": { ... } } ],
  "visualHeader": [ { "properties": { ... } } ],
  "visualHeaderTooltip": [ { "properties": { ... } } ]
}
```

Each key holds an **array** of formatting definition objects. Each item has:
- `selector` (optional) — scope at which formatting applies
- `properties` (required) — the actual formatting values

For most use cases, use a single item with no `selector` (applies globally):
```json
"title": [
  {
    "properties": {
      "show": { "expr": { "Literal": { "Value": "true" } } },
      "text": { "expr": { "Literal": { "Value": "'My Visual Title'" } } }
    }
  }
]
```

---

## Property Value Format

All formatting property values use the **expression wrapper** pattern:

```json
"propertyName": {
  "expr": {
    "Literal": { "Value": "<value>" }
  }
}
```

| Value type | Example |
|---|---|
| String | `{ "expr": { "Literal": { "Value": "'My Title'" } } }` |
| Number | `{ "expr": { "Literal": { "Value": "12D" } } }` |
| Boolean | `{ "expr": { "Literal": { "Value": "true" } } }` |
| Color | `{ "expr": { "Literal": { "Value": "'#FF0000'" } } }` |

> Note: String values require single quotes inside the string e.g. `"'My Title'"`. Numbers use `D` suffix for decimals e.g. `"12D"`.

---

## `title` — Visual Title

```json
"title": [
  {
    "properties": {
      "show": { "expr": { "Literal": { "Value": "true" } } },
      "text": { "expr": { "Literal": { "Value": "'Sales by Category'" } } },
      "fontColor": { "expr": { "Literal": { "Value": "'#252423'" } } },
      "background": { "expr": { "Literal": { "Value": "'#FFFFFF'" } } },
      "alignment": { "expr": { "Literal": { "Value": "'center'" } } },
      "fontSize": { "expr": { "Literal": { "Value": "12D" } } },
      "bold": { "expr": { "Literal": { "Value": "false" } } },
      "italic": { "expr": { "Literal": { "Value": "false" } } },
      "underline": { "expr": { "Literal": { "Value": "false" } } },
      "fontFamily": { "expr": { "Literal": { "Value": "'DIN'" } } },
      "titleWrap": { "expr": { "Literal": { "Value": "true" } } }
    }
  }
]
```

| Property | Type | Description |
|---|---|---|
| `show` | boolean | Show or hide the title |
| `text` | string | Title text content |
| `fontColor` | color string | Title text colour (hex) |
| `background` | color string | Title background colour (hex) |
| `alignment` | string | `'left'`, `'center'`, `'right'` |
| `fontSize` | number (D) | Font size in points |
| `bold` | boolean | Bold text |
| `italic` | boolean | Italic text |
| `underline` | boolean | Underlined text |
| `fontFamily` | string | Font family name |
| `titleWrap` | boolean | Allow title text to wrap |
| `heading` | string | Heading level style |

---

## `subTitle` — Visual Subtitle

Same properties as `title` except no `background` field:

```json
"subTitle": [
  {
    "properties": {
      "show": { "expr": { "Literal": { "Value": "true" } } },
      "text": { "expr": { "Literal": { "Value": "'Filtered by Region'" } } },
      "fontSize": { "expr": { "Literal": { "Value": "10D" } } }
    }
  }
]
```

---

## `background` — Visual Background

```json
"background": [
  {
    "properties": {
      "show": { "expr": { "Literal": { "Value": "true" } } },
      "color": { "expr": { "Literal": { "Value": "'#FFFFFF'" } } },
      "transparency": { "expr": { "Literal": { "Value": "0D" } } }
    }
  }
]
```

| Property | Type | Description |
|---|---|---|
| `show` | boolean | Show background |
| `color` | color string | Background colour (hex) |
| `transparency` | number (D) | 0 = opaque, 100 = fully transparent |

---

## `border` — Visual Border

```json
"border": [
  {
    "properties": {
      "show": { "expr": { "Literal": { "Value": "true" } } },
      "color": { "expr": { "Literal": { "Value": "'#CCCCCC'" } } },
      "radius": { "expr": { "Literal": { "Value": "4D" } } },
      "width": { "expr": { "Literal": { "Value": "1D" } } }
    }
  }
]
```

| Property | Type | Description |
|---|---|---|
| `show` | boolean | Show border |
| `color` | color string | Border colour |
| `radius` | number (D) | Corner radius in pixels |
| `width` | number (D) | Border thickness in pixels |

---

## `padding` — Visual Padding

```json
"padding": [
  {
    "properties": {
      "top": { "expr": { "Literal": { "Value": "8D" } } },
      "bottom": { "expr": { "Literal": { "Value": "8D" } } },
      "left": { "expr": { "Literal": { "Value": "8D" } } },
      "right": { "expr": { "Literal": { "Value": "8D" } } }
    }
  }
]
```

---

## `dropShadow` — Drop Shadow

```json
"dropShadow": [
  {
    "properties": {
      "show": { "expr": { "Literal": { "Value": "true" } } },
      "preset": { "expr": { "Literal": { "Value": "'BottomRight'" } } },
      "color": { "expr": { "Literal": { "Value": "'#000000'" } } },
      "transparency": { "expr": { "Literal": { "Value": "60D" } } },
      "shadowSpread": { "expr": { "Literal": { "Value": "2D" } } },
      "shadowBlur": { "expr": { "Literal": { "Value": "4D" } } },
      "angle": { "expr": { "Literal": { "Value": "45D" } } },
      "shadowDistance": { "expr": { "Literal": { "Value": "4D" } } }
    }
  }
]
```

---

## `divider` — Title Divider Line

```json
"divider": [
  {
    "properties": {
      "show": { "expr": { "Literal": { "Value": "true" } } },
      "color": { "expr": { "Literal": { "Value": "'#CCCCCC'" } } },
      "width": { "expr": { "Literal": { "Value": "1D" } } },
      "style": { "expr": { "Literal": { "Value": "'solid'" } } }
    }
  }
]
```

---

## `spacing` — Title Area Spacing

```json
"spacing": [
  {
    "properties": {
      "customizeSpacing": { "expr": { "Literal": { "Value": "true" } } },
      "spaceBelowTitle": { "expr": { "Literal": { "Value": "4D" } } },
      "spaceBelowSubTitle": { "expr": { "Literal": { "Value": "4D" } } },
      "spaceBelowTitleArea": { "expr": { "Literal": { "Value": "8D" } } }
    }
  }
]
```

---

## `general` — General Container Properties

```json
"general": [
  {
    "properties": {
      "altText": { "expr": { "Literal": { "Value": "'Bar chart showing sales by category'" } } },
      "keepLayerOrder": { "expr": { "Literal": { "Value": "true" } } }
    }
  }
]
```

| Property | Description |
|---|---|
| `x`, `y`, `width`, `height` | Override position (mirrors `position` object) |
| `altText` | Accessibility alt text |
| `keepLayerOrder` | Keep visual on top when selected |
| `allowBinnedLineSample` | Better line chart sampling |
| `allowOverlappingPointsSample` | Better scatter chart sampling |

---

## `visualHeader` — Header Buttons

Controls which buttons appear in the visual header on hover:

```json
"visualHeader": [
  {
    "properties": {
      "show": { "expr": { "Literal": { "Value": "true" } } },
      "showFocusModeButton": { "expr": { "Literal": { "Value": "true" } } },
      "showOptionsMenu": { "expr": { "Literal": { "Value": "true" } } },
      "showFilterRestatementButton": { "expr": { "Literal": { "Value": "false" } } },
      "showDrillDownLevelButton": { "expr": { "Literal": { "Value": "true" } } }
    }
  }
]
```

Available button toggles: `showVisualInformationButton`, `showVisualWarningButton`, `showVisualErrorButton`, `showDrillRoleSelector`, `showDrillUpButton`, `showDrillToggleButton`, `showDrillDownLevelButton`, `showDrillDownExpandButton`, `showPinButton`, `showFilterRestatementButton`, `showFocusModeButton`, `showCopyVisualImageButton`, `showSeeDataLayoutToggleButton`, `showOptionsMenu`, `showCommentButton`, `showTooltipButton`, `showPersonalizeVisualButton`, `showSmartNarrativeButton`, `showSetAlertButton`, `showFollowVisualButton`

---

## `visualTooltip` — Tooltip Formatting

```json
"visualTooltip": [
  {
    "properties": {
      "show": { "expr": { "Literal": { "Value": "true" } } },
      "type": { "expr": { "Literal": { "Value": "'Default'" } } },
      "fontSize": { "expr": { "Literal": { "Value": "11D" } } },
      "background": { "expr": { "Literal": { "Value": "'#FFFFFF'" } } },
      "transparency": { "expr": { "Literal": { "Value": "0D" } } }
    }
  }
]
```

---

## `stylePreset` — Style Preset

Apply a named visual style preset:

```json
"stylePreset": [
  {
    "properties": {
      "name": { "expr": { "Literal": { "Value": "'None'" } } }
    }
  }
]
```

---

## `lockAspect` — Lock Aspect Ratio

```json
"lockAspect": [
  {
    "properties": {
      "show": { "expr": { "Literal": { "Value": "false" } } }
    }
  }
]
```

---

## `visualLink` — Visual Action/Link

Add a clickable action to the visual (bookmark, URL, drillthrough):

```json
"visualLink": [
  {
    "properties": {
      "show": { "expr": { "Literal": { "Value": "true" } } },
      "type": { "expr": { "Literal": { "Value": "'WebUrl'" } } },
      "webUrl": { "expr": { "Literal": { "Value": "'https://example.com'" } } },
      "tooltip": { "expr": { "Literal": { "Value": "'Click to open'" } } }
    }
  }
]
```

Available `type` values: `'WebUrl'`, `'BookmarkNav'`, `'PageNav'`, `'Drillthrough'`
