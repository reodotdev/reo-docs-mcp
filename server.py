"""
Reo MCP Server
Wraps the reo.dev integration and ingest APIs for use with Claude Desktop.
"""

import os
import httpx
from dotenv import load_dotenv
from fastmcp import FastMCP, Context

load_dotenv()

REO_INTEGRATION_BASE_URL = os.environ.get("REO_INTEGRATION_BASE_URL", "https://integration.reo.dev")
REO_INGEST_BASE_URL = os.environ.get("REO_INGEST_BASE_URL", "https://ingest.reo.dev")
# Fallback keys used only for stdio/local mode; HTTP clients pass their own via headers
REO_API_KEY_DEFAULT = os.environ.get("REO_API_KEY", "")
REO_USER_DEFAULT = os.environ.get("REO_USER", "")
TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
PORT = int(os.environ.get("MCP_PORT", "8000"))

mcp = FastMCP("Reo Service")


def _build_payload(**kwargs) -> dict:
    """Build request payload, dropping None values."""
    return {k: v for k, v in kwargs.items() if v is not None}


def _get_credentials(ctx: Context) -> tuple[str, str]:
    """Extract API key and user from request headers, falling back to env vars."""
    try:
        headers = ctx.request_context.request.headers
        api_key = headers.get("x-api-key", "") or REO_API_KEY_DEFAULT
        user = headers.get("x-reo-user", "") or REO_USER_DEFAULT
    except AttributeError:
        api_key = REO_API_KEY_DEFAULT
        user = REO_USER_DEFAULT
    return api_key, user


def _reo_headers(api_key: str) -> dict:
    return {
        "x-api-key": api_key,
        "Content-Type": "application/json",
    }


def _reo_list_headers(api_key: str, user: str) -> dict:
    return {
        "x-api-key": api_key,
        "user": user,
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
async def reo_list_segments(ctx: Context, page: int | None = None) -> str:
    """
    List all segments defined in reo.dev. A segment is a group of accounts, developers,
    or buyers that share common traits (e.g. "High Developer Activity", "US Enterprise Accounts").

    Use this tool when the user asks to:
    - See all segments or groups
    - Find a segment by name or type
    - Get segment IDs needed to drill into accounts, developers, or buyers

    Each segment has a type: ACCOUNT, DEVELOPER, or BUYER. Use the returned segment_id
    with other tools like reo_list_segment_accounts, reo_list_segment_developers, or
    reo_list_segment_buyers to explore the members of a segment.

    Results are paginated. If total_pages > 1, call again with page=2, page=3, etc.
    to retrieve subsequent pages. Omit page to get the first page.

    Args:
        page: Page number for pagination. Starts at 1. Omit to get the first page.

    Returns:
        A formatted list of segments showing segment_id, name, type, and description.
        Includes pagination info (total_pages, next_page) when multiple pages exist.
    """
    api_key, _ = _get_credentials(ctx)
    params = {}
    if page is not None:
        params["page"] = page

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            f"{REO_INTEGRATION_BASE_URL}/segments",
            headers=_reo_headers(api_key),
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
async def reo_list_segment_accounts(ctx: Context, segment_id: str, page: int | None = None) -> str:
    """
    List all company accounts that belong to a specific reo.dev segment. Accounts represent
    companies or organizations (e.g. Stripe, Notion) identified by their domain.

    Use this tool when the user asks to:
    - See which companies are in a segment
    - Find accounts with high developer activity or a specific customer fit score
    - Get account IDs or domains needed to fetch activities or developers for a company

    Each account includes the company name, domain, number of active developers,
    developer activity level, customer fit score, and country.

    You need the segment_id first — use reo_list_segments to find it if unknown.
    Results are paginated. Check total_pages in the response and call again with
    incremented page numbers to retrieve all accounts.

    Args:
        segment_id: The unique ID of the segment (e.g. "seg-abc123"). Use reo_list_segments
                    to discover available segment IDs.
        page: Page number for pagination. Starts at 1. Omit to get the first page.

    Returns:
        A formatted list of accounts showing company name, domain, active developer count,
        activity level, customer fit, and country. Includes pagination info when applicable.
    """
    api_key, _ = _get_credentials(ctx)
    params = {}
    if page is not None:
        params["page"] = page

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            f"{REO_INTEGRATION_BASE_URL}/segment/{segment_id}/accounts",
            headers=_reo_headers(api_key),
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
async def reo_get_account_activities(ctx: Context, account_id: str) -> str:
    """
    Get the full activity history for a specific company account from reo.dev. Activities
    represent developer actions such as visiting docs pages, copying code snippets, clicking
    links, or engaging with GitHub content — all attributed to the account's domain.

    Use this tool when the user asks to:
    - See what a company has been doing or looking at recently
    - Understand which pages or docs a company's developers are engaging with
    - Find the most active or recent touchpoints for an account
    - Research an account before a sales call or outreach

    Each activity includes the activity type, date, source type (e.g. GITHUB, DOCS),
    the actor (developer), their designation, and the source URL they interacted with.

    This endpoint is not paginated — all activities are returned in a single response.
    Use reo_list_segment_accounts or reo_list_segments to find account IDs if unknown.

    Args:
        account_id: The unique ID of the account (UUID format). Use reo_list_segment_accounts
                    to find account IDs.

    Returns:
        A formatted list of activities showing activity type, date, source type, actor name,
        developer designation, and source URL for each event.
    """
    api_key, _ = _get_credentials(ctx)
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            f"{REO_INTEGRATION_BASE_URL}/account/{account_id}/activities",
            headers=_reo_headers(api_key),
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
async def reo_get_account_developers(ctx: Context, account_id: str, page: int | None = None) -> str:
    """
    Get all individual developers linked to a specific company account in reo.dev.
    Developers are identified by their GitHub activity, LinkedIn profile, or business email,
    and are associated with an account based on their company domain.

    Use this tool when the user asks to:
    - Find the developers or engineers at a specific company
    - Get contact details (email, GitHub, LinkedIn) for people at an account
    - Identify who to reach out to at a company
    - See when a company's developers were last or first active

    Each developer entry includes their name, business email, GitHub URL, LinkedIn URL,
    and timestamps for their first and last activity.

    You need the account_id first — use reo_list_segment_accounts to find it.
    Results are paginated. Use total_pages and next_page to fetch subsequent pages.

    Args:
        account_id: The unique ID of the account (UUID format). Use reo_list_segment_accounts
                    to find account IDs.
        page: Page number for pagination. Starts at 1. Omit to get the first page.

    Returns:
        A formatted list of developers showing name, business email, GitHub, and LinkedIn.
        Includes pagination info when multiple pages exist.
    """
    api_key, _ = _get_credentials(ctx)
    params = {}
    if page is not None:
        params["page"] = page

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            f"{REO_INTEGRATION_BASE_URL}/account/{account_id}/developers",
            headers=_reo_headers(api_key),
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
async def reo_list_segment_developers(ctx: Context, segment_id: str, page: int | None = None) -> str:
    """
    List all individual developers who belong to a specific reo.dev segment. Unlike
    reo_get_account_developers (which fetches developers under one account), this tool
    returns developers across all accounts in the segment — useful for broad outreach
    or identifying active developers within a cohort.

    Use this tool when the user asks to:
    - See all developers in a segment (e.g. "high activity developers", "US developers")
    - Build a list of people to contact from a developer segment
    - Get GitHub or email details for developers in a segment
    - Explore which developers are tagged with specific labels

    Each developer entry includes name, business email, GitHub URL, LinkedIn URL,
    activity timestamps, and tags (e.g. "US Buyers, High intent").

    You need the segment_id first — use reo_list_segments to find segments of type DEVELOPER.
    Results are paginated. Use total_pages and next_page to fetch all pages.

    Args:
        segment_id: The unique ID of the segment (e.g. "seg-abc123"). Should be a DEVELOPER
                    type segment. Use reo_list_segments to discover available segment IDs.
        page: Page number for pagination. Starts at 1. Omit to get the first page.

    Returns:
        A formatted list of developers showing name, business email, GitHub URL, and tags.
        Includes pagination info when multiple pages exist.
    """
    api_key, _ = _get_credentials(ctx)
    params = {}
    if page is not None:
        params["page"] = page

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            f"{REO_INTEGRATION_BASE_URL}/segment/{segment_id}/developers",
            headers=_reo_headers(api_key),
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
async def reo_get_developer_activities(ctx: Context, developer_id: str) -> str:
    """
    Get the full activity history for a specific individual developer from reo.dev.
    This shows every tracked action the developer has taken — such as reading docs,
    visiting pages, copying code, or interacting with GitHub — along with timestamps
    and the account they are associated with.

    Use this tool when the user asks to:
    - See what a specific developer has been doing or looking at
    - Understand a developer's intent or interest areas based on their activity
    - Find out which account/company a developer belongs to
    - Research a specific person before outreach

    Each activity includes the activity type, source type (e.g. GITHUB, DOCS),
    the source name, the source URL, action timestamp, and the associated account ID.

    This endpoint is not paginated — all activities are returned in a single response.
    Use reo_list_segment_developers or reo_get_account_developers to find developer IDs.

    Args:
        developer_id: The unique ID of the developer (UUID format). Use
                      reo_list_segment_developers or reo_get_account_developers to find IDs.

    Returns:
        A formatted list of activities showing activity type, source type, source name,
        action timestamp, account ID, and source URL for each event.
    """
    api_key, _ = _get_credentials(ctx)
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            f"{REO_INTEGRATION_BASE_URL}/developer/{developer_id}/activities",
            headers=_reo_headers(api_key),
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
async def reo_list_segment_buyers(ctx: Context, segment_id: str, page: int | None = None) -> str:
    """
    List all buyers who belong to a specific reo.dev segment. Buyers are business
    decision-makers or purchasing contacts (as opposed to developers/engineers) —
    typically people in roles like sales, marketing, procurement, or leadership
    who may be evaluating or purchasing a product.

    Use this tool when the user asks to:
    - Find buyers or decision-makers in a segment
    - Get contact details (email, LinkedIn) for business contacts in a cohort
    - See which buyers are tagged as high-intent or from a specific region
    - Build outreach lists targeting business stakeholders rather than developers

    Each buyer entry includes name, business email, LinkedIn URL, activity timestamps,
    and tags (e.g. "US Buyers, High intent Buyers").

    You need the segment_id first — use reo_list_segments to find segments of type BUYER.
    Results are paginated. Use total_pages and next_page to fetch all pages.

    Args:
        segment_id: The unique ID of the segment (e.g. "seg-abc123"). Should be a BUYER
                    type segment. Use reo_list_segments to discover available segment IDs.
        page: Page number for pagination. Starts at 1. Omit to get the first page.

    Returns:
        A formatted list of buyers showing name, business email, LinkedIn URL, and tags.
        Includes pagination info when multiple pages exist.
    """
    api_key, _ = _get_credentials(ctx)
    params = {}
    if page is not None:
        params["page"] = page

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            f"{REO_INTEGRATION_BASE_URL}/segment/{segment_id}/buyers",
            headers=_reo_headers(api_key),
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
    ctx: Context,
    name: str,
    list_type: str,
    primary_key: str,
    description: str | None = None,
    mapping: list[dict] | None = None,
) -> str:
    """
    Create a new custom list in reo.dev. Lists are used to import your own sets of accounts
    or developers into reo — for example, uploading a list of target accounts from a CRM,
    or a list of known developer contacts. Once created, use reo_add_to_list to populate it.

    Use this tool when the user asks to:
    - Create a new list of accounts or developers in reo
    - Set up a custom import for a set of companies or people
    - Define a new list before adding entries to it

    list_type must be either "ACCOUNT" or "DEVELOPER".
    primary_key is the field that uniquely identifies each entry:
      - Use "domain" for ACCOUNT lists (e.g. "stripe.com")
      - Use "email" for DEVELOPER lists (e.g. "dev@stripe.com")

    The optional mapping parameter defines additional custom fields beyond the primary key.
    Each mapping object should specify fieldName, fieldType, and optionally other metadata.
    After creating a list, note the returned ID and use it with reo_add_to_list.

    Args:
        name: A descriptive name for the list (e.g. "Q1 Target Accounts", "Conference Leads")
        list_type: Type of entities in the list — must be "ACCOUNT" or "DEVELOPER"
        primary_key: The field used to uniquely identify each entity — "domain" for accounts,
                     "email" for developers
        description: Optional human-readable description of the list's purpose
        mapping: Optional list of field mapping objects for custom fields beyond the primary key

    Returns:
        Confirmation of list creation including the new list's ID, name, type, and description.
    """
    api_key, user = _get_credentials(ctx)
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
            headers=_reo_list_headers(api_key, user),
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
async def reo_get_lists(ctx: Context) -> str:
    """
    Retrieve all custom lists that have been created in reo.dev. Lists are user-created
    imports of accounts or developers (as opposed to segments, which are automatically
    computed by reo based on activity signals).

    Use this tool when the user asks to:
    - See all existing lists in reo
    - Find a list ID before adding entries to it with reo_add_to_list
    - Check whether a specific list already exists before creating a new one
    - Get an overview of imported account or developer lists

    Each list entry shows its ID, name, type (ACCOUNT or DEVELOPER), and description.
    This endpoint returns all lists in a single response — no pagination.

    Returns:
        A formatted list of all reo.dev lists showing ID, name, type, and description.
    """
    api_key, user = _get_credentials(ctx)
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            f"{REO_INGEST_BASE_URL}/api/product/list",
            headers=_reo_list_headers(api_key, user),
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
    ctx: Context,
    list_id: str,
    entities: list[dict],
) -> str:
    """
    Add one or more accounts or developers to an existing reo.dev list. This is used to
    populate a list after creating it with reo_create_list. Each call can add up to 1000
    entities. For larger datasets, split into batches and call multiple times.

    Use this tool when the user asks to:
    - Add companies or people to an existing reo list
    - Import a batch of accounts or developers into reo
    - Populate a list that was just created

    The list must already exist — use reo_create_list first if needed, or reo_get_lists
    to find an existing list ID.

    Each entity object must include a primaryKey field (the domain for accounts, email for
    developers). Additional data can be passed in a companyData object.

    Example entity for an ACCOUNT list:
        {"primaryKey": "stripe.com", "companyData": {"name": "Stripe", "industry": "Fintech"}}

    Example entity for a DEVELOPER list:
        {"primaryKey": "dev@stripe.com", "companyData": {"domain": "stripe.com"}}

    Args:
        list_id: The ID of the existing list to add entities to. Use reo_get_lists to find IDs.
        entities: Array of entity objects to add (max 1000 per call). Each must have a
                  primaryKey field and optionally a companyData object with extra fields.

    Returns:
        Confirmation of how many entities were submitted and the raw API response.
    """
    api_key, user = _get_credentials(ctx)
    payload = {"entities": entities}

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.put(
            f"{REO_INGEST_BASE_URL}/api/product/list/{list_id}",
            headers=_reo_list_headers(api_key, user),
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()

    result = data.get("data", data) if isinstance(data, dict) else data
    return f"**Added to List {list_id}**\n{len(entities)} entities submitted.\nResponse: {result}"


@mcp.tool()
async def reo_list_audiences(ctx: Context, type: str | None = None) -> str:
    """
    List all audiences from reo.dev. An audience is a curated, filtered group of buyers or
    developers built from a segment or list, with optional filters applied (e.g. by designation,
    location, job function, or seniority). Audiences are typically used for targeted outreach
    or ad campaigns.

    Use this tool when the user asks to:
    - See all available audiences in reo
    - Find an audience by name or type before fetching its members
    - Check audience size, source (SEGMENT or LIST), and last sync time
    - Get an audience ID to use with reo_get_audience_members

    Optionally filter by type:
      - "BUYER" — audiences of business decision-makers
      - "DEVELOPER" — audiences of engineers/developers
      Omit type to return all audiences regardless of type.

    Each audience entry shows its ID, name, type, source (SEGMENT or LIST), member count,
    and last synced timestamp. This endpoint is not paginated.

    Args:
        type: Optional filter — "BUYER" or "DEVELOPER". Omit to return all audiences.

    Returns:
        A formatted list of audiences showing ID, name, type, source, member count,
        and last synced time.
    """
    api_key, _ = _get_credentials(ctx)
    params = {}
    if type is not None:
        params["type"] = type

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            f"{REO_INTEGRATION_BASE_URL}/audiences",
            headers=_reo_headers(api_key),
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
async def reo_get_audience_members(ctx: Context, audience_id: str, page: int = 1) -> str:
    """
    Get the individual members of a specific reo.dev audience, with pagination.
    Each member is a person (buyer or developer) who matched the audience's filters.
    Returns contact-level details useful for outreach — name, designation, email,
    country, and LinkedIn URL.

    Use this tool when the user asks to:
    - See the people in a specific audience
    - Get contact details (email, LinkedIn) for audience members
    - Browse through an audience page by page
    - Find out who is in a particular targeted group

    Each member entry includes full name, job designation, email, country, and LinkedIn URL.
    Page size is 100 members per page. Use total_pages in the response to determine how many
    pages exist and call again with page=2, page=3, etc. to retrieve all members.

    You need the audience_id first — use reo_list_audiences to find it.

    Args:
        audience_id: The unique ID of the audience (UUID format). Use reo_list_audiences
                     to find available audience IDs.
        page: Page number for pagination. Starts at 1 (default). Each page returns up to
              100 members. Check total_pages in the response to know when you've fetched all.

    Returns:
        A formatted list of audience members showing full name, designation, email, country,
        and LinkedIn URL. Includes current page, total pages, and page size.
    """
    api_key, _ = _get_credentials(ctx)
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            f"{REO_INTEGRATION_BASE_URL}/audiences/{audience_id}/members",
            headers=_reo_headers(api_key),
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
