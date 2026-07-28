# Version Metadata (`version.json`) — Deep Dive

Schema: `https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json`

File location: `definition/version.json`

Declares the version of the report **definition** file format.

---

## Structure

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json",
  "version": "1.0.0"
}
```

---

## Fields

| Field | Required | Type | Description |
|---|---|---|---|
| `$schema` | **yes** | string | Must be the versionMetadata 1.0.0 schema URL |
| `version` | **yes** | string | Report definition version, `major.minor.patch` |

`additionalProperties: false` — only these two fields are allowed.

---

## `version` format rules

Pattern: `^[1-9][0-9]*\.(0|[1-9][0-9]*)\.0$`

- **major**: `>= 1` (cannot be 0)
- **minor**: `>= 0`
- **patch**: always `0`

Examples valid: `1.0.0`, `2.3.0`, `10.0.0`
Examples invalid: `0.1.0` (major must be ≥1), `1.0.1` (patch must be 0)

---

## Minimal Valid File

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json",
  "version": "1.0.0"
}
```
