# Reo MCP Server

MCP server that exposes reo.dev integration and ingest APIs to Claude Desktop.

## Tools

- **reo_list_segments** — list all segments
- **reo_list_segment_accounts** — list accounts within a segment
- **reo_get_account_activities** — get activities for an account
- **reo_get_account_developers** — get developers for an account
- **reo_list_segment_developers** — list developers within a segment
- **reo_get_developer_activities** — get activity logs for a developer
- **reo_list_segment_buyers** — list buyers within a segment
- **reo_create_list** — create a new account or developer list
- **reo_get_lists** — retrieve all lists
- **reo_add_to_list** — add accounts or developers to a list
- **reo_list_audiences** — list all audiences
- **reo_get_audience_members** — get members of an audience

## Local Setup (Claude Desktop on your Mac)

### 1. Install dependencies

```bash
cd reo-docs-mcp
pip install -r requirements.txt
```

### 2. Set environment variables

```bash
export REO_API_KEY=your_api_key
export REO_USER=your_user
```

### 3. Configure Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "reo": {
      "command": "python",
      "args": ["/absolute/path/to/reo-docs-mcp/server.py"],
      "env": {
        "REO_API_KEY": "your_api_key",
        "REO_USER": "your_user"
      }
    }
  }
}
```

### 4. Restart Claude Desktop

Quit and reopen Claude Desktop. You should see "reo" in the MCP tools panel.

### Example queries

- "List all reo.dev segments"
- "Show accounts in segment seg-123"
- "Get developers for account acc-456"
- "List all audiences"
- "Show members of audience aud-789"

## Staging Deployment

### 1. Build and run with Docker

```bash
docker build -t reo-docs-mcp .
docker run -d \
  -e REO_API_KEY=your_api_key \
  -e REO_USER=your_user \
  -e MCP_TRANSPORT=http \
  -e MCP_PORT=8000 \
  -p 8000:8000 \
  reo-docs-mcp
```

### 2. Configure Claude Desktop (remote URL)

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "reo": {
      "url": "http://<staging-ip>:8000/mcp"
    }
  }
}
```

Restart Claude Desktop.
