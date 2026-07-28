# Report (`report.json`) — Deep Dive

Schema: `https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/3.3.0/schema.json`

File location: `definition/report.json`

Top-level file defining the report: its theme, report-wide filters, formatting, settings, custom visuals, and resources.

---

## Structure

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/3.3.0/schema.json",
  "themeCollection": { ... },
  "filterConfig": { ... },
  "objects": { ... },
  "reportSource": "Default",
  "publicCustomVisuals": [ ... ],
  "resourcePackages": [ ... ],
  "organizationCustomVisuals": [ ... ],
  "annotations": [ ... ],
  "dataSourceVariables": "...",
  "settings": { ... },
  "slowDataSourceSettings": { ... }
}
```

---

## Required Fields

| Field | Type | Description |
|---|---|---|
| `$schema` | string | Must be the report 3.3.0 schema URL |
| `themeCollection` | object | Base and/or custom theme for the report |

Only `$schema` and `themeCollection` are required. Everything else is optional.

---

## `themeCollection` (required)

```json
"themeCollection": {
  "baseTheme": {
    "name": "CY24SU10",
    "reportVersionAtImport": { "visual": "2.10.0", "page": "2.1.0", "report": "3.3.0" },
    "type": "SharedResources"
  },
  "customTheme": {
    "name": "MyCustomTheme",
    "reportVersionAtImport": { "visual": "2.10.0", "page": "2.1.0", "report": "3.3.0" },
    "type": "RegisteredResources"
  }
}
```

| Field | Description |
|---|---|
| `baseTheme` | The built-in monthly-release theme (ThemeMetadata) |
| `customTheme` | A custom theme applied on top of the base; missing props fall back to base |

### ThemeMetadata (required: name, reportVersionAtImport, type)

| Field | Description |
|---|---|
| `name` | Theme name |
| `reportVersionAtImport` | `ThemeVersion` — max `visual`, `page`, `report` versions when theme was added (all three required, pattern `x.y.z`) |
| `type` | `RegisteredResources` (external file) or `SharedResources` (bundled with Power BI) |

---

## `filterConfig` (report-level filters)

Filters applied to the **entire** report — every page and every visual. References `filterConfiguration/1.3.0`. Same structure used at page and visual level. *(See the filters KB file once added.)*

---

## `reportSource` — How the report was created (enum)

`Default`, `SharePoint`, `Teams`, `QuickCreate`, `EmbedQuickCreate`, `Datamart`, `DataExplore`.
Use `Default` for a normal blank report.

---

## `objects` — Report Formatting (ReportFormattingObjects)

Report-wide formatting. Two objects supported:

| Object | Properties | Purpose |
|---|---|---|
| `outspacePane` | `expanded`, `visible` | Default state of the filter pane |
| `section` | `verticalAlignment` | Default vertical alignment for pages |

```json
"objects": {
  "outspacePane": [
    { "properties": { "expanded": {}, "visible": {} } }
  ]
}
```

Each entry may include a `selector` (scope/highlight rules) plus required `properties`.

---

## Custom Visuals

| Field | Type | Description |
|---|---|---|
| `publicCustomVisuals` | string[] | Names of AppSource custom visuals used |
| `organizationCustomVisuals` | array | Org-approved custom visuals — each `{ name, path, disabled? }` (name + path required) |

---

## `resourcePackages` — Bundled Resources

Array of `ResourcePackage` (required: `items`, `name`, `type`).

```json
"resourcePackages": [
  {
    "name": "SharedResources",
    "type": "RegisteredResources",
    "disabled": false,
    "items": [
      { "name": "CY24SU10", "path": "BaseThemes/CY24SU10.json", "type": "BaseTheme" }
    ]
  }
]
```

- **ResourcePackageType**: `CustomVisual`, `RegisteredResources`, `SharedResources`, `OrganizationalStoreCustomVisual`
- **ResourcePackageItem** (required: `name`, `path`, `type`)
- **ResourcePackageItemType**: `CustomVisualJavascript`, `CustomVisualsCss`, `CustomVisualScreenshot`, `CustomVisualIcon`, `CustomVisualWatermark`, `CustomVisualMetadata`, `Image`, `ShapeMap`, `CustomTheme`, `BaseTheme`, `DashboardTheme`, `DashboardBaseTheme`, `HighContrastTheme`, `AppNavigation`, `AppTheme`, `AppBaseTheme`

---

## `annotations`

Array of `{ name, value }` (both required) — comments, readme, custom metadata.

---

## `dataSourceVariables`

String holding the state of DirectQuery data-source variables to override when rendering. Not related to semantic-model M parameters.

---

## `settings` — ExplorationSettings

Report behaviour toggles. All optional booleans unless noted:

| Setting | Purpose |
|---|---|
| `isPersistentUserStateDisabled` | Don't save viewers' slicer/filter changes |
| `hideVisualContainerHeader` | Hide visual headers in view mode |
| `useStylableVisualContainerHeader` | Use new formattable visual header |
| `exportDataMode` | `AllowSummarized` / `AllowSummarizedAndUnderlying` / `None` |
| `isReportAnnotationsDisabled` | Disable commenting |
| `defaultFilterActionIsDataFilter` | Selecting data points filters (not highlights) other visuals |
| `defaultDrillFilterOtherVisuals` | Drilling one visual filters others |
| `useCrossReportDrillthrough` | Allow drill-through from other reports |
| `allowChangeFilterTypes` | Allow changing filter type in view mode |
| `allowInlineExploration` | Allow personalising visuals in view mode |
| `useEnhancedTooltips` | Better visual tooltips |
| `useScaledTooltips` | Scale tooltips with canvas zoom |
| `filterPaneHiddenInEditMode` | Hide filter pane |
| `disableFilterPaneSearch` | Disable filter-pane search bar |
| `pagesPosition` | Page navigator location — `PagesPane` or `Bottom` |
| `allowAutomatedInsightsNotification` | Background insights on refresh |
| `useDefaultAggregateDisplayName` | Show default aggregate in display names |
| `enableDeveloperMode` | Dev mode for private custom visuals |
| `pauseQueries` | Pause queries while editing (slow sources) |
| `queryLimitOption` | `None`/`Shared`/`Premium`/`SQLServerAS`/`AzureAS`/`Custom`/`Auto` |
| `customMemoryLimit` | Memory limit string (when `queryLimitOption`=`Custom`) |
| `customTimeoutLimit` | Timeout limit string (when Custom) |
| `fieldParameterReportSettings` | `{ skipHierarchyLevelPersistence }` |
| `defaultDataExplorePerspective` | Default perspective name |
| `locale` | Report-specific locale, overrides browser/OS |
| `defaultDisplayUnitsToNone` | Default display units to none |

---

## `slowDataSourceSettings` — ExplorationSlowDataSourceSettings

Adds apply buttons for slow data sources. All optional booleans:

| Setting | Purpose |
|---|---|
| `isCrossHighlightingDisabled` | Disable cross-highlights |
| `isSlicerSelectionsButtonEnabled` | Add Apply button to slicers |
| `isFilterSelectionsButtonEnabled` | Add Apply button to filters |
| `isFieldWellButtonEnabled` | Add Apply button to field changes |
| `isApplyAllButtonEnabled` | Add a single Apply-all button |

---

## Minimal Valid Report

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/3.3.0/schema.json",
  "themeCollection": {
    "baseTheme": {
      "name": "CY24SU10",
      "reportVersionAtImport": { "visual": "2.10.0", "page": "2.1.0", "report": "3.3.0" },
      "type": "SharedResources"
    }
  }
}
```

---

## Related Knowledge Base Files

- `05_page_order.md` — `pages.json` (page order + active page)
- `06_page.md` — `page.json`
- `08_report_version.md` — `version.json` (definition version)
- `09_data_connection.md` — `definition.pbir` (semantic-model binding)
