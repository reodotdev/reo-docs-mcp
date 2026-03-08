# Reo MCP Server

MCP server that exposes reo.dev integration and ingest APIs to Claude Desktop. Once set up, you can ask Claude questions in plain English — no API calls or technical knowledge needed.

## For End Users: Connect Claude Desktop to Reo

Follow these steps once. After that, just open Claude Desktop and start asking questions.

### Step 1: Install Node.js

Claude Desktop requires Node.js version 20 or higher to connect to remote MCP servers.

**Mac:**

1. Open **Terminal** (press `Cmd + Space`, type "Terminal", press Enter)
2. Paste the following command and press Enter:

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
```

3. Close and reopen Terminal, then run:

```bash
nvm install 20
nvm use 20
```

4. Verify it worked:

```bash
node --version
```

You should see something like `v20.x.x`.

**Windows:**

1. Go to [https://nodejs.org](https://nodejs.org) and download the **LTS** version
2. Run the installer and follow the prompts
3. Open **Command Prompt** and verify:

```
node --version
```

### Step 2: Edit Claude Desktop Config

1. Open **Finder** and press `Cmd + Shift + G`
2. Paste this path and press Enter:

```
~/Library/Application Support/Claude/
```

3. Open the file `claude_desktop_config.json` with any text editor (TextEdit works)
4. Replace the contents with:

```json
{
  "mcpServers": {
    "reo": {
      "url": "https://<your-staging-url>/mcp"
    }
  }
}
```

> If the file already has other servers configured, add only the `"reo"` block inside `"mcpServers"` — don't replace the whole file.

### Step 3: Restart Claude Desktop

Quit Claude Desktop completely (`Cmd + Q`) and reopen it. You should see a hammer icon in the chat input — that means Reo tools are connected.

### What you can ask Claude

- "List all reo.dev segments"
- "Show accounts in segment seg-123"
- "Get developers for account acc-456"
- "List all audiences"
- "Show members of audience aud-789"
- "What buyers are in the high-intent segment?"

---

## Tools Available

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

---

## For Developers: Running the Server

### Local Development

```bash
pip install -r requirements.txt
export REO_API_KEY=your_api_key
export REO_USER=your_user
python server.py
```

### Staging Deployment (Docker)

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

The server will be available at `http://<host>:8000/mcp`.
