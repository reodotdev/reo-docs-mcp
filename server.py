"""
Reo MCP Server
Wraps the reo.dev integration and ingest APIs for use with Claude Desktop.
"""

import os
import httpx
from dotenv import load_dotenv
from fastmcp import FastMCP

load_dotenv()

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


def _pagination_info(data: dict) -> str:
    total = data.get("total_pages")
    next_pg = data.get("next_page")
    if total is not None:
        info = f"total_pages: {total}"
        if next_pg is not None:
            info += f", next_page: {next_pg}"
        return info
    return ""


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

    segments = data.get("data", [])
    pagination = _pagination_info(data)

    header = f"**Reo.dev Segments** ({len(segments)} found)"
    if pagination:
        header += f" | {pagination}"
    lines = [header, ""]

    if not segments:
        lines.append("No segments found.")
    else:
        for s in segments:
            line = f"• [{s.get('segment_id', '')}] {s.get('name', '')} — type: {s.get('type', '')}"
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

    accounts = data.get("data", [])
    pagination = _pagination_info(data)

    header = f"**Accounts in Segment {segment_id}** ({len(accounts)} found)"
    if pagination:
        header += f" | {pagination}"
    lines = [header, ""]

    if not accounts:
        lines.append("No accounts found.")
    else:
        for a in accounts:
            line = f"• {a.get('account_name', 'Unknown')} — {a.get('account_domain', '')}"
            if a.get("active_developers_count") is not None:
                line += f" | devs: {a['active_developers_count']}"
            if a.get("developer_activity"):
                line += f" | activity: {a['developer_activity']}"
            if a.get("customer_fit"):
                line += f" | fit: {a['customer_fit']}"
            if a.get("country"):
                line += f" | {a['country']}"
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

    activities = data.get("data", [])

    lines = [f"**Activities for Account {account_id}** ({len(activities)} found)", ""]
    if not activities:
        lines.append("No activities found.")
    else:
        for a in activities:
            line = f"• [{a.get('activity_type', '')}] {a.get('activity_date', '')} — source: {a.get('source_type', '')}"
            if a.get("actor"):
                line += f" | actor: {a['actor']}"
            if a.get("developer_designation"):
                line += f" | {a['developer_designation']}"
            if a.get("source_url"):
                line += f" | {a['source_url']}"
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

    developers = data.get("data", [])
    pagination = _pagination_info(data)

    header = f"**Developers for Account {account_id}** ({len(developers)} found)"
    if pagination:
        header += f" | {pagination}"
    lines = [header, ""]

    if not developers:
        lines.append("No developers found.")
    else:
        for d in developers:
            line = f"• {d.get('developer_name', 'Unknown')}"
            if d.get("developer_business_email"):
                line += f" — {d['developer_business_email']}"
            if d.get("developer_github"):
                line += f" | GitHub: {d['developer_github']}"
            if d.get("developer_linkedin"):
                line += f" | LinkedIn: {d['developer_linkedin']}"
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

    developers = data.get("data", [])
    pagination = _pagination_info(data)

    header = f"**Developers in Segment {segment_id}** ({len(developers)} found)"
    if pagination:
        header += f" | {pagination}"
    lines = [header, ""]

    if not developers:
        lines.append("No developers found.")
    else:
        for d in developers:
            line = f"• {d.get('developer_name', 'Unknown')}"
            if d.get("developer_business_email"):
                line += f" — {d['developer_business_email']}"
            if d.get("developer_github"):
                line += f" | GitHub: {d['developer_github']}"
            if d.get("tags"):
                line += f" | tags: {d['tags']}"
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

    activities = data.get("data", [])

    lines = [f"**Activities for Developer {developer_id}** ({len(activities)} found)", ""]
    if not activities:
        lines.append("No activities found.")
    else:
        for a in activities:
            line = f"• [{a.get('activity_type', '')}] {a.get('source_type', '')} — {a.get('source', '')}"
            if a.get("action_time"):
                line += f" | time: {a['action_time']}"
            if a.get("account_id"):
                line += f" | account: {a['account_id']}"
            if a.get("source_url"):
                line += f" | {a['source_url']}"
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

    buyers = data.get("data", [])
    pagination = _pagination_info(data)

    header = f"**Buyers in Segment {segment_id}** ({len(buyers)} found)"
    if pagination:
        header += f" | {pagination}"
    lines = [header, ""]

    if not buyers:
        lines.append("No buyers found.")
    else:
        for b in buyers:
            line = f"• {b.get('developer_name', 'Unknown')}"
            if b.get("developer_business_email"):
                line += f" — {b['developer_business_email']}"
            if b.get("developer_linkedin"):
                line += f" | LinkedIn: {b['developer_linkedin']}"
            if b.get("tags"):
                line += f" | tags: {b['tags']}"
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
        f"ID: {result.get('id', 'N/A')}",
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

    lists = data if isinstance(data, list) else data.get("data", [])

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
async def reo_list_audiences(type: str | None = None) -> str:
    """
    List all audiences from reo.dev.

    Args:
        type: Filter audiences by type — "BUYER" or "DEVELOPER". Omit to return all audiences.
    """
    params = {}
    if type is not None:
        params["type"] = type

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            f"{REO_INTEGRATION_BASE_URL}/audiences",
            headers=_reo_headers(),
            params=params,
        )
        resp.raise_for_status()
        data = resp.json()

    audiences = data.get("data", [])

    lines = [f"**Reo.dev Audiences** ({len(audiences)} found)", ""]
    if not audiences:
        lines.append("No audiences found.")
    else:
        for a in audiences:
            line = f"• [{a.get('id', '')}] {a.get('name', '')} — type: {a.get('type', '')} | source: {a.get('source', '')}"
            if a.get("count") is not None:
                line += f" | members: {a['count']}"
            if a.get("last_synced_at"):
                line += f" | synced: {a['last_synced_at']}"
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

    members = data.get("data", [])
    page_no = data.get("page_no", page)
    page_size = data.get("page_size")
    total_pages = data.get("total_pages")

    pagination = f"page {page_no}"
    if total_pages is not None:
        pagination += f" of {total_pages}"
    if page_size is not None:
        pagination += f" (page size: {page_size})"

    lines = [
        f"**Audience {audience_id} Members** ({len(members)} on {pagination})",
        "",
    ]
    if not members:
        lines.append("No members found.")
    else:
        for m in members:
            line = f"• {m.get('full_name', 'Unknown')}"
            if m.get("designation"):
                line += f" ({m['designation']})"
            if m.get("email"):
                line += f" — {m['email']}"
            if m.get("country"):
                line += f" | {m['country']}"
            if m.get("linkedin"):
                line += f" | LinkedIn: {m['linkedin']}"
            lines.append(line)

    return "\n".join(lines)


if __name__ == "__main__":
    if TRANSPORT == "http":
        mcp.run(transport="streamable-http", host="0.0.0.0", port=PORT, path="/mcp")
    else:
        mcp.run(transport="stdio")
