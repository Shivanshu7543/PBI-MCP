# Bookmarks Metadata (`bookmarks.json`) — Deep Dive

Schema: `https://developer.microsoft.com/json-schemas/fabric/item/report/definition/bookmarksMetadata/1.0.0/schema.json`

File location: `definition/bookmarks/bookmarks.json`

Defines the **order** of bookmarks and which bookmarks belong to **groups**. The individual bookmark state lives in separate `<name>.bookmark.json` files (see `12_bookmark.md`).

---

## Structure

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/bookmarksMetadata/1.0.0/schema.json",
  "items": [
    { "name": "Bookmark1" },
    {
      "name": "Group1",
      "displayName": "Sales Views",
      "children": ["Bookmark2", "Bookmark3"]
    }
  ]
}
```

### Required Fields

| Field | Type | Description |
|---|---|---|
| `$schema` | string | The bookmarksMetadata 1.0.0 schema URL |
| `items` | array | Ordered list of bookmarks and bookmark groups |

`additionalProperties: false`. The **order** of `items` is the display order in the bookmarks pane.

---

## `items` entries

Each entry is either a **standalone bookmark** or a **bookmark group**.

### SingleBookmarkMetadata (standalone)

| Field | Required | Description |
|---|---|---|
| `name` | **yes** | Name of a standalone bookmark; must match a `<name>.bookmark.json` and be unique across the report |

```json
{ "name": "Bookmark1" }
```

### BookmarkGroupMetadata (group)

**Required**: `name`, `displayName`, `children`.

| Field | Type | Description |
|---|---|---|
| `name` | string | Unique group name across the report |
| `displayName` | string | Group display name shown in the pane |
| `children` | string[] | Ordered bookmark names belonging to this group |

```json
{
  "name": "Group1",
  "displayName": "Sales Views",
  "children": ["Bookmark2", "Bookmark3"]
}
```

> Bookmarks referenced in a group's `children` should **not** also appear as standalone `items`. Each child name must correspond to its own `<name>.bookmark.json`.

---

## Minimal Valid File

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/bookmarksMetadata/1.0.0/schema.json",
  "items": [
    { "name": "Bookmark1" }
  ]
}
```

---

## Folder Layout Recap

```
definition/bookmarks/
  bookmarks.json                 → this file (order + groups)
  Bookmark1.bookmark.json        → 12_bookmark.md
  Bookmark2.bookmark.json
  Bookmark3.bookmark.json
```

---

## Related Knowledge Base Files

- `12_bookmark.md` — individual `bookmark.json` (explorationState, options)
