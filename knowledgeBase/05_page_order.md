# Pages Metadata (`pages.json`) — Deep Dive

Schema: `https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.1.0/schema.json`

File location: `definition/pages/pages.json`

This file defines report-wide information about pages: their order and which page opens by default.

---

## Structure

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.1.0/schema.json",
  "pageOrder": ["ReportSection1", "ReportSection2"],
  "activePageName": "ReportSection1",
  "landingPageName": "ReportSection1"
}
```

---

## Fields

| Field | Required | Type | Description |
|---|---|---|---|
| `$schema` | **yes** | string | Must be the pagesMetadata 1.1.0 schema URL |
| `pageOrder` | no | string[] | Order in which pages render, by page **name** (not display name) |
| `activePageName` | no | string | Page the report opens on by default |
| `landingPageName` | no | string | Forces the report to always open on this page for all users |

---

## `pageOrder`
- Array of page **names** (the `name` field from each `page.json`, not the display name).
- Controls the left-to-right tab order of pages.
- Rules:
  - Names in this list without a matching `page.json` are **ignored**.
  - Pages that have a definition but are **not** in this list are ordered by display name and appended to the end.
- If omitted entirely, all pages are ordered by display name.

```json
"pageOrder": ["Overview", "Sales", "Details"]
```

---

## `activePageName`
- The page the report opens on when first loaded.
- Value is the page **name**, not display name.
- If omitted, the report opens on the first page per `pageOrder`.
- If both `activePageName` and `landingPageName` are set, **`landingPageName` wins**.

---

## `landingPageName`
- Forces **all users** to always open on this page, overriding `activePageName`.
- Value is the page **name**.
- Use for a mandatory intro/home page.

---

## Minimal Valid Example (single page)

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.1.0/schema.json",
  "pageOrder": ["ReportSection1"],
  "activePageName": "ReportSection1"
}
```

> Only `$schema` is strictly required, but always include `pageOrder` and `activePageName` for predictable behaviour.
