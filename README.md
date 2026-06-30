# 📰 Google News Lite API: Fast Google News headlines and snippets as JSON

> The most efficient, low-cost, developer-friendly way to monitor Google News.

**Actor page:** [apify.com/johnvc/google-news-lite-api](https://apify.com/johnvc/google-news-lite-api?fpr=9n7kx3)
**Input schema:** [apify.com/johnvc/google-news-lite-api/input-schema](https://apify.com/johnvc/google-news-lite-api/input-schema?fpr=9n7kx3)

Search Google News for one or more terms and get back the matching headlines and snippets as structured JSON, one row per article: title, link, source, snippet, date, and image. Filter by time range, country, and language. Pay per article with no setup fee, so high-volume monitoring stays cheap and predictable.

## Video Walkthrough

[![Watch the walkthrough](https://img.youtube.com/vi/jREWahDGhJM/maxresdefault.jpg)](https://www.youtube.com/watch?v=jREWahDGhJM)

## Quick Start

### Prerequisites
- Python 3.10 or higher
- An Apify account and API key ([get a free key here](https://apify.com?fpr=9n7kx3))

1. **Clone the repository**
   ```bash
   git clone https://github.com/johnisanerd/Apify-Google-News-Lite-API.git
   cd Apify-Google-News-Lite-API
   ```

2. **Install dependencies with UV**
   ```bash
   # Install UV if you do not have it:
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Install project dependencies:
   uv sync
   ```

3. **Configure your API key**
   ```bash
   cp .env.example .env
   # Edit .env and add your Apify API key
   # Get your free API key at: https://apify.com?fpr=9n7kx3
   ```

4. **Run the example**
   ```bash
   uv run python google-news-lite-api-example.py
   ```

### Alternative: set the API key directly
```bash
export APIFY_API_TOKEN="your_api_key_here"
uv run python google-news-lite-api-example.py
```

## Why Use This Google News Lite API?

**Clean, structured output.** Every article comes back as one JSON row with a consistent set of fields, ready to drop into a database, a report, or an LLM pipeline. No HTML parsing.

**One term or many.** Pass a list of `searchTerms` and the API searches each one separately, tagging every row with the term it matched. Perfect for monitoring several topics, brands, or competitors in a single run.

**Pay per article, no setup fee.** Pricing is a flat $0.002 per article, which is $2 per 1,000 articles. There is no per-run start fee and no subscription, so a search that returns nothing costs nothing.

**Time, country, and language targeting.** Limit results to the past hour, day, week, month, or year, and choose the country (`country`) and language (`language`).

**De-duplicated.** Results are de-duplicated by link within each search term, so you do not pay for or process the same article twice.

**MCP-ready.** Load it as a tool in Claude Cowork, Claude Code, Claude on the web, and Cursor (see below) and ask for the latest headlines in plain language.

## Features

### Core Capabilities
- One dataset row per article, tagged with the `searchTerm` it matched
- Headline (`title`), `link`, `source`, `snippet`, `date`, and `imageUrl` on every article
- Batch input: search many terms in one run via `searchTerms`
- Time-range filter: `hour`, `day`, `week`, `month`, `year`, or `any`
- Country and language targeting, plus a configurable result cap per term

### Data Quality
- Clean, typed JSON output with a stable `result_type` field
- Link de-duplication within each search term
- A `no_results` row for any term with no coverage, so nothing fails silently

## Usage Examples

### Basic Example
```json
{
  "searchTerms": ["OpenAI"],
  "timeRange": "day"
}
```

### Advanced Example
```json
{
  "searchTerms": ["Apple Vision Pro", "electric vehicles", "OpenAI"],
  "timeRange": "week",
  "country": "us",
  "language": "en",
  "maxResultsPerSearch": 50
}
```

## Input Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `searchTerms` | `list[str]` | yes | - | One or more search terms. Each is searched separately; one row per article. |
| `timeRange` | `str` | no | `day` | How recent results must be: `hour`, `day`, `week`, `month`, `year`, or `any`. |
| `country` | `str` | no | `us` | Country code (ISO 3166-1), e.g. `us`, `gb`, `ca`. |
| `language` | `str` | no | `en` | Language code (ISO 639-1), e.g. `en`, `es`, `fr`. |
| `maxResultsPerSearch` | `int` | no | `100` | Maximum articles per search term, from 1 to 100. |

## Output Format

One row per article. Each item has a `result_type` of `news_article`, `no_results`, or `error`.

```json
{
  "result_type": "news_article",
  "searchTerm": "OpenAI",
  "position": 1,
  "title": "OpenAI announces new model with improved reasoning",
  "link": "https://www.example-news.com/openai-new-model",
  "source": "Example News",
  "snippet": "The company says the update brings significant gains on multi-step reasoning and coding tasks.",
  "date": "3 hours ago",
  "imageUrl": "https://www.example-news.com/img/openai.jpg",
  "country": "us",
  "language": "en",
  "timeRange": "day",
  "fetchedAt": "2026-05-29T12:00:00+00:00"
}
```

When a term has no coverage in the chosen `timeRange`, its row comes back with `"result_type": "no_results"` and a short `note`. Widen the range (for example to `week` or `any`) to get articles.

---

## Install in Claude Cowork Desktop

![Install in Claude Cowork Desktop](https://raw.githubusercontent.com/johnisanerd/ApifyPublicData/main/assets/guides/install_mcp_into_claude_desktop.png)

Cowork is the desktop app's automation mode. To give it the Google News Lite API as a tool, add the Apify MCP server as a connector.

1. Open the Claude desktop app and go to **Settings → Connectors** (or **Settings → Developer → Edit Config** to edit `claude_desktop_config.json` directly).
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
2. Add the Apify MCP server, preloaded with only this Actor:

```json
{
  "mcpServers": {
    "apify": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "https://mcp.apify.com/?tools=actors,docs,johnvc/google-news-lite-api"
      ]
    }
  }
}
```

3. Restart the app. When Cowork first calls the tool, complete the OAuth prompt in your browser, or add your Apify API token in the connector settings to skip OAuth.
4. In a Cowork chat, confirm the tool is available and ask it to run the Google News Lite API.

Download the desktop app and start a free trial: https://claude.ai/referral/uIlpa7nPLg
More help: https://docs.apify.com/platform/integrations/claude-desktop

---

## Install in Claude Code

![Install in Claude Code](https://raw.githubusercontent.com/johnisanerd/ApifyPublicData/main/assets/guides/install_mcp_into_claude_code.png)

Claude Code is the command-line tool. Add the Actor's MCP server with one command:

```bash
claude mcp add --transport http apify \
  "https://mcp.apify.com/?tools=actors,docs,johnvc/google-news-lite-api"
```

To use a token instead of browser OAuth:

```bash
claude mcp add --transport http apify \
  "https://mcp.apify.com/?tools=actors,docs,johnvc/google-news-lite-api" \
  --header "Authorization: Bearer YOUR_APIFY_TOKEN"
```

Then verify with `claude mcp list`, or run `/mcp` inside a session. Ask Claude Code to call the Google News Lite API.

Try Claude Code free: https://claude.ai/referral/uIlpa7nPLg
Claude Code MCP docs: https://code.claude.com/docs/en/mcp

---

## Install in Claude (website)

![Install in Claude (website)](https://raw.githubusercontent.com/johnisanerd/ApifyPublicData/main/assets/guides/install_mcp_into_claude_ai.png)

On claude.ai you add Apify as a connector, then enable just this Actor's tool.

1. Go to **Settings → Connectors → Browse connectors** and search for **Apify MCP server**. Install it (enable or update if prompted).
2. When connecting, authenticate with your Apify API token, and enable the tool `johnvc/google-news-lite-api`.
3. In any chat, open **+ → Connectors** and turn on **Apify**.
4. Alternatively, choose **Add custom connector** and paste the full MCP URL `https://mcp.apify.com/?tools=actors,docs,johnvc/google-news-lite-api`, using OAuth when prompted.
5. Ask Claude to run the Google News Lite API.

Open Claude on the web: https://claude.ai

---

## Install in Cursor

![Install in Cursor](https://raw.githubusercontent.com/johnisanerd/ApifyPublicData/main/assets/guides/install_mcp_into_cursor.png)

Cursor reads MCP servers from a project file at `.cursor/mcp.json`.

1. In your project, create `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "apify": {
      "url": "https://mcp.apify.com/?tools=actors,docs,johnvc/google-news-lite-api"
    }
  }
}
```

2. If you prefer token auth over browser OAuth, add a header:

```json
{
  "mcpServers": {
    "apify": {
      "url": "https://mcp.apify.com/?tools=actors,docs,johnvc/google-news-lite-api",
      "headers": { "Authorization": "Bearer YOUR_APIFY_TOKEN" }
    }
  }
}
```

3. Open **Cursor → Settings → MCP** and confirm the **apify** server is connected (green dot).
4. In Composer or Chat, ask Cursor to call the Google News Lite API.

New to Cursor? Get it here: https://cursor.com/referral?code=XQP4VBLI3NNX

---

## Install in ChatGPT

![Install in ChatGPT](https://raw.githubusercontent.com/johnisanerd/ApifyPublicData/main/assets/guides/install_mcp_into_ChatGPT.png)

ChatGPT connects to the Apify MCP server through Developer mode (available on ChatGPT Pro, Plus, Business, Enterprise, and Education plans).

1. Click your profile icon, then go to **Settings > Apps**. If you do not see a **Create app** button, open **Advanced settings** and enable **Developer mode**.
2. Click **Create app** and fill out the form:
   - **Name:** Apify
   - **MCP Server URL:** `https://mcp.apify.com/?tools=actors,docs,johnvc/google-news-lite-api`
   - **Authentication:** OAuth
3. Click **Create** and authorize the connection with Apify.
4. To use the app in a conversation, click **+** in the chat, choose **Developer mode**, and select **Apify**.

More help: https://docs.apify.com/platform/integrations/mcp

---

[**Made with care**](https://apify.com/johnvc?fpr=9n7kx3)

*Use the Google News Lite API to power your media monitoring with reliable, structured results.*

Last Updated: 2026.06.30
