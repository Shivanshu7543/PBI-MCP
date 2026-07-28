# Definition Properties (`definition.pbir`) — Deep Dive

Schema: `https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json`

File location: `definition.pbir` (at the report item root, **not** inside `definition/`)

The `definition.pbir` file holds metadata about the overall file structure and — critically — the reference to the semantic model this report is bound to. **This file is required.**

---

## Structure

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
  "version": "4.0",
  "datasetReference": {
    "byConnection": {
      "connectionString": "semanticmodelid=<SEMANTIC_MODEL_GUID>"
    }
  }
}
```

---

## Required Fields

| Field | Type | Description |
|---|---|---|
| `$schema` | string | Must match `definitionProperties/2.x.x/schema.json` |
| `version` | string | Version of the report artifact / `.pbir` file format |
| `datasetReference` | object | The semantic model binding (see below) |

`additionalProperties: false`.

---

## `datasetReference` (DatasetReference)

Must have **exactly one** of `byPath` or `byConnection`.

| Property | Use case |
|---|---|
| `byConnection` | LiveConnect — remote semantic model in the Fabric service |
| `byPath` | Local semantic model definition in the same project |

### `byConnection` (ReportDatasetReferenceByConnection)

```json
"datasetReference": {
  "byConnection": {
    "connectionString": "semanticmodelid=3a1b...guid"
  }
}
```

- `connectionString` (**required**): points to the remote semantic model hosted in Microsoft Fabric.
- **This is the pattern the Fabric REST API requires** — every report created via the API must supply a valid `connectionString` of the form `semanticmodelid=<GUID>`.
- Type can be `object` or `null`, but for a working report it must be a populated object.
- Connections to non-Fabric Analysis Services models must instead use `byPath` to a semantic model containing a `modelReference.json`.

### `byPath` (ReportDatasetReferenceByPath)

```json
"datasetReference": {
  "byPath": {
    "path": "../MyModel.SemanticModel"
  }
}
```

- `path` (**required**): relative path (using `/`) from `definition.pbir` to the target semantic model artifact folder.

---

## Key Rules

1. Exactly one of `byPath` / `byConnection` must be populated — never both, never neither.
2. For Fabric REST API report creation, always use `byConnection` with `connectionString = "semanticmodelid=<GUID>"`.
3. This file lives at the **item root**, alongside the `definition/` folder and `.platform` file.

---

## Minimal Valid File (LiveConnect)

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
  "version": "4.0",
  "datasetReference": {
    "byConnection": {
      "connectionString": "semanticmodelid=00000000-0000-0000-0000-000000000000"
    }
  }
}
```

---

## Related Knowledge Base Files

- `07_report.md` — `report.json`
- `08_report_version.md` — `version.json`
- `05_page_order.md` / `06_page.md` — pages
