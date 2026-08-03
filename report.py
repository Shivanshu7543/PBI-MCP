import asyncio
import base64
import json
import time
from pathlib import Path

import httpx
from azure.identity import DefaultAzureCredential
from fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Automatic token acquisition (Azure CLI locally, Managed Identity in Azure)
# ---------------------------------------------------------------------------
_credential = DefaultAzureCredential()
_POWERBI_SCOPE = "https://analysis.windows.net/powerbi/api/.default"

# In-memory token cache — avoids calling `az` on every API request.
# The token is refreshed only when it is within _TOKEN_REFRESH_BEFORE_EXPIRY
# seconds of expiring (default: 5 minutes).
_cached_token: str = ""
_token_expires_on: float = 0.0
_TOKEN_REFRESH_BEFORE_EXPIRY: int = 300  # seconds


def _get_token() -> str:
    """Return a valid Power BI bearer token.

    Uses DefaultAzureCredential which tries (in order):
    1. Environment variables (AZURE_CLIENT_ID / AZURE_CLIENT_SECRET / AZURE_TENANT_ID)
    2. Workload Identity (AKS)
    3. Managed Identity (Azure VMs, App Service, Container Apps, …)
    4. Azure CLI  (``az login`` — works on local dev machines)
    5. Azure PowerShell

    The token is cached in memory and only re-acquired when it is within
    5 minutes of expiring, minimising subprocess calls to the Azure CLI.
    """
    global _cached_token, _token_expires_on
    if not _cached_token or time.time() >= _token_expires_on - _TOKEN_REFRESH_BEFORE_EXPIRY:
        access_token = _credential.get_token(_POWERBI_SCOPE)
        _cached_token = access_token.token
        _token_expires_on = float(access_token.expires_on)
    return _cached_token


mcp = FastMCP("PowerBI Reports")


# ---------------------------------------------------------------------------
# MCP Prompt — workflow guide loaded by the LLM client at session start
# ---------------------------------------------------------------------------

@mcp.prompt()
def powerbi_workflow_guide() -> str:
    """
    Complete workflow guide for building Power BI reports via MCP.
    Read this prompt at the start of every session before using any tool.
    """
    return """
# Power BI MCP — Workflow Guide

Always read the relevant knowledge-base resource BEFORE calling a tool.
The resources contain the exact JSON structures, role names and constraints
that Power BI enforces.  Skipping them leads to silent errors or blank visuals.

---

## Step 1 — Discover the workspace
- Tool: `list_semantic_models(workspace_id)` → find semantic_model_id
- Tool: `list_reports(workspace_id)` → find existing report_ids

---

## Step 2 — Create a report
- Resource to read first: `powerbi://knowledge_base/semantic_model`
  (explains datasetReference / connection string format)
- Resource to read first: `powerbi://knowledge_base/report_version`
  (explains the PBIR-Legacy version field)
- Tool: `create_empty_report(workspace_id, display_name, semantic_model_id)`

---

## Step 3 — Add / manage pages
- Resource to read first: `powerbi://knowledge_base/page`
  (canvas size, displayOption values, page structure)
- Resource to read first: `powerbi://knowledge_base/page_order`
  (ordinal rules, active page)
- Tools: `list_pages`, `add_page`, `update_page`, `delete_page`, `reorder_pages`

---

## Step 4 — Add visuals
- Resource to read first: `powerbi://visuals/list`
  (all 41 valid visual type names)
- Resource to read first: `powerbi://knowledge_base/visuals`
  (what a visual is, canvas defaults, placeholder rules)
- Resource to read first: `powerbi://visuals/{visual_type}`
  (full JSON schema for the specific visual you are adding)
- Tool: `add_visual(workspace_id, report_id, page_name, visual_type, x, y, width, height, title)`

---

## Step 5 — Bind data fields to visuals
- Resource to read first: `powerbi://knowledge_base/field_wells`
  (EXACT role key names per visual type — Category, Y, Field, Values, Series, X, Size…)
- Resource to read first: `powerbi://knowledge_base/fields`
  (prototypeQuery / queryState structure, Column vs Measure expression format)
- Resource to read first: `powerbi://knowledge_base/fields_and_measures`
  (DAX expression syntax, how columns and measures differ)
- Tool: `list_semantic_model_columns(workspace_id, semantic_model_id)` → discover table/field names
- Tool: `add_field_to_visual(workspace_id, report_id, page_name, visual_id, table_name, field_name, role, is_measure)`

Role name quick-reference (from field_wells KB):
  clusteredBarChart / barChart  → Category (column), Y (measure), Series (column)
  lineChart                     → Category (column), Y (measure), Series (column)
  pieChart / donutChart         → Category (column), Y (measure)
  cardVisual                    → Values (measure)
  tableEx / matrixVisual        → Values (column or measure)
  slicer                        → Field (column)
  scatterChart                  → X (measure), Y (measure), Size (measure), Details (column)
  kpi                           → Value (measure), Goal (measure), TrendAxis (column)

---

## Step 6 — Add filters
- Resource to read first: `powerbi://knowledge_base/filters`
  (filter types, JSON structure for Categorical / Advanced filters)
- Tools: `list_filters`, `add_categorical_filter`, `remove_filter`

---

## Step 7 — Add DAX measures
- Resource to read first: `powerbi://knowledge_base/dax_measures`
  (reportExtensions.json structure, entity/measure schema)
- Resource to read first: `powerbi://knowledge_base/fields_and_measures`
  (DAX expression syntax)
- Tools: `list_dax_measures`, `add_dax_measure`, `update_dax_measure`, `delete_dax_measure`

---

## Step 8 — Add bookmarks
- Resource to read first: `powerbi://knowledge_base/bookmark`
  (bookmark JSON structure, explorationState format)
- Resource to read first: `powerbi://knowledge_base/bookmarks_pane`
  (bookmark groups and ordering)
- Tools: `list_bookmarks`, `add_bookmark`, `delete_bookmark`

---

## Step 9 — Format visuals
- Resource to read first: `powerbi://knowledge_base/format_pane`
  (title, colours, background, borders, shadow, tooltips)
- Resource to read first: `powerbi://visuals/{visual_type}`
  (visual-specific formatting objects)
- Tool: `update_visual_title`, `update_visual_position`

---

## Golden rules
1. Always read the relevant resource(s) BEFORE calling a tool.
2. Use `list_pages` to get the internal page_name before any page/visual operation.
3. Use `list_visuals` to get visual_id before any field-binding or position update.
4. Role names in `add_field_to_visual` must match EXACTLY what `field_wells` KB says.
5. Set `is_measure=True` for DAX measures and implicit numeric aggregates (Σ symbol).
6. Set `is_measure=False` for text/date/key columns (no Σ symbol).
"""


# ---------------------------------------------------------------------------
# Visual knowledge base – MCP Resources
# ---------------------------------------------------------------------------

_VISUALS_DIR = Path(__file__).parent / "visuals"
_KB_DIR = Path(__file__).parent / "knowledgeBase"


@mcp.resource("powerbi://knowledge_base/visuals")
def kb_visual_schema() -> str:
    """Visuals 1 of 4: What a visual is and its basic parts."""
    return (_KB_DIR / "01_charts_basics.md").read_text(encoding="utf-8")


@mcp.resource("powerbi://knowledge_base/fields")
def kb_query_and_projections() -> str:
    """Visuals 2 of 4: The Fields well — which columns and measures a visual shows."""
    return (_KB_DIR / "02_charts_data.md").read_text(encoding="utf-8")


@mcp.resource("powerbi://knowledge_base/format_pane")
def kb_formatting() -> str:
    """Visuals 3 of 4: The Format pane — title, colours, background, borders, shadow, tooltips."""
    return (_KB_DIR / "03_charts_look.md").read_text(encoding="utf-8")


@mcp.resource("powerbi://knowledge_base/field_wells")
def kb_visual_roles() -> str:
    """Visuals 4 of 4: Field wells — where fields go for each visual (Axis, Legend, Values, slicer Field...)."""
    return (_KB_DIR / "04_charts_fields.md").read_text(encoding="utf-8")


@mcp.resource("powerbi://knowledge_base/page_order")
def kb_pages_metadata() -> str:
    """Pages: Page order and which page opens first."""
    return (_KB_DIR / "05_page_order.md").read_text(encoding="utf-8")


@mcp.resource("powerbi://knowledge_base/page")
def kb_page() -> str:
    """Pages: A report page — canvas size, page filters, format and visual interactions."""
    return (_KB_DIR / "06_page.md").read_text(encoding="utf-8")


@mcp.resource("powerbi://knowledge_base/report")
def kb_report() -> str:
    """Report: The report — theme, report-level filters and report settings."""
    return (_KB_DIR / "07_report.md").read_text(encoding="utf-8")


@mcp.resource("powerbi://knowledge_base/report_version")
def kb_version_metadata() -> str:
    """Report: The report definition version number."""
    return (_KB_DIR / "08_report_version.md").read_text(encoding="utf-8")


@mcp.resource("powerbi://knowledge_base/semantic_model")
def kb_definition_properties() -> str:
    """Data: The semantic model the report is connected to (live connection)."""
    return (_KB_DIR / "09_data_connection.md").read_text(encoding="utf-8")


@mcp.resource("powerbi://knowledge_base/filters")
def kb_filters() -> str:
    """Data: Filters — the Filters pane at report, page and visual level."""
    return (_KB_DIR / "10_filters.md").read_text(encoding="utf-8")


@mcp.resource("powerbi://knowledge_base/fields_and_measures")
def kb_semantic_query() -> str:
    """Data: How columns, measures and DAX expressions are written (used everywhere)."""
    return (_KB_DIR / "11_data_fields.md").read_text(encoding="utf-8")


@mcp.resource("powerbi://knowledge_base/bookmark")
def kb_bookmark() -> str:
    """Bookmarks: A bookmark — a saved view of the report."""
    return (_KB_DIR / "12_bookmark.md").read_text(encoding="utf-8")


@mcp.resource("powerbi://knowledge_base/bookmarks_pane")
def kb_bookmarks_metadata() -> str:
    """Bookmarks: The Bookmarks pane — bookmark order and groups."""
    return (_KB_DIR / "13_bookmark_list.md").read_text(encoding="utf-8")


@mcp.resource("powerbi://knowledge_base/dax_measures")
def kb_report_extensions_dax() -> str:
    """Data: DAX measures — report-level measures you add with DAX."""
    return (_KB_DIR / "14_dax_measures.md").read_text(encoding="utf-8")


@mcp.resource("powerbi://visuals/knowledge_base")
def get_visual_knowledge_base() -> str:
    """Get the full visual knowledge base: placeholder rules, canvas defaults,
    auto-layout tips, and descriptions of all 41 visual types with categories."""
    path = _VISUALS_DIR / "knowledge_base.md"
    return path.read_text(encoding="utf-8")


@mcp.resource("powerbi://visuals/list")
def list_visual_types() -> str:
    """List all available Power BI visual types in the knowledge base."""
    types = sorted(p.stem for p in _VISUALS_DIR.glob("*.json"))
    return json.dumps({"visualTypes": types, "count": len(types)}, indent=2)


@mcp.resource("powerbi://visuals/{visual_type}")
def get_visual_schema(visual_type: str) -> str:
    """Get the full schema/definition for a specific Power BI visual type.

    Args:
        visual_type: The visual type name e.g. barChart, lineChart, cardVisual,
                     clusteredColumnChart, tableEx, slicer, pieChart, kpi, etc.
                     Call powerbi://visuals/list to see all available types.
    """
    path = _VISUALS_DIR / f"{visual_type}.json"
    if not path.exists():
        available = sorted(p.stem for p in _VISUALS_DIR.glob("*.json"))
        return json.dumps({
            "error": f"Visual type '{visual_type}' not found.",
            "available": available,
        }, indent=2)
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Helpers to build a minimal PBIR report definition
# ---------------------------------------------------------------------------


def _b64(data: dict | str) -> str:
    """Encode a dict (as JSON) or a plain string to a base64 string."""
    text = json.dumps(data, indent=2) if isinstance(data, dict) else data
    return base64.b64encode(text.encode()).decode()


def _build_definition(display_name: str, semantic_model_id: str) -> dict:
    """Return the CreateReport `definition` object using PBIR-Legacy format.

    Matches the structure shown in the official Fabric REST API docs:
      - definition.pbir  – report properties with required datasetReference
      - report.json      – PBIR-Legacy single-file report (one blank page)
      - .platform        – Fabric item metadata

    Fabric schema enforces that datasetReference must be present in
    definition.pbir with byConnection populated.
    """
    # ── definition.pbir ──────────────────────────────────────────────────────
    definition_pbir: dict = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
        "version": "4.0",
        "datasetReference": {
            "byConnection": {
                "connectionString": f"semanticmodelid={semantic_model_id}"
            }
        },
    }

    # ── report.json  (PBIR-Legacy) ────────────────────────────────────────────
    # config / filters are double-encoded JSON strings as required by the format
    report_json = {
        "config": json.dumps({}),
        "filters": json.dumps([]),
        "sections": [
            {
                "name": "ReportSection",
                "displayName": "Page 1",
                "filters": json.dumps([]),
                "ordinal": 0,
                "visualContainers": [],
                "config": json.dumps({}),
                "displayOption": 1,
                "height": 720.0,
                "width": 1280.0,
            }
        ],
    }

    # ── .platform ─────────────────────────────────────────────────────────────
    platform = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata": {
            "type": "Report",
            "displayName": display_name,
        },
        "config": {
            "version": "2.0",
            "logicalId": "00000000-0000-0000-0000-000000000000",
        },
    }

    return {
        "format": "PBIR-Legacy",
        "parts": [
            {
                "path": "definition.pbir",
                "payload": _b64(definition_pbir),
                "payloadType": "InlineBase64",
            },
            {
                "path": "report.json",
                "payload": _b64(report_json),
                "payloadType": "InlineBase64",
            },
            {
                "path": ".platform",
                "payload": _b64(platform),
                "payloadType": "InlineBase64",
            },
        ],
    }


async def _poll_lro(client: httpx.AsyncClient, operation_url: str, retry_after: int, headers: dict) -> dict:
    """Poll a Fabric long-running operation until it completes."""
    while True:
        await asyncio.sleep(max(retry_after, 2))
        resp = await client.get(operation_url, headers=headers)
        if resp.status_code != 200:
            return {"error": f"LRO polling failed with status {resp.status_code}", "details": resp.text}
        body = resp.json()
        status = body.get("status", "").lower()
        if status in ("succeeded", "completed"):
            # Fetch the final resource if a Location header was returned
            result_url = resp.headers.get(
                "Location") or body.get("resourceLocation")
            if result_url:
                final = await client.get(result_url, headers=headers)
                return final.json() if final.status_code == 200 else body
            return body
        if status in ("failed", "cancelled"):
            return {"error": f"LRO ended with status '{status}'", "details": body}
        # Still running – use Retry-After if present
        retry_after = int(resp.headers.get("Retry-After", retry_after))


# ---------------------------------------------------------------------------
# MCP tool
# ---------------------------------------------------------------------------

@mcp.tool()
async def create_empty_report(
    workspace_id: str,
    display_name: str,
    semantic_model_id: str,
    description: str = "",
    folder_id: str = "",
    sensitivity_label_id: str = "",
    sensitivity_label_apply_strategy: str = "ApplyOrFail",
) -> dict:
    """Create an empty Power BI report in a Fabric workspace.

    Uses PBIR-Legacy format (definition.pbir + report.json + .platform).

    IMPORTANT: Fabric's schema requires datasetReference in definition.pbir,
    so a semantic_model_id is mandatory. Use list_semantic_models to find
    available semantic model IDs in the workspace.
    Use connect_report_to_semantic_model to rebind to a different model later.

    Calls POST https://api.fabric.microsoft.com/v1/workspaces/{workspaceId}/reports.
    Supports long-running operations (LRO) – automatically polls until done.

    Args:
        workspace_id: UUID of the Fabric workspace.
        display_name: Display name for the new report (must be unique in workspace).
        semantic_model_id: UUID of the semantic model to bind the report to.
                           Use list_semantic_models to discover available IDs.
        description: Optional description (max 256 characters).
        folder_id: Optional UUID of the folder to create the report in.
        sensitivity_label_id: Optional UUID of a sensitivity label to apply.
        sensitivity_label_apply_strategy: 'ApplyOrFail' (default) or 'Ignore'.

    Returns:
        The created Report object including the report 'id'.
    """
    url = f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/reports"

    auth_headers = {
        "Authorization": f"Bearer {_get_token()}",
        "Content-Type": "application/json",
    }

    payload: dict = {
        "displayName": display_name,
        "definition": _build_definition(display_name, semantic_model_id),
    }
    if description:
        payload["description"] = description
    if folder_id:
        payload["folderId"] = folder_id
    if sensitivity_label_id:
        payload["sensitivityLabelSettings"] = {
            "labelId": sensitivity_label_id,
            "sensitivityLabelApplyStrategy": sensitivity_label_apply_strategy,
        }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(url, headers=auth_headers, json=payload)

        # 201 Created – immediate success
        if response.status_code == 201:
            return response.json()

        # 202 Accepted – long-running operation
        if response.status_code == 202:
            operation_url = response.headers.get(
                "Location") or response.headers.get("x-ms-operation-id")
            if not operation_url:
                return {"error": "202 returned but no Location/operation URL in headers"}
            retry_after = int(response.headers.get("Retry-After", 5))
            return await _poll_lro(client, operation_url, retry_after, {"Authorization": f"Bearer {_get_token()}"})

        # 429 Too Many Requests
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After", "unknown")
            return {"error": "Rate limit exceeded", "retry_after_seconds": retry_after}

        # All other errors
        try:
            error_body = response.json()
        except Exception:
            error_body = response.text
        return {"error": f"Request failed with status {response.status_code}", "details": error_body}


@mcp.tool()
async def connect_report_to_semantic_model(
    workspace_id: str,
    report_id: str,
    semantic_model_id: str,
) -> dict:
    """Bind an existing Power BI report to a semantic model.

    Step 2 of 2: Updates the report's definition.pbir to point at the given
    semantic model. Use the 'id' returned by create_empty_report as report_id.

    Calls POST https://api.fabric.microsoft.com/v1/workspaces/{workspaceId}/reports/{reportId}/updateDefinition.
    Supports long-running operations (LRO) – automatically polls until done.

    Args:
        workspace_id: UUID of the Fabric workspace.
        report_id: UUID of the report to update (returned by create_empty_report).
        semantic_model_id: UUID of the semantic model to bind the report to.

    Returns:
        Success confirmation or LRO result from the Fabric API.
    """
    url = (
        f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}"
        f"/reports/{report_id}/updateDefinition"
    )

    auth_headers = {
        "Authorization": f"Bearer {_get_token()}",
        "Content-Type": "application/json",
    }

    # Only update definition.pbir – other parts are left unchanged
    definition_pbir = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
        "version": "4.0",
        "datasetReference": {
            "byConnection": {
                "connectionString": f"semanticmodelid={semantic_model_id}"
            }
        },
    }

    payload = {
        "definition": {
            "parts": [
                {
                    "path": "definition.pbir",
                    "payload": _b64(definition_pbir),
                    "payloadType": "InlineBase64",
                }
            ]
        }
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(url, headers=auth_headers, json=payload)

        # 200 No Content – immediate success
        if response.status_code in (200, 204):
            return {"status": "success", "report_id": report_id, "semantic_model_id": semantic_model_id}

        # 202 Accepted – long-running operation
        if response.status_code == 202:
            operation_url = response.headers.get(
                "Location") or response.headers.get("x-ms-operation-id")
            if not operation_url:
                return {"error": "202 returned but no Location/operation URL in headers"}
            retry_after = int(response.headers.get("Retry-After", 5))
            result = await _poll_lro(
                client, operation_url, retry_after,
                {"Authorization": f"Bearer {_get_token()}"}
            )
            return result

        # 429 Too Many Requests
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After", "unknown")
            return {"error": "Rate limit exceeded", "retry_after_seconds": retry_after}

        try:
            error_body = response.json()
        except Exception:
            error_body = response.text
        return {"error": f"Request failed with status {response.status_code}", "details": error_body}



@mcp.tool()
async def list_workspaces() -> dict:
    """List all Power BI workspaces user have access

    Calls GET https://api.fabric.microsoft.com/v1/workspaces.

    Args: 

    Returns:
        List of workspaces with id, name.
    """
    url = f"https://api.fabric.microsoft.com/v1/workspaces"
    headers = {"Authorization": f"Bearer {_get_token()}"}

    results = []
    async with httpx.AsyncClient(timeout=30) as client:
        while url:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 429:
                return {"error": "Rate limit exceeded", "retry_after_seconds": resp.headers.get("Retry-After", "unknown")}
            if resp.status_code != 200:
                try:
                    err = resp.json()
                except Exception:
                    err = resp.text
                return {"error": f"Request failed with status {resp.status_code}", "details": err}
            body = resp.json()
            for r in body.get("value", []):
                results.append({
                    "id": r.get("id"),
                    "displayName": r.get("displayName")
                })
            url = body.get("continuationUri")
    return {"reports": results, "count": len(results)}



@mcp.tool()
async def list_semantic_models(
    workspace_id: str,
) -> dict:
    """List all semantic models in a Fabric workspace.

    Use this BEFORE create_empty_report to discover available semantic model IDs.

    Calls GET https://api.fabric.microsoft.com/v1/workspaces/{workspaceId}/semanticModels.

    Args:
        workspace_id: UUID of the Fabric workspace.

    Returns:
        A list of semantic models with their 'id', 'displayName', and 'description'.
    """
    url = f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/semanticModels"
    headers = {
        "Authorization": f"Bearer {_get_token()}",
    }

    results = []
    async with httpx.AsyncClient(timeout=30) as client:
        while url:
            response = await client.get(url, headers=headers)

            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After", "unknown")
                return {"error": "Rate limit exceeded", "retry_after_seconds": retry_after}

            if response.status_code != 200:
                try:
                    error_body = response.json()
                except Exception:
                    error_body = response.text
                return {"error": f"Request failed with status {response.status_code}", "details": error_body}

            body = response.json()
            for model in body.get("value", []):
                results.append({
                    "id": model.get("id"),
                    "displayName": model.get("displayName"),
                    "description": model.get("description", ""),
                })

            # Handle pagination via continuationToken / continuationUri
            continuation_uri = body.get("continuationUri")
            url = continuation_uri  # None stops the loop

    return {"semanticModels": results, "count": len(results)}


# ---------------------------------------------------------------------------
# Internal helpers for definition-level CRUD
# ---------------------------------------------------------------------------

async def _fetch_definition(
    client: httpx.AsyncClient,
    workspace_id: str,
    report_id: str,
    headers: dict,
) -> dict:
    """GET report definition and return decoded parts as {path: parsed_object}.

    For text/JSON parts the value is a dict; for unknown binary parts a raw
    base64 string is kept so they can be round-tripped unchanged.
    """
    url = (
        f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}"
        f"/reports/{report_id}/getDefinition"
    )
    resp = await client.post(url, headers=headers, json={})

    # 202 Accepted — LRO for large definitions
    if resp.status_code == 202:
        operation_url = resp.headers.get(
            "Location") or resp.headers.get("x-ms-operation-id")
        if not operation_url:
            return {"error": "202 returned but no Location header"}
        retry_after = int(resp.headers.get("Retry-After", 5))
        body = await _poll_lro(client, operation_url, retry_after, headers)
        if "error" in body:
            return body
        # After LRO the body itself contains the definition
        parts_list = body.get("definition", {}).get("parts", [])
    elif resp.status_code == 200:
        parts_list = resp.json().get("definition", {}).get("parts", [])
    else:
        try:
            err = resp.json()
        except Exception:
            err = resp.text
        return {"error": f"GET definition failed with status {resp.status_code}", "details": err}

    decoded: dict[str, object] = {}
    for part in parts_list:
        path = part.get("path", "")
        payload_type = part.get("payloadType", "")
        raw = part.get("payload", "")
        if payload_type == "InlineBase64":
            text = base64.b64decode(raw).decode("utf-8", errors="replace")
            try:
                decoded[path] = json.loads(text)
            except Exception:
                decoded[path] = raw  # keep raw if not valid JSON
        else:
            decoded[path] = raw
    return decoded


def _encode_parts(decoded: dict[str, object]) -> list[dict]:
    """Re-encode decoded parts back to base64 InlineBase64 format."""
    parts = []
    for path, value in decoded.items():
        if isinstance(value, (dict, list)):
            text = json.dumps(value, indent=2)
        else:
            text = str(value)
        parts.append({
            "path": path,
            "payload": base64.b64encode(text.encode()).decode(),
            "payloadType": "InlineBase64",
        })
    return parts


async def _push_definition(
    client: httpx.AsyncClient,
    workspace_id: str,
    report_id: str,
    decoded: dict[str, object],
    headers: dict,
) -> dict:
    """Encode and POST updated definition parts."""
    url = (
        f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}"
        f"/reports/{report_id}/updateDefinition"
    )
    payload = {"definition": {"parts": _encode_parts(decoded)}}
    resp = await client.post(url, headers=headers, json=payload)

    if resp.status_code in (200, 204):
        return {"status": "success"}
    if resp.status_code == 202:
        operation_url = resp.headers.get(
            "Location") or resp.headers.get("x-ms-operation-id")
        if not operation_url:
            return {"error": "202 returned but no Location header"}
        retry_after = int(resp.headers.get("Retry-After", 5))
        return await _poll_lro(client, operation_url, retry_after, headers)
    if resp.status_code == 429:
        return {"error": "Rate limit exceeded", "retry_after_seconds": resp.headers.get("Retry-After", "unknown")}
    try:
        err = resp.json()
    except Exception:
        err = resp.text
    return {"error": f"updateDefinition failed with status {resp.status_code}", "details": err}


def _get_report_json(decoded: dict) -> dict:
    """Extract and JSON-decode the report.json part (handles double-encoded strings)."""
    rj = decoded.get("report.json", {})
    if isinstance(rj, str):
        rj = json.loads(rj)
    return rj


def _set_report_json(decoded: dict, report_json: dict) -> None:
    decoded["report.json"] = report_json


def _parse_inner(value: object) -> object:
    """Parse a value that may be a JSON string (double-encoded) or already a dict/list."""
    if isinstance(value, str):
        try:
            return json.loads(value)
        except Exception:
            return value
    return value


def _dump_inner(value: object) -> str:
    """Serialise a value back to a JSON string (for double-encoded fields)."""
    return json.dumps(value, separators=(",", ":"))


# ---------------------------------------------------------------------------
# Report-level CRUD
# ---------------------------------------------------------------------------

@mcp.tool()
async def list_reports(
    workspace_id: str,
) -> dict:
    """List all Power BI reports in a Fabric workspace.

    Calls GET https://api.fabric.microsoft.com/v1/workspaces/{workspaceId}/reports.

    Args:
        workspace_id: UUID of the Fabric workspace.

    Returns:
        List of reports with id, displayName, description, and workspaceId.
    """
    url = f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/reports"
    headers = {"Authorization": f"Bearer {_get_token()}"}

    results = []
    async with httpx.AsyncClient(timeout=30) as client:
        while url:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 429:
                return {"error": "Rate limit exceeded", "retry_after_seconds": resp.headers.get("Retry-After", "unknown")}
            if resp.status_code != 200:
                try:
                    err = resp.json()
                except Exception:
                    err = resp.text
                return {"error": f"Request failed with status {resp.status_code}", "details": err}
            body = resp.json()
            for r in body.get("value", []):
                results.append({
                    "id": r.get("id"),
                    "displayName": r.get("displayName"),
                    "description": r.get("description", ""),
                    "workspaceId": r.get("workspaceId"),
                })
            url = body.get("continuationUri")
    return {"reports": results, "count": len(results)}


@mcp.tool()
async def get_report(
    workspace_id: str,
    report_id: str,
) -> dict:
    """Get metadata for a single Power BI report.

    Calls GET https://api.fabric.microsoft.com/v1/workspaces/{workspaceId}/reports/{reportId}.

    Args:
        workspace_id: UUID of the Fabric workspace.
        report_id: UUID of the report.

    Returns:
        Report metadata: id, displayName, description, workspaceId, etc.
    """
    url = f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/reports/{report_id}"
    headers = {"Authorization": f"Bearer {_get_token()}"}
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url, headers=headers)
        if resp.status_code == 200:
            return resp.json()
        if resp.status_code == 429:
            return {"error": "Rate limit exceeded", "retry_after_seconds": resp.headers.get("Retry-After", "unknown")}
        try:
            err = resp.json()
        except Exception:
            err = resp.text
        return {"error": f"Request failed with status {resp.status_code}", "details": err}


@mcp.tool()
async def update_report_metadata(
    workspace_id: str,
    report_id: str,
    display_name: str = "",
    description: str = "",
) -> dict:
    """Update display name and/or description of an existing Power BI report.

    Calls PATCH https://api.fabric.microsoft.com/v1/workspaces/{workspaceId}/reports/{reportId}.
    At least one of display_name or description must be provided.

    Args:
        workspace_id: UUID of the Fabric workspace.
        report_id: UUID of the report.
        display_name: New display name for the report. Leave empty to keep current.
        description: New description. Leave empty to keep current.

    Returns:
        Updated report metadata.
    """
    if not display_name and not description:
        return {"error": "At least one of display_name or description must be provided."}

    url = f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/reports/{report_id}"
    headers = {
        "Authorization": f"Bearer {_get_token()}",
        "Content-Type": "application/json",
    }
    body: dict = {}
    if display_name:
        body["displayName"] = display_name
    if description:
        body["description"] = description

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.patch(url, headers=headers, json=body)
        if resp.status_code == 200:
            return resp.json()
        if resp.status_code == 429:
            return {"error": "Rate limit exceeded", "retry_after_seconds": resp.headers.get("Retry-After", "unknown")}
        try:
            err = resp.json()
        except Exception:
            err = resp.text
        return {"error": f"Request failed with status {resp.status_code}", "details": err}


@mcp.tool()
async def delete_report(
    workspace_id: str,
    report_id: str,
) -> dict:
    """Permanently delete a Power BI report from a Fabric workspace.

    Calls DELETE https://api.fabric.microsoft.com/v1/workspaces/{workspaceId}/reports/{reportId}.

    Args:
        workspace_id: UUID of the Fabric workspace.
        report_id: UUID of the report to delete.

    Returns:
        Success confirmation or error details.
    """
    url = f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/reports/{report_id}"
    headers = {"Authorization": f"Bearer {_get_token()}"}
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.delete(url, headers=headers)
        if resp.status_code in (200, 204):
            return {"status": "success", "report_id": report_id}
        if resp.status_code == 429:
            return {"error": "Rate limit exceeded", "retry_after_seconds": resp.headers.get("Retry-After", "unknown")}
        try:
            err = resp.json()
        except Exception:
            err = resp.text
        return {"error": f"Request failed with status {resp.status_code}", "details": err}


@mcp.tool()
async def get_report_definition(
    workspace_id: str,
    report_id: str,
) -> dict:
    """Fetch and decode the full PBIR-Legacy definition of a Power BI report.

    Returns all definition parts (report.json, definition.pbir, .platform) decoded
    from base64. Double-encoded JSON strings inside report.json (config, filters) are
    left as raw JSON strings to preserve structure fidelity.

    Args:
        workspace_id: UUID of the Fabric workspace.
        report_id: UUID of the report.

    Returns:
        Dict mapping each definition part path to its decoded content.
    """
    headers = {"Authorization": f"Bearer {_get_token()}"}
    async with httpx.AsyncClient(timeout=60) as client:
        return await _fetch_definition(client, workspace_id, report_id, headers)


# ---------------------------------------------------------------------------
# Page CRUD  (operates on report.json → sections[])
# ---------------------------------------------------------------------------

@mcp.tool()
async def list_pages(
    workspace_id: str,
    report_id: str,
) -> dict:
    """List all pages (sections) in a Power BI report.

    Args:
        workspace_id: UUID of the Fabric workspace.
        report_id: UUID of the report.

    Returns:
        List of pages with name, displayName, ordinal, width, height, and visual count.
    """
    headers = {"Authorization": f"Bearer {_get_token()}"}
    async with httpx.AsyncClient(timeout=60) as client:
        decoded = await _fetch_definition(client, workspace_id, report_id, headers)
    if "error" in decoded:
        return decoded

    rj = _get_report_json(decoded)
    sections = rj.get("sections", [])
    pages = [
        {
            "name": s.get("name"),
            "displayName": s.get("displayName"),
            "ordinal": s.get("ordinal"),
            "width": s.get("width"),
            "height": s.get("height"),
            "visualCount": len(s.get("visualContainers", [])),
        }
        for s in sections
    ]
    return {"pages": pages, "count": len(pages)}


@mcp.tool()
async def add_page(
    workspace_id: str,
    report_id: str,
    display_name: str,
    page_name: str = "",
    width: float = 1280.0,
    height: float = 720.0,
    display_option: int = 1,
) -> dict:
    """Add a new blank page (section) to an existing Power BI report.

    READ THESE RESOURCES FIRST:
    - powerbi://knowledge_base/page        → canvas size, displayOption values
    - powerbi://knowledge_base/page_order  → ordinal rules and active page

    Args:
        workspace_id: UUID of the Fabric workspace.
        report_id: UUID of the report.
        display_name: User-facing page tab name.
        page_name: Internal page identifier (auto-generated if omitted).
        width: Canvas width in pixels. Default 1280.
        height: Canvas height in pixels. Default 720.
        display_option: Page scaling — 1=FitToPage, 2=FitToWidth, 3=ActualSize.

    Returns:
        Success confirmation with the new page name.
    """
    import uuid as _uuid
    headers = {
        "Authorization": f"Bearer {_get_token()}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=60) as client:
        decoded = await _fetch_definition(client, workspace_id, report_id, headers)
        if "error" in decoded:
            return decoded

        rj = _get_report_json(decoded)
        sections: list = rj.setdefault("sections", [])

        # Auto-generate a unique page name if not provided
        if not page_name:
            page_name = "ReportSection" + _uuid.uuid4().hex[:8].upper()

        # Guard: name must be unique
        existing_names = {s.get("name") for s in sections}
        if page_name in existing_names:
            return {"error": f"A page with name '{page_name}' already exists."}

        new_section = {
            "name": page_name,
            "displayName": display_name,
            "filters": _dump_inner([]),
            "ordinal": len(sections),
            "visualContainers": [],
            "config": _dump_inner({}),
            "displayOption": display_option,
            "height": height,
            "width": width,
        }
        sections.append(new_section)
        _set_report_json(decoded, rj)

        result = await _push_definition(client, workspace_id, report_id, decoded, headers)
        if result.get("status") == "success":
            return {"status": "success", "pageName": page_name, "displayName": display_name}
        return result


@mcp.tool()
async def update_page(
    workspace_id: str,
    report_id: str,
    page_name: str,
    display_name: str = "",
    width: float = 0,
    height: float = 0,
    display_option: int = -1,
) -> dict:
    """Update settings of an existing page in a Power BI report.

    Args:
        workspace_id: UUID of the Fabric workspace.
        report_id: UUID of the report.
        page_name: Internal page name (from list_pages).
        display_name: New display name. Leave empty to keep current.
        width: New canvas width. Use 0 to keep current.
        height: New canvas height. Use 0 to keep current.
        display_option: Page scaling (1/2/3). Use -1 to keep current.

    Returns:
        Success confirmation or error.
    """
    headers = {
        "Authorization": f"Bearer {_get_token()}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=60) as client:
        decoded = await _fetch_definition(client, workspace_id, report_id, headers)
        if "error" in decoded:
            return decoded

        rj = _get_report_json(decoded)
        section = next((s for s in rj.get("sections", [])
                       if s.get("name") == page_name), None)
        if section is None:
            return {"error": f"Page '{page_name}' not found."}

        if display_name:
            section["displayName"] = display_name
        if width > 0:
            section["width"] = width
        if height > 0:
            section["height"] = height
        if display_option >= 0:
            section["displayOption"] = display_option

        _set_report_json(decoded, rj)
        return await _push_definition(client, workspace_id, report_id, decoded, headers)


@mcp.tool()
async def delete_page(
    workspace_id: str,
    report_id: str,
    page_name: str,
) -> dict:
    """Delete a page from a Power BI report.

    Note: A report must have at least one page; deleting the last page will fail.

    Args:
        workspace_id: UUID of the Fabric workspace.
        report_id: UUID of the report.
        page_name: Internal page name to remove (from list_pages).

    Returns:
        Success confirmation or error.
    """
    headers = {
        "Authorization": f"Bearer {_get_token()}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=60) as client:
        decoded = await _fetch_definition(client, workspace_id, report_id, headers)
        if "error" in decoded:
            return decoded

        rj = _get_report_json(decoded)
        sections = rj.get("sections", [])
        if len(sections) <= 1:
            return {"error": "Cannot delete the only page in a report."}

        new_sections = [s for s in sections if s.get("name") != page_name]
        if len(new_sections) == len(sections):
            return {"error": f"Page '{page_name}' not found."}

        # Re-index ordinals
        for i, s in enumerate(new_sections):
            s["ordinal"] = i

        rj["sections"] = new_sections
        _set_report_json(decoded, rj)
        return await _push_definition(client, workspace_id, report_id, decoded, headers)


@mcp.tool()
async def reorder_pages(
    workspace_id: str,
    report_id: str,
    page_order: list,
) -> dict:
    """Reorder pages in a Power BI report by providing the desired page-name sequence.

    Args:
        workspace_id: UUID of the Fabric workspace.
        report_id: UUID of the report.
        page_order: Ordered list of internal page names (all pages must be included).

    Returns:
        Success confirmation or error.
    """
    headers = {
        "Authorization": f"Bearer {_get_token()}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=60) as client:
        decoded = await _fetch_definition(client, workspace_id, report_id, headers)
        if "error" in decoded:
            return decoded

        rj = _get_report_json(decoded)
        sections = rj.get("sections", [])
        section_map = {s.get("name"): s for s in sections}

        # Validate all names present
        missing = [n for n in page_order if n not in section_map]
        if missing:
            return {"error": f"Unknown page names: {missing}"}
        if len(page_order) != len(sections):
            return {"error": f"page_order must contain all {len(sections)} page names."}

        rj["sections"] = [
            {**section_map[name], "ordinal": idx}
            for idx, name in enumerate(page_order)
        ]
        _set_report_json(decoded, rj)
        return await _push_definition(client, workspace_id, report_id, decoded, headers)


# ---------------------------------------------------------------------------
# Visual CRUD  (operates on report.json → sections[].visualContainers[])
# ---------------------------------------------------------------------------

@mcp.tool()
async def list_visuals(
    workspace_id: str,
    report_id: str,
    page_name: str,
) -> dict:
    """List all visuals on a specific page of a Power BI report.

    Args:
        workspace_id: UUID of the Fabric workspace.
        report_id: UUID of the report.
        page_name: Internal page name (from list_pages).

    Returns:
        List of visuals with their id, visualType, position, and size.
    """
    headers = {"Authorization": f"Bearer {_get_token()}"}
    async with httpx.AsyncClient(timeout=60) as client:
        decoded = await _fetch_definition(client, workspace_id, report_id, headers)
    if "error" in decoded:
        return decoded

    rj = _get_report_json(decoded)
    section = next((s for s in rj.get("sections", [])
                   if s.get("name") == page_name), None)
    if section is None:
        return {"error": f"Page '{page_name}' not found."}

    visuals = []
    for vc in section.get("visualContainers", []):
        cfg = _parse_inner(vc.get("config", "{}"))
        visual_name = cfg.get("name", "")
        visual_obj = cfg.get("singleVisual") or cfg.get("visual", {})
        visuals.append({
            "id": visual_name,
            "visualType": visual_obj.get("visualType", "unknown"),
            "x": vc.get("x"),
            "y": vc.get("y"),
            "z": vc.get("z"),
            "width": vc.get("width"),
            "height": vc.get("height"),
        })
    return {"visuals": visuals, "count": len(visuals)}


@mcp.tool()
async def add_visual(
    workspace_id: str,
    report_id: str,
    page_name: str,
    visual_type: str,
    x: float = 0,
    y: float = 0,
    width: float = 300,
    height: float = 200,
    z: float = 1000,
    title: str = "",
) -> dict:
    """Add a new visual to a page in a Power BI report.

    READ THESE RESOURCES FIRST:
    - powerbi://visuals/list            → all valid visual_type names
    - powerbi://visuals/{visual_type}   → schema/constraints for the specific type
    - powerbi://knowledge_base/visuals  → canvas defaults and placeholder rules

    Common visual types: barChart, clusteredColumnChart, lineChart, pieChart,
    donutChart, areaChart, scatterChart, tableEx, matrixVisual, cardVisual,
    multiRowCard, slicer, kpi, gauge, waterfallChart, ribbonChart, treemap,
    funnel, map, filledMap, azureMap, decompositionTree, keyInfluencers,
    qnaVisual, textbox, image, shapeMap, actionButton.

    Use the powerbi://visuals/list resource to see all available types.

    Args:
        workspace_id: UUID of the Fabric workspace.
        report_id: UUID of the report.
        page_name: Internal page name (from list_pages).
        visual_type: Power BI visual type name (e.g. 'barChart', 'tableEx').
        x: Horizontal position in points. Default 0.
        y: Vertical position in points. Default 0.
        width: Visual width in points. Default 300.
        height: Visual height in points. Default 200.
        z: Layer stacking order. Default 1000.
        title: Optional visual title text.

    Returns:
        Success confirmation with the new visual id.
    """
    import uuid as _uuid
    headers = {
        "Authorization": f"Bearer {_get_token()}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=60) as client:
        decoded = await _fetch_definition(client, workspace_id, report_id, headers)
        if "error" in decoded:
            return decoded

        rj = _get_report_json(decoded)
        section = next((s for s in rj.get("sections", [])
                       if s.get("name") == page_name), None)
        if section is None:
            return {"error": f"Page '{page_name}' not found."}

        visual_id = _uuid.uuid4().hex[:20]

        visual_cfg: dict = {
            "name": visual_id,
            "layouts": [
                {
                    "id": 0,
                    "position": {"x": x, "y": y, "z": z, "width": width, "height": height, "tabOrder": int(z)},
                }
            ],
            "singleVisual": {
                "visualType": visual_type,
                "drillFilterOtherVisuals": True,
                "objects": {},
                "vcObjects": {},
            },
        }

        if title:
            visual_cfg["singleVisual"]["vcObjects"]["title"] = [
                {
                    "properties": {
                        "show": {"expr": {"Literal": {"Value": "true"}}},
                        "text": {"expr": {"Literal": {"Value": f"'{title}'"}}},
                    }
                }
            ]

        visual_container = {
            "x": x,
            "y": y,
            "z": z,
            "width": width,
            "height": height,
            "config": _dump_inner(visual_cfg),
            "filters": _dump_inner([]),
        }

        section.setdefault("visualContainers", []).append(visual_container)
        _set_report_json(decoded, rj)

        result = await _push_definition(client, workspace_id, report_id, decoded, headers)
        if result.get("status") == "success":
            return {"status": "success", "visualId": visual_id, "visualType": visual_type}
        return result


@mcp.tool()
async def update_visual_position(
    workspace_id: str,
    report_id: str,
    page_name: str,
    visual_id: str,
    x: float = -1,
    y: float = -1,
    width: float = -1,
    height: float = -1,
    z: float = -1,
) -> dict:
    """Move or resize a visual on a report page.

    Pass -1 for any dimension to leave it unchanged.

    Args:
        workspace_id: UUID of the Fabric workspace.
        report_id: UUID of the report.
        page_name: Internal page name (from list_pages).
        visual_id: Visual id (from list_visuals).
        x: New horizontal position. -1 = no change.
        y: New vertical position. -1 = no change.
        width: New width. -1 = no change.
        height: New height. -1 = no change.
        z: New z-order. -1 = no change.

    Returns:
        Success confirmation or error.
    """
    headers = {
        "Authorization": f"Bearer {_get_token()}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=60) as client:
        decoded = await _fetch_definition(client, workspace_id, report_id, headers)
        if "error" in decoded:
            return decoded

        rj = _get_report_json(decoded)
        section = next((s for s in rj.get("sections", [])
                       if s.get("name") == page_name), None)
        if section is None:
            return {"error": f"Page '{page_name}' not found."}

        target_vc = None
        for vc in section.get("visualContainers", []):
            cfg = _parse_inner(vc.get("config", "{}"))
            if cfg.get("name") == visual_id:
                target_vc = vc
                break

        if target_vc is None:
            return {"error": f"Visual '{visual_id}' not found on page '{page_name}'."}

        # Update outer container fields
        if x >= 0:
            target_vc["x"] = x
        if y >= 0:
            target_vc["y"] = y
        if z >= 0:
            target_vc["z"] = z
        if width > 0:
            target_vc["width"] = width
        if height > 0:
            target_vc["height"] = height

        # Update layouts inside config as well
        cfg = _parse_inner(target_vc.get("config", "{}"))
        for layout in cfg.get("layouts", []):
            pos = layout.setdefault("position", {})
            if x >= 0:
                pos["x"] = x
            if y >= 0:
                pos["y"] = y
            if z >= 0:
                pos["z"] = z
            if width > 0:
                pos["width"] = width
            if height > 0:
                pos["height"] = height
        target_vc["config"] = _dump_inner(cfg)

        _set_report_json(decoded, rj)
        return await _push_definition(client, workspace_id, report_id, decoded, headers)


@mcp.tool()
async def update_visual_title(
    workspace_id: str,
    report_id: str,
    page_name: str,
    visual_id: str,
    title: str,
    show_title: bool = True,
) -> dict:
    """Set or update the title of a visual on a report page.

    Args:
        workspace_id: UUID of the Fabric workspace.
        report_id: UUID of the report.
        page_name: Internal page name (from list_pages).
        visual_id: Visual id (from list_visuals).
        title: New title text.
        show_title: Whether to show the title. Default True.

    Returns:
        Success confirmation or error.
    """
    headers = {
        "Authorization": f"Bearer {_get_token()}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=60) as client:
        decoded = await _fetch_definition(client, workspace_id, report_id, headers)
        if "error" in decoded:
            return decoded

        rj = _get_report_json(decoded)
        section = next((s for s in rj.get("sections", [])
                       if s.get("name") == page_name), None)
        if section is None:
            return {"error": f"Page '{page_name}' not found."}

        for vc in section.get("visualContainers", []):
            cfg = _parse_inner(vc.get("config", "{}"))
            if cfg.get("name") == visual_id:
                sv = cfg.setdefault("singleVisual", {})
                sv.setdefault("vcObjects", {})["title"] = [
                    {
                        "properties": {
                            "show": {"expr": {"Literal": {"Value": str(show_title).lower()}}},
                            "text": {"expr": {"Literal": {"Value": f"'{title}'"}}},
                        }
                    }
                ]
                vc["config"] = _dump_inner(cfg)
                _set_report_json(decoded, rj)
                return await _push_definition(client, workspace_id, report_id, decoded, headers)

        return {"error": f"Visual '{visual_id}' not found on page '{page_name}'."}


@mcp.tool()
async def delete_visual(
    workspace_id: str,
    report_id: str,
    page_name: str,
    visual_id: str,
) -> dict:
    """Delete a visual from a report page.

    Args:
        workspace_id: UUID of the Fabric workspace.
        report_id: UUID of the report.
        page_name: Internal page name (from list_pages).
        visual_id: Visual id (from list_visuals).

    Returns:
        Success confirmation or error.
    """
    headers = {
        "Authorization": f"Bearer {_get_token()}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=60) as client:
        decoded = await _fetch_definition(client, workspace_id, report_id, headers)
        if "error" in decoded:
            return decoded

        rj = _get_report_json(decoded)
        section = next((s for s in rj.get("sections", [])
                       if s.get("name") == page_name), None)
        if section is None:
            return {"error": f"Page '{page_name}' not found."}

        containers = section.get("visualContainers", [])
        new_containers = []
        removed = False
        for vc in containers:
            cfg = _parse_inner(vc.get("config", "{}"))
            if cfg.get("name") == visual_id:
                removed = True
            else:
                new_containers.append(vc)

        if not removed:
            return {"error": f"Visual '{visual_id}' not found on page '{page_name}'."}

        section["visualContainers"] = new_containers
        _set_report_json(decoded, rj)
        return await _push_definition(client, workspace_id, report_id, decoded, headers)


# ---------------------------------------------------------------------------
# Filter CRUD  (report-level and page-level)
# ---------------------------------------------------------------------------

@mcp.tool()
async def list_filters(
    workspace_id: str,
    report_id: str,
    page_name: str = "",
) -> dict:
    """List filters applied at the report level or on a specific page.

    Args:
        workspace_id: UUID of the Fabric workspace.
        report_id: UUID of the report.
        page_name: Internal page name to list page-level filters.
                   Leave empty for report-level filters.

    Returns:
        List of filters with name, type, and field info.
    """
    headers = {"Authorization": f"Bearer {_get_token()}"}
    async with httpx.AsyncClient(timeout=60) as client:
        decoded = await _fetch_definition(client, workspace_id, report_id, headers)
    if "error" in decoded:
        return decoded

    rj = _get_report_json(decoded)

    if page_name:
        section = next((s for s in rj.get("sections", [])
                       if s.get("name") == page_name), None)
        if section is None:
            return {"error": f"Page '{page_name}' not found."}
        raw_filters = _parse_inner(section.get("filters", "[]"))
    else:
        raw_filters = _parse_inner(rj.get("filters", "[]"))

    return {"filters": raw_filters, "count": len(raw_filters)}


@mcp.tool()
async def add_categorical_filter(
    workspace_id: str,
    report_id: str,
    table_name: str,
    column_name: str,
    values: list,
    filter_name: str = "",
    page_name: str = "",
) -> dict:
    """Add a categorical (IN list) filter at report level or on a specific page.

    READ THESE RESOURCES FIRST:
    - powerbi://knowledge_base/filters → filter types and JSON structure

    Args:
        workspace_id: UUID of the Fabric workspace.
        report_id: UUID of the report.
        table_name: Table/entity name in the semantic model (e.g. 'Product').
        column_name: Column name to filter on (e.g. 'Category').
        values: List of values to include (e.g. ['Bikes', 'Accessories']).
        filter_name: Unique filter name. Auto-generated if empty.
        page_name: Apply filter to this page only. Leave empty for report level.

    Returns:
        Success confirmation or error.
    """
    import uuid as _uuid
    if not filter_name:
        filter_name = f"Filter_{table_name}_{column_name}_{_uuid.uuid4().hex[:6]}"

    source_alias = table_name[0].lower()
    # Build literal values: strings get single quotes, numbers stay bare
    filter_values = []
    for v in values:
        if isinstance(v, str):
            filter_values.append([{"Literal": {"Value": f"'{v}'"}}])
        else:
            filter_values.append([{"Literal": {"Value": str(v)}}])

    new_filter = {
        "name": filter_name,
        "type": "Categorical",
        "howCreated": "User",
        "field": {
            "Column": {
                "Expression": {"SourceRef": {"Entity": table_name}},
                "Property": column_name,
            }
        },
        "filter": {
            "Version": 2,
            "From": [{"Name": source_alias, "Entity": table_name, "Type": 0}],
            "Where": [
                {
                    "Condition": {
                        "In": {
                            "Expressions": [
                                {
                                    "Column": {
                                        "Expression": {"SourceRef": {"Source": source_alias}},
                                        "Property": column_name,
                                    }
                                }
                            ],
                            "Values": filter_values,
                        }
                    }
                }
            ],
        },
    }

    headers = {
        "Authorization": f"Bearer {_get_token()}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=60) as client:
        decoded = await _fetch_definition(client, workspace_id, report_id, headers)
        if "error" in decoded:
            return decoded

        rj = _get_report_json(decoded)

        if page_name:
            section = next((s for s in rj.get("sections", [])
                           if s.get("name") == page_name), None)
            if section is None:
                return {"error": f"Page '{page_name}' not found."}
            current = _parse_inner(section.get("filters", "[]"))
            current.append(new_filter)
            section["filters"] = _dump_inner(current)
        else:
            current = _parse_inner(rj.get("filters", "[]"))
            current.append(new_filter)
            rj["filters"] = _dump_inner(current)

        _set_report_json(decoded, rj)
        result = await _push_definition(client, workspace_id, report_id, decoded, headers)
        if result.get("status") == "success":
            return {"status": "success", "filterName": filter_name}
        return result


@mcp.tool()
async def remove_filter(
    workspace_id: str,
    report_id: str,
    filter_name: str,
    page_name: str = "",
) -> dict:
    """Remove a filter by name from the report level or from a specific page.

    Args:
        workspace_id: UUID of the Fabric workspace.
        report_id: UUID of the report.
        filter_name: Name of the filter to remove (from list_filters).
        page_name: Remove from this page only. Leave empty for report level.

    Returns:
        Success confirmation or error.
    """
    headers = {
        "Authorization": f"Bearer {_get_token()}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=60) as client:
        decoded = await _fetch_definition(client, workspace_id, report_id, headers)
        if "error" in decoded:
            return decoded

        rj = _get_report_json(decoded)

        if page_name:
            section = next((s for s in rj.get("sections", [])
                           if s.get("name") == page_name), None)
            if section is None:
                return {"error": f"Page '{page_name}' not found."}
            current = _parse_inner(section.get("filters", "[]"))
            new_filters = [f for f in current if f.get("name") != filter_name]
            if len(new_filters) == len(current):
                return {"error": f"Filter '{filter_name}' not found on page '{page_name}'."}
            section["filters"] = _dump_inner(new_filters)
        else:
            current = _parse_inner(rj.get("filters", "[]"))
            new_filters = [f for f in current if f.get("name") != filter_name]
            if len(new_filters) == len(current):
                return {"error": f"Filter '{filter_name}' not found at report level."}
            rj["filters"] = _dump_inner(new_filters)

        _set_report_json(decoded, rj)
        return await _push_definition(client, workspace_id, report_id, decoded, headers)


# ---------------------------------------------------------------------------
# DAX Measure CRUD  (operates on reportExtensions.json)
# ---------------------------------------------------------------------------

@mcp.tool()
async def list_dax_measures(
    workspace_id: str,
    report_id: str,
) -> dict:
    """List all report-level DAX measures defined in a Power BI report.

    Report-level DAX measures live in reportExtensions.json and extend entities
    of the bound semantic model without modifying the model itself.

    Args:
        workspace_id: UUID of the Fabric workspace.
        report_id: UUID of the report.

    Returns:
        List of DAX measures grouped by entity (table).
    """
    headers = {"Authorization": f"Bearer {_get_token()}"}
    async with httpx.AsyncClient(timeout=60) as client:
        decoded = await _fetch_definition(client, workspace_id, report_id, headers)
    if "error" in decoded:
        return decoded

    ext = decoded.get("reportExtensions.json")
    if ext is None:
        return {"entities": [], "count": 0, "note": "No reportExtensions.json found in definition."}

    if isinstance(ext, str):
        try:
            ext = json.loads(ext)
        except Exception:
            return {"error": "Could not parse reportExtensions.json"}

    results = []
    for entity in ext.get("entities", []):
        for m in entity.get("measures", []):
            results.append({
                "entity": entity.get("name"),
                "name": m.get("name"),
                "expression": m.get("expression"),
                "dataType": m.get("dataType"),
                "formatString": m.get("formatString", ""),
                "hidden": m.get("hidden", False),
                "displayFolder": m.get("displayFolder", ""),
            })
    return {"measures": results, "count": len(results)}


@mcp.tool()
async def add_dax_measure(
    workspace_id: str,
    report_id: str,
    entity_name: str,
    measure_name: str,
    expression: str,
    data_type: str = "Decimal",
    format_string: str = "",
    description: str = "",
    display_folder: str = "",
    hidden: bool = False,
) -> dict:
    """Add a new report-level DAX measure to a Power BI report.

    READ THESE RESOURCES FIRST:
    - powerbi://knowledge_base/dax_measures      → reportExtensions.json structure
    - powerbi://knowledge_base/fields_and_measures → DAX expression syntax

    Report-level measures extend a table in the bound semantic model without
    modifying the model. They live in reportExtensions.json and can be
    referenced in visuals and filters just like model measures.

    Args:
        workspace_id: UUID of the Fabric workspace.
        report_id: UUID of the report.
        entity_name: Table name in the semantic model to extend (e.g. 'Sales').
        measure_name: Unique measure name (e.g. 'Profit Margin %').
        expression: DAX expression (e.g. 'DIVIDE([Total Profit], [Total Revenue])').
        data_type: PrimitiveTypeName — Decimal, Double, Integer, Text, Boolean, etc.
        format_string: VBA format string (e.g. '0.00%', '#,0', '$#,0.00').
        description: Optional description.
        display_folder: Folder path in the Fields pane (e.g. 'KPIs').
        hidden: Whether to hide the measure. Default False.

    Returns:
        Success confirmation or error.
    """
    headers = {
        "Authorization": f"Bearer {_get_token()}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=60) as client:
        decoded = await _fetch_definition(client, workspace_id, report_id, headers)
        if "error" in decoded:
            return decoded

        # Initialise or parse reportExtensions.json
        ext_raw = decoded.get("reportExtensions.json")
        if ext_raw is None:
            ext: dict = {
                "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/reportExtension/1.0.0/schema.json",
                "name": "extension",
                "entities": [],
            }
        elif isinstance(ext_raw, str):
            ext = json.loads(ext_raw)
        else:
            ext = ext_raw

        # Build measure object
        new_measure: dict = {
            "name": measure_name,
            "dataType": data_type,
            "expression": expression,
        }
        if format_string:
            new_measure["formatString"] = format_string
        if description:
            new_measure["description"] = description
        if display_folder:
            new_measure["displayFolder"] = display_folder
        if hidden:
            new_measure["hidden"] = True

        # Find or create entity
        entity_entry = next(
            (e for e in ext.get("entities", []) if e.get("name") == entity_name), None)
        if entity_entry is None:
            entity_entry = {"name": entity_name, "measures": []}
            ext.setdefault("entities", []).append(entity_entry)

        # Guard: measure name must be unique within entity
        existing = {m.get("name") for m in entity_entry.get("measures", [])}
        if measure_name in existing:
            return {"error": f"Measure '{measure_name}' already exists on entity '{entity_name}'."}

        entity_entry.setdefault("measures", []).append(new_measure)
        decoded["reportExtensions.json"] = ext

        result = await _push_definition(client, workspace_id, report_id, decoded, headers)
        if result.get("status") == "success":
            return {"status": "success", "entity": entity_name, "measure": measure_name}
        return result


@mcp.tool()
async def update_dax_measure(
    workspace_id: str,
    report_id: str,
    entity_name: str,
    measure_name: str,
    expression: str = "",
    data_type: str = "",
    format_string: str = "",
    description: str = "",
    display_folder: str = "",
) -> dict:
    """Update an existing report-level DAX measure.

    Pass empty string for any field to leave it unchanged.

    Args:
        workspace_id: UUID of the Fabric workspace.
        report_id: UUID of the report.
        entity_name: Table name the measure belongs to.
        measure_name: Name of the measure to update.
        expression: New DAX expression. Empty = no change.
        data_type: New data type. Empty = no change.
        format_string: New format string. Empty = no change.
        description: New description. Empty = no change.
        display_folder: New display folder. Empty = no change.

    Returns:
        Success confirmation or error.
    """
    headers = {
        "Authorization": f"Bearer {_get_token()}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=60) as client:
        decoded = await _fetch_definition(client, workspace_id, report_id, headers)
        if "error" in decoded:
            return decoded

        ext_raw = decoded.get("reportExtensions.json")
        if ext_raw is None:
            return {"error": "No reportExtensions.json found — no DAX measures defined yet."}
        ext = json.loads(ext_raw) if isinstance(ext_raw, str) else ext_raw

        entity_entry = next(
            (e for e in ext.get("entities", []) if e.get("name") == entity_name), None)
        if entity_entry is None:
            return {"error": f"Entity '{entity_name}' not found in report extensions."}

        measure = next((m for m in entity_entry.get(
            "measures", []) if m.get("name") == measure_name), None)
        if measure is None:
            return {"error": f"Measure '{measure_name}' not found in entity '{entity_name}'."}

        if expression:
            measure["expression"] = expression
        if data_type:
            measure["dataType"] = data_type
        if format_string:
            measure["formatString"] = format_string
        if description:
            measure["description"] = description
        if display_folder:
            measure["displayFolder"] = display_folder

        decoded["reportExtensions.json"] = ext
        return await _push_definition(client, workspace_id, report_id, decoded, headers)


@mcp.tool()
async def delete_dax_measure(
    workspace_id: str,
    report_id: str,
    entity_name: str,
    measure_name: str,
) -> dict:
    """Delete a report-level DAX measure from a Power BI report.

    Args:
        workspace_id: UUID of the Fabric workspace.
        report_id: UUID of the report.
        entity_name: Table name the measure belongs to.
        measure_name: Name of the measure to delete.

    Returns:
        Success confirmation or error.
    """
    headers = {
        "Authorization": f"Bearer {_get_token()}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=60) as client:
        decoded = await _fetch_definition(client, workspace_id, report_id, headers)
        if "error" in decoded:
            return decoded

        ext_raw = decoded.get("reportExtensions.json")
        if ext_raw is None:
            return {"error": "No reportExtensions.json found — no DAX measures defined yet."}
        ext = json.loads(ext_raw) if isinstance(ext_raw, str) else ext_raw

        entity_entry = next(
            (e for e in ext.get("entities", []) if e.get("name") == entity_name), None)
        if entity_entry is None:
            return {"error": f"Entity '{entity_name}' not found in report extensions."}

        measures = entity_entry.get("measures", [])
        new_measures = [m for m in measures if m.get("name") != measure_name]
        if len(new_measures) == len(measures):
            return {"error": f"Measure '{measure_name}' not found in entity '{entity_name}'."}

        entity_entry["measures"] = new_measures
        # Remove entity entry if it has no measures left
        if not new_measures:
            ext["entities"] = [e for e in ext.get(
                "entities", []) if e.get("name") != entity_name]

        decoded["reportExtensions.json"] = ext
        return await _push_definition(client, workspace_id, report_id, decoded, headers)


# ---------------------------------------------------------------------------
# Bookmark CRUD  (operates on bookmarks.json and bookmark files)
# ---------------------------------------------------------------------------

@mcp.tool()
async def list_bookmarks(
    workspace_id: str,
    report_id: str,
) -> dict:
    """List all bookmarks in a Power BI report.

    Reads the bookmarks.json definition part which contains bookmark order and
    group structure. Only available for PBIR-format reports (not PBIR-Legacy).

    Args:
        workspace_id: UUID of the Fabric workspace.
        report_id: UUID of the report.

    Returns:
        List of bookmark names and display names.
    """
    headers = {"Authorization": f"Bearer {_get_token()}"}
    async with httpx.AsyncClient(timeout=60) as client:
        decoded = await _fetch_definition(client, workspace_id, report_id, headers)
    if "error" in decoded:
        return decoded

    # Collect all bookmark files
    bookmark_parts = {
        k: v for k, v in decoded.items()
        if k.endswith(".bookmark.json") or k == "bookmarks/bookmarks.json"
    }

    if not bookmark_parts:
        return {"bookmarks": [], "count": 0, "note": "No bookmarks found in this report."}

    bookmarks = []
    for path, content in bookmark_parts.items():
        if path.endswith(".bookmark.json"):
            bm = content if isinstance(content, dict) else json.loads(content)
            bookmarks.append({
                "path": path,
                "name": bm.get("name"),
                "displayName": bm.get("displayName"),
                "activePage": bm.get("explorationState", {}).get("activeSection"),
            })
    return {"bookmarks": bookmarks, "count": len(bookmarks)}


@mcp.tool()
async def add_bookmark(
    workspace_id: str,
    report_id: str,
    display_name: str,
    active_page_name: str,
    bookmark_name: str = "",
    suppress_data: bool = False,
    suppress_display: bool = False,
) -> dict:
    """Add a new bookmark to a Power BI report.

    READ THESE RESOURCES FIRST:
    - powerbi://knowledge_base/bookmark       → bookmark JSON structure
    - powerbi://knowledge_base/bookmarks_pane → bookmark groups and ordering

    Creates a bookmark that captures the current active page. The bookmark is
    added to the report definition as a new .bookmark.json part.

    Note: This only works for PBIR-format (non-Legacy) reports. For PBIR-Legacy,
    bookmarks are embedded in report.json config.

    Args:
        workspace_id: UUID of the Fabric workspace.
        report_id: UUID of the report.
        display_name: User-facing bookmark name.
        active_page_name: The page name the bookmark captures.
        bookmark_name: Internal bookmark name. Auto-generated if empty.
        suppress_data: If True, bookmark won't change data/filters (display-only).
        suppress_display: If True, bookmark won't change visual formatting (data-only).

    Returns:
        Success confirmation with the new bookmark name.
    """
    import uuid as _uuid
    if not bookmark_name:
        bookmark_name = "Bookmark" + _uuid.uuid4().hex[:8].upper()

    options: dict = {}
    if suppress_data:
        options["suppressData"] = True
    if suppress_display:
        options["suppressDisplay"] = True

    bookmark_def: dict = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/bookmark/1.0.0/schema.json",
        "name": bookmark_name,
        "displayName": display_name,
        "explorationState": {
            "version": "1.0",
            "activeSection": active_page_name,
            "sections": {
                active_page_name: {"visualContainers": {}}
            },
        },
    }
    if options:
        bookmark_def["options"] = options

    headers = {
        "Authorization": f"Bearer {_get_token()}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=60) as client:
        decoded = await _fetch_definition(client, workspace_id, report_id, headers)
        if "error" in decoded:
            return decoded

        bm_path = f"definition/bookmarks/{bookmark_name}.bookmark.json"
        decoded[bm_path] = bookmark_def

        result = await _push_definition(client, workspace_id, report_id, decoded, headers)
        if result.get("status") == "success":
            return {"status": "success", "bookmarkName": bookmark_name, "displayName": display_name}
        return result


@mcp.tool()
async def delete_bookmark(
    workspace_id: str,
    report_id: str,
    bookmark_path: str,
) -> dict:
    """Delete a bookmark from a Power BI report.

    Args:
        workspace_id: UUID of the Fabric workspace.
        report_id: UUID of the report.
        bookmark_path: Full path of the bookmark part (from list_bookmarks, e.g.
                       'definition/bookmarks/Bookmark1.bookmark.json').

    Returns:
        Success confirmation or error.
    """
    headers = {
        "Authorization": f"Bearer {_get_token()}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=60) as client:
        decoded = await _fetch_definition(client, workspace_id, report_id, headers)
        if "error" in decoded:
            return decoded

        if bookmark_path not in decoded:
            return {"error": f"Bookmark path '{bookmark_path}' not found in report definition."}

        del decoded[bookmark_path]
        return await _push_definition(client, workspace_id, report_id, decoded, headers)


# ---------------------------------------------------------------------------
# Semantic model schema discovery
# ---------------------------------------------------------------------------

@mcp.tool()
async def list_semantic_model_columns(
    workspace_id: str,
    semantic_model_id: str,
) -> dict:
    """List all visible tables and columns in a Fabric semantic model.

    Uses the Power BI executeQueries API with DAX INFO.COLUMNS() to discover
    the schema without needing XMLA access. Use the results to know which
    table/column names to pass to add_field_to_visual.

    Args:
        workspace_id: UUID of the Fabric workspace (used for context only).
        semantic_model_id: UUID of the semantic model to inspect.

    Returns:
        Dict mapping table names to lists of {column, dataType} objects.
    """
    headers = {
        "Authorization": f"Bearer {_get_token()}",
        "Content-Type": "application/json",
    }
    # DAX queries to try in order (simplest to most complex)
    dax_queries = [
        "EVALUATE SELECTCOLUMNS(FILTER(INFO.COLUMNS(), [IsHidden] = FALSE()), \"Table\", [TableName], \"Column\", [ExplicitName], \"DataType\", [DataType])",
        "EVALUATE SELECTCOLUMNS(INFO.COLUMNS(), \"Table\", [TableName], \"Column\", [ExplicitName], \"DataType\", [DataType])",
        "EVALUATE INFO.TABLES()",
    ]
    # Try workspace-scoped URL first (Fabric), then global URL (classic Power BI)
    base_urls = [
        f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{semantic_model_id}/executeQueries",
        f"https://api.powerbi.com/v1.0/myorg/datasets/{semantic_model_id}/executeQueries",
    ]

    errors = []
    async with httpx.AsyncClient(timeout=30) as client:
        for base_url in base_urls:
            for dax in dax_queries:
                payload = {
                    "queries": [{"query": dax}],
                    "serializerSettings": {"includeNulls": True},
                }
                resp = await client.post(base_url, headers=headers, json=payload)
                if resp.status_code != 200:
                    errors.append(f"{base_url}: HTTP {resp.status_code}")
                    continue
                data = resp.json()
                if "error" in data:
                    errors.append(
                        f"{base_url}: {data['error'].get('code', 'DAX error')}")
                    continue
                rows = data.get("results", [{}])[0].get(
                    "tables", [{}])[0].get("rows", [])
                tables: dict = {}
                for row in rows:
                    t = row.get("[Table]") or row.get("[Name]", "")
                    c = row.get("[Column]", "")
                    d = row.get("[DataType]", "")
                    if t:
                        tables.setdefault(t, [])
                        if c:
                            tables[t].append({"column": c, "dataType": d})
                if tables or rows:
                    return {"tables": tables, "tableCount": len(tables)}

    return {
        "error": "Could not retrieve schema via executeQueries.",
        "triedUrls": base_urls,
        "details": errors,
        "hint": "The model may need Build permission. Provide table/column names manually to add_field_to_visual.",
    }


# ---------------------------------------------------------------------------
# Visual field binding
# ---------------------------------------------------------------------------

@mcp.tool()
async def remove_field_from_visual(
    workspace_id: str,
    report_id: str,
    page_name: str,
    visual_id: str,
    table_name: str,
    field_name: str,
    role: str,
) -> dict:
    """Remove a bound field from a visual's data role (field well).

    Use list_visuals to get visual_id, then call this to unbind a specific
    table/field from a role without affecting other bindings on the visual.

    Args:
        workspace_id: UUID of the Fabric workspace.
        report_id: UUID of the report.
        page_name: Internal page name (from list_pages).
        visual_id: Visual id (from list_visuals).
        table_name: Table name of the field to remove (e.g. 'Sales').
        field_name: Column or measure name to remove (e.g. 'Data').
        role: The visual role the field is bound to (e.g. 'Y', 'Category', 'Values').

    Returns:
        Success confirmation or error.
    """
    headers = {
        "Authorization": f"Bearer {_get_token()}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=60) as client:
        decoded = await _fetch_definition(client, workspace_id, report_id, headers)
        if "error" in decoded:
            return decoded

        rj = _get_report_json(decoded)
        section = next((s for s in rj.get("sections", [])
                       if s.get("name") == page_name), None)
        if section is None:
            return {"error": f"Page '{page_name}' not found."}

        target_vc = None
        for vc in section.get("visualContainers", []):
            cfg = _parse_inner(vc.get("config", "{}"))
            if cfg.get("name") == visual_id:
                target_vc = vc
                break
        if target_vc is None:
            return {"error": f"Visual '{visual_id}' not found on page '{page_name}'."}

        cfg = _parse_inner(target_vc.get("config", "{}"))
        sv = cfg.setdefault("singleVisual", {})
        query_ref = f"{table_name}.{field_name}"

        # ── Remove from projections ───────────────────────────────────────────
        projections = sv.get("projections", {})
        role_entries = projections.get(role, [])
        new_role_entries = [
            e for e in role_entries if e.get("queryRef") != query_ref]
        if len(new_role_entries) == len(role_entries):
            return {"error": f"Field '{query_ref}' not found in role '{role}' on visual '{visual_id}'."}
        projections[role] = new_role_entries
        # Remove the role key entirely if it has no more entries
        if not new_role_entries:
            del projections[role]

        # ── Remove from prototypeQuery Select ────────────────────────────────
        pq = sv.get("prototypeQuery", {})
        pq["Select"] = [s for s in pq.get(
            "Select", []) if s.get("Name") != query_ref]

        # ── Remove source from From if no other Select references it ────────
        source_alias = table_name[0].lower()
        remaining_sources = {
            s.get("Column", s.get("Measure", {})).get(
                "Expression", {}).get("SourceRef", {}).get("Source")
            for s in pq.get("Select", [])
        }
        pq["From"] = [f for f in pq.get("From", []) if f.get(
            "Name") in remaining_sources]

        target_vc["config"] = _dump_inner(cfg)
        _set_report_json(decoded, rj)
        result = await _push_definition(client, workspace_id, report_id, decoded, headers)
        if result.get("status") == "success":
            return {"status": "success", "visualId": visual_id, "removed": f"{table_name}[{field_name}] from {role}"}
        if isinstance(result, dict) and result.get("status", "").lower() in ("succeeded", "completed"):
            return {"status": "success", "visualId": visual_id, "removed": f"{table_name}[{field_name}] from {role}"}
        return result


@mcp.tool()
async def add_field_to_visual(
    workspace_id: str,
    report_id: str,
    page_name: str,
    visual_id: str,
    table_name: str,
    field_name: str,
    role: str,
    is_measure: bool = False,
) -> dict:
    """Bind a table column or measure to a visual's data role (field well).

    READ THESE RESOURCES FIRST:
    - powerbi://knowledge_base/field_wells      → exact role key names per visual type
    - powerbi://knowledge_base/fields           → field binding / expression structure
    - powerbi://knowledge_base/fields_and_measures → Column vs Measure syntax

    Call list_visuals to get visual_id and list_semantic_model_columns to
    discover available table/field names.

    Common roles by visual type
    ───────────────────────────
    clusteredBarChart / clusteredColumnChart / lineChart:
        Category (X-axis), Y (values), Series (legend)
    pieChart / donutChart:
        Category, Y (values)
    tableEx / matrixVisual:
        Values
    cardVisual:
        Values
    slicer:
        Field
    scatterChart:
        X, Y, Size, Details, Series

    Args:
        workspace_id: UUID of the Fabric workspace.
        report_id: UUID of the report.
        page_name: Internal page name (from list_pages).
        visual_id: Visual id (from list_visuals).
        table_name: Table name in the semantic model (e.g. 'Sales').
        field_name: Column or measure name (e.g. 'Category', 'Total Sales').
        role: The visual role / field well to bind to (e.g. 'Category', 'Y', 'Values', 'Field').
        is_measure: True if field_name is a measure, False for a column. Default False.

    Returns:
        Success confirmation or error.
    """
    headers = {
        "Authorization": f"Bearer {_get_token()}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=60) as client:
        decoded = await _fetch_definition(client, workspace_id, report_id, headers)
        if "error" in decoded:
            return decoded

        rj = _get_report_json(decoded)
        section = next((s for s in rj.get("sections", [])
                       if s.get("name") == page_name), None)
        if section is None:
            return {"error": f"Page '{page_name}' not found."}

        target_vc = None
        for vc in section.get("visualContainers", []):
            cfg = _parse_inner(vc.get("config", "{}"))
            if cfg.get("name") == visual_id:
                target_vc = vc
                break
        if target_vc is None:
            return {"error": f"Visual '{visual_id}' not found on page '{page_name}'."}

        cfg = _parse_inner(target_vc.get("config", "{}"))
        sv = cfg.setdefault("singleVisual", {})

        # ── Build query ref name (used as key across prototypeQuery + projections)
        source_alias = table_name[0].lower()
        query_ref = f"{table_name}.{field_name}"

        # ── Update prototypeQuery ──────────────────────────────────────────────
        pq = sv.setdefault("prototypeQuery", {
            "Version": 2,
            "From": [],
            "Select": [],
        })

        # Add source if not already present
        if not any(f.get("Entity") == table_name for f in pq.get("From", [])):
            pq.setdefault("From", []).append({
                "Name": source_alias,
                "Entity": table_name,
                "Type": 0,
            })

        # Add select expression if not already present
        existing_refs = {s.get("Name") for s in pq.get("Select", [])}
        if query_ref not in existing_refs:
            expr_ref = {"SourceRef": {"Source": source_alias}}
            if is_measure:
                select_item = {
                    "Measure": {"Expression": expr_ref, "Property": field_name},
                    "Name": query_ref,
                }
            else:
                select_item = {
                    "Column": {"Expression": expr_ref, "Property": field_name},
                    "Name": query_ref,
                }
            pq.setdefault("Select", []).append(select_item)

        # ── Update projections ────────────────────────────────────────────────
        projections = sv.setdefault("projections", {})
        role_entries = projections.setdefault(role, [])
        if not any(e.get("queryRef") == query_ref for e in role_entries):
            role_entries.append({"queryRef": query_ref, "active": True})

        target_vc["config"] = _dump_inner(cfg)
        _set_report_json(decoded, rj)
        result = await _push_definition(client, workspace_id, report_id, decoded, headers)
        if result.get("status") == "success":
            return {
                "status": "success",
                "visualId": visual_id,
                "bound": f"{table_name}[{field_name}] → {role}",
            }
        # LRO succeeded
        if isinstance(result, dict) and result.get("status", "").lower() in ("succeeded", "completed"):
            return {
                "status": "success",
                "visualId": visual_id,
                "bound": f"{table_name}[{field_name}] → {role}",
            }
        return result


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=9000)
