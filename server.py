"""
Reo MCP Server
Wraps the reo.dev integration and ingest APIs for use with Claude Desktop.
"""

import os
import httpx
from fastmcp import FastMCP

REO_INTEGRATION_BASE_URL = os.environ.get("REO_INTEGRATION_BASE_URL", "https://integration.reo.dev")
REO_INGEST_BASE_URL = os.environ.get("REO_INGEST_BASE_URL", "https://ingest.reo.dev")
REO_API_KEY = os.environ.get("REO_API_KEY", "")
REO_USER = os.environ.get("REO_USER", "")
TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
PORT = int(os.environ.get("MCP_PORT", "8000"))

mcp = FastMCP("Reo Service")


def _build_payload(**kwargs) -> dict:
    """Build request payload, dropping None values."""
    return {k: v for k, v in kwargs.items() if v is not None}


def _reo_headers() -> dict:
    return {
        "x-api-key": REO_API_KEY,
        "Content-Type": "application/json",
    }


def _reo_list_headers() -> dict:
    return {
        "x-api-key": REO_API_KEY,
        "user": REO_USER,
        "Content-Type": "application/json",
    }


@mcp.tool()
async def reo_list_segments(page: int | None = None) -> str:
    """
    List all segments from reo.dev.

    Args:
        page: Page number for pagination
    """
    params = {}
    if page is not None:
        params["page"] = page

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            f"{REO_INTEGRATION_BASE_URL}/segments",
            headers=_reo_headers(),
            params=params,
        )
        resp.raise_for_status()
        data = resp.json()

    segments = data.get("data", data) if isinstance(data, dict) else data
    if isinstance(segments, dict):
        segments = segments.get("segments", [])

    lines = [f"**Reo.dev Segments** ({len(segments)} found)", ""]
    if not segments:
        lines.append("No segments found.")
    else:
        for s in segments:
            line = f"• [{s.get('segment_id', s.get('id', ''))}] {s.get('name', '')} — type: {s.get('type', '')}"
            if s.get("description"):
                line += f" | {s['description']}"
            lines.append(line)

    return "\n".join(lines)


@mcp.tool()
async def reo_list_segment_accounts(segment_id: str, page: int | None = None) -> str:
    """
    List accounts within a reo.dev segment.

    Args:
        segment_id: The segment ID
        page: Page number for pagination
    """
    params = {}
    if page is not None:
        params["page"] = page

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            f"{REO_INTEGRATION_BASE_URL}/segment/{segment_id}/accounts",
            headers=_reo_headers(),
            params=params,
        )
        resp.raise_for_status()
        data = resp.json()

    accounts = data.get("data", data) if isinstance(data, dict) else data
    if isinstance(accounts, dict):
        accounts = accounts.get("accounts", [])

    lines = [f"**Accounts in Segment {segment_id}** ({len(accounts)} found)", ""]
    if not accounts:
        lines.append("No accounts found.")
    else:
        for a in accounts:
            line = f"• {a.get('name', 'Unknown')} — {a.get('domain', '')}"
            if a.get("developer_count") is not None:
                line += f" | devs: {a['developer_count']}"
            lines.append(line)

    return "\n".join(lines)


@mcp.tool()
async def reo_get_account_activities(account_id: str) -> str:
    """
    Get activities for a specific account from reo.dev.

    Args:
        account_id: The account ID
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            f"{REO_INTEGRATION_BASE_URL}/account/{account_id}/activities",
            headers=_reo_headers(),
        )
        resp.raise_for_status()
        data = resp.json()

    activities = data.get("data", data) if isinstance(data, dict) else data
    if isinstance(activities, dict):
        activities = activities.get("activities", [])

    lines = [f"**Activities for Account {account_id}** ({len(activities)} found)", ""]
    if not activities:
        lines.append("No activities found.")
    else:
        for a in activities:
            line = f"• [{a.get('type', '')}] {a.get('source', '')} — {a.get('date', a.get('timestamp', ''))}"
            if a.get("actor"):
                actor = a["actor"]
                line += f" | actor: {actor.get('name', '')} {actor.get('email', '')}"
            lines.append(line)

    return "\n".join(lines)


@mcp.tool()
async def reo_get_account_developers(account_id: str, page: int | None = None) -> str:
    """
    Get developers associated with a specific account from reo.dev.

    Args:
        account_id: The account ID
        page: Page number for pagination
    """
    params = {}
    if page is not None:
        params["page"] = page

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            f"{REO_INTEGRATION_BASE_URL}/account/{account_id}/developers",
            headers=_reo_headers(),
            params=params,
        )
        resp.raise_for_status()
        data = resp.json()

    developers = data.get("data", data) if isinstance(data, dict) else data
    if isinstance(developers, dict):
        developers = developers.get("developers", [])

    lines = [f"**Developers for Account {account_id}** ({len(developers)} found)", ""]
    if not developers:
        lines.append("No developers found.")
    else:
        for d in developers:
            line = f"• {d.get('name', d.get('full_name', 'Unknown'))}"
            if d.get("email") or d.get("business_email"):
                line += f" — {d.get('email') or d.get('business_email')}"
            if d.get("github"):
                line += f" | GitHub: {d['github']}"
            if d.get("linkedin"):
                line += f" | LinkedIn: {d['linkedin']}"
            lines.append(line)

    return "\n".join(lines)


@mcp.tool()
async def reo_list_segment_developers(segment_id: str, page: int | None = None) -> str:
    """
    List developers within a reo.dev segment.

    Args:
        segment_id: The segment ID
        page: Page number for pagination
    """
    params = {}
    if page is not None:
        params["page"] = page

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            f"{REO_INTEGRATION_BASE_URL}/segment/{segment_id}/developers",
            headers=_reo_headers(),
            params=params,
        )
        resp.raise_for_status()
        data = resp.json()

    developers = data.get("data", data) if isinstance(data, dict) else data
    if isinstance(developers, dict):
        developers = developers.get("developers", [])

    lines = [f"**Developers in Segment {segment_id}** ({len(developers)} found)", ""]
    if not developers:
        lines.append("No developers found.")
    else:
        for d in developers:
            line = f"• {d.get('name', d.get('full_name', 'Unknown'))}"
            if d.get("email") or d.get("business_email"):
                line += f" — {d.get('email') or d.get('business_email')}"
            if d.get("github"):
                line += f" | GitHub: {d['github']}"
            lines.append(line)

    return "\n".join(lines)


@mcp.tool()
async def reo_get_developer_activities(developer_id: str) -> str:
    """
    Get activity logs for a specific developer from reo.dev.

    Args:
        developer_id: The developer ID
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            f"{REO_INTEGRATION_BASE_URL}/developer/{developer_id}/activities",
            headers=_reo_headers(),
        )
        resp.raise_for_status()
        data = resp.json()

    activities = data.get("data", data) if isinstance(data, dict) else data
    if isinstance(activities, dict):
        activities = activities.get("activities", [])

    lines = [f"**Activities for Developer {developer_id}** ({len(activities)} found)", ""]
    if not activities:
        lines.append("No activities found.")
    else:
        for a in activities:
            line = f"• [{a.get('type', '')}] {a.get('source', a.get('source_url', ''))} — {a.get('timestamp', a.get('date', ''))}"
            if a.get("account_id"):
                line += f" | account: {a['account_id']}"
            lines.append(line)

    return "\n".join(lines)


@mcp.tool()
async def reo_list_segment_buyers(segment_id: str, page: int | None = None) -> str:
    """
    List buyers within a reo.dev segment.

    Args:
        segment_id: The segment ID
        page: Page number for pagination
    """
    params = {}
    if page is not None:
        params["page"] = page

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            f"{REO_INTEGRATION_BASE_URL}/segment/{segment_id}/buyers",
            headers=_reo_headers(),
            params=params,
        )
        resp.raise_for_status()
        data = resp.json()

    buyers = data.get("data", data) if isinstance(data, dict) else data
    if isinstance(buyers, dict):
        buyers = buyers.get("buyers", [])

    lines = [f"**Buyers in Segment {segment_id}** ({len(buyers)} found)", ""]
    if not buyers:
        lines.append("No buyers found.")
    else:
        for b in buyers:
            line = f"• {b.get('name', b.get('full_name', 'Unknown'))}"
            if b.get("email") or b.get("business_email"):
                line += f" — {b.get('email') or b.get('business_email')}"
            if b.get("designation"):
                line += f" | {b['designation']}"
            lines.append(line)

    return "\n".join(lines)


@mcp.tool()
async def reo_create_list(
    name: str,
    list_type: str,
    primary_key: str,
    description: str | None = None,
    mapping: list[dict] | None = None,
) -> str:
    """
    Create a new list in reo.dev.

    Args:
        name: Name of the list
        list_type: Type of list — "ACCOUNT" or "DEVELOPER"
        primary_key: Primary key field name (e.g. "domain" for accounts, "email" for developers)
        description: Optional description of the list
        mapping: Optional array of field mapping objects (each with fieldName, fieldType, etc.)
    """
    payload = _build_payload(
        name=name,
        description=description,
        type=list_type,
        primaryKey=primary_key,
        mapping=mapping,
    )

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{REO_INGEST_BASE_URL}/api/product/list",
            headers=_reo_list_headers(),
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()

    result = data.get("data", data) if isinstance(data, dict) else data
    lines = [
        "**List Created Successfully**",
        f"ID: {result.get('id', result.get('list_id', 'N/A'))}",
        f"Name: {result.get('name', name)}",
        f"Type: {result.get('type', list_type)}",
    ]
    if result.get("description"):
        lines.append(f"Description: {result['description']}")

    return "\n".join(lines)


@mcp.tool()
async def reo_get_lists() -> str:
    """
    Retrieve all lists from reo.dev.
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            f"{REO_INGEST_BASE_URL}/api/product/list",
            headers=_reo_list_headers(),
        )
        resp.raise_for_status()
        data = resp.json()

    lists = data.get("data", data) if isinstance(data, dict) else data
    if isinstance(lists, dict):
        lists = lists.get("lists", [])

    lines = [f"**Reo.dev Lists** ({len(lists)} found)", ""]
    if not lists:
        lines.append("No lists found.")
    else:
        for lst in lists:
            line = f"• [{lst.get('id', '')}] {lst.get('name', '')} — type: {lst.get('type', '')}"
            if lst.get("description"):
                line += f" | {lst['description']}"
            lines.append(line)

    return "\n".join(lines)


@mcp.tool()
async def reo_add_to_list(
    list_id: str,
    entities: list[dict],
) -> str:
    """
    Add accounts or developers to an existing reo.dev list.

    Args:
        list_id: The ID of the list to add entities to
        entities: Array of entity objects (max 1000). Each object should include:
                  primaryKey (the key value), and any additional field data.
                  Example for accounts: [{"primaryKey": "stripe.com", "companyData": {"name": "Stripe"}}]
                  Example for developers: [{"primaryKey": "dev@example.com", "companyData": {"domain": "example.com"}}]
    """
    payload = {"entities": entities}

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.put(
            f"{REO_INGEST_BASE_URL}/api/product/list/{list_id}",
            headers=_reo_list_headers(),
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()

    result = data.get("data", data) if isinstance(data, dict) else data
    return f"**Added to List {list_id}**\n{len(entities)} entities submitted.\nResponse: {result}"


@mcp.tool()
async def reo_list_audiences() -> str:
    """
    List all audiences from reo.dev.
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            f"{REO_INTEGRATION_BASE_URL}/audiences",
            headers=_reo_headers(),
        )
        resp.raise_for_status()
        data = resp.json()

    audiences = data.get("data", data) if isinstance(data, dict) else data
    if isinstance(audiences, dict):
        audiences = audiences.get("audiences", [])

    lines = [f"**Reo.dev Audiences** ({len(audiences)} found)", ""]
    if not audiences:
        lines.append("No audiences found.")
    else:
        for a in audiences:
            line = f"• [{a.get('audience_id', a.get('id', ''))}] {a.get('name', '')} — type: {a.get('type', '')}"
            if a.get("member_count") is not None:
                line += f" | members: {a['member_count']}"
            if a.get("source"):
                line += f" | source: {a['source']}"
            lines.append(line)

    return "\n".join(lines)


@mcp.tool()
async def reo_get_audience_members(audience_id: str, page: int = 1) -> str:
    """
    Get members of a specific reo.dev audience.

    Args:
        audience_id: The audience ID
        page: Page number (required, starts at 1)
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            f"{REO_INTEGRATION_BASE_URL}/audiences/{audience_id}/members",
            headers=_reo_headers(),
            params={"page": page},
        )
        resp.raise_for_status()
        data = resp.json()

    inner = data.get("data", data) if isinstance(data, dict) else data
    members = inner.get("members", inner) if isinstance(inner, dict) else inner
    if not isinstance(members, list):
        members = []

    pagination = data.get("pagination", inner.get("pagination", {})) if isinstance(data, dict) else {}

    lines = [
        f"**Audience {audience_id} Members** (page {page})",
        f"{len(members)} members" + (f" of {pagination.get('total', '?')} total" if pagination else ""),
        "",
    ]
    if not members:
        lines.append("No members found.")
    else:
        for m in members:
            line = f"• {m.get('name', m.get('full_name', 'Unknown'))}"
            if m.get("designation"):
                line += f" ({m['designation']})"
            if m.get("email") or m.get("business_email"):
                line += f" — {m.get('email') or m.get('business_email')}"
            if m.get("linkedin"):
                line += f" | LinkedIn: {m['linkedin']}"
            lines.append(line)

    return "\n".join(lines)


if __name__ == "__main__":
    if TRANSPORT == "http":
        mcp.run(transport="streamable-http", host="0.0.0.0", port=PORT, path="/mcp")
    else:
        mcp.run(transport="stdio")
