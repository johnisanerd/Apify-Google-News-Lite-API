# 📰 Google News API: bulk keyword monitoring and daily news digests in Python

> **Google News Lite API was retired in October 2026.** This repo now shows how to do the same jobs (monitor many keywords at once, build a daily news digest) with the **[Google News API](https://apify.com/johnvc/GoogleNewsAPI?fpr=9n7kx3)**. It searches the same Google News data, takes a list of keywords and a time range just like Lite did, and adds an exact publish time to every article. If you used Lite, map your input like this:

| Google News Lite API | Google News API |
|---|---|
| Actor `johnvc/google-news-lite-api` | Actor `johnvc/GoogleNewsAPI` |
| `searchTerms` | `queries` |
| `timeRange` (`hour`, `day`, `week`, `month`, `year`, `any`) | `time_range` (same values) |
| `country` | `gl` |
| `language` | `hl` |
| `maxResultsPerSearch` | `max_pages` (page 1 has 10 to 25 articles, later pages about 10) |
| `imageUrl` (output) | `thumbnail` (output) |
| `searchTerm` on each row (output) | `search_parameters.q` on each page item (output) |
| One row per article | One item per results page, articles in a `news_results` list (flatten it in Python, or use the `articles` dataset view) |
| `"result_type": "no_results"` | `"no_results": true` |

Two defaults changed: Lite used `day`, `us`, and `en` when you left those fields out, while Google News API defaults to `time_range: "any"` and no country or language. Set `time_range`, `gl`, and `hl` explicitly when you port a Lite job. Runs against the Lite Actor now fail with a migration notice, so switch the Actor ID too.

**Actor page:** [apify.com/johnvc/GoogleNewsAPI](https://apify.com/johnvc/GoogleNewsAPI?fpr=9n7kx3)
**Input schema:** [apify.com/johnvc/GoogleNewsAPI/input-schema](https://apify.com/johnvc/GoogleNewsAPI/input-schema?fpr=9n7kx3)

The Google News API searches Google News and returns structured JSON: one dataset item per results page per keyword, each holding a `news_results` list where every article has its position, title, link, source, snippet, relative date, and an absolute `published_at` time in UTC. This repo focuses on the news monitoring jobs Lite was known for: tracking a whole watchlist of brands, competitors, or topics in one run, and pulling only the last 24 hours of coverage for a daily digest.

## Video Walkthrough

[![Watch the walkthrough](https://img.youtube.com/vi/jREWahDGhJM/maxresdefault.jpg)](https://www.youtube.com/watch?v=jREWahDGhJM)

### Text walkthrough

The Google News API takes a list of keywords in `queries` and searches each one on Google News with the same settings, so one run can cover a full watchlist and the setup fee is charged once. Add `time_range: "day"` and you get only articles from the past 24 hours, sorted newest first, with a hard cutoff: the search stops at the first older article, so you never pay for pages of stale news. Each results page comes back as one dataset item with the keyword in `search_parameters.q` and the articles in `news_results`: `title`, `source`, `link`, `snippet`, `date`, `published_at`, and sometimes `thumbnail`. The Python example in this repo turns that into three everyday outputs: a per-keyword summary, a past-24-hours digest grouped by keyword, and a flat CSV with one row per article. It is the same pattern as the [Monitor brand mentions in Google News for PR](https://apify.com/johnvc/GoogleNewsAPI/examples/monitor-brand-mentions-in-google-news-for-pr?fpr=9n7kx3) task on Apify Store, run from your own code.

## Quick Start

### Prerequisites
- Python 3.11 or higher
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

4. **Run the examples**
   ```bash
   # Several keywords in one run, short summary per keyword (past week)
   uv run python google-news-api-example.py

   # Past-24-hours digest, grouped by keyword, newest first
   uv run python google-news-api-example.py --example digest

   # One row per article, written to news_articles.csv
   uv run python google-news-api-example.py --example csv
   ```

   Pick your own keywords and window with `--queries "Acme Corp" "Globex" --time-range day`. Every example defaults to `max_pages: 1` so the first run stays cheap; raise it with `--max-pages`. Add `--max-charge 0.50` to cap what a single run can spend; the Actor checks the projected cost up front and returns an error item instead of results if the cap is too low for your keywords and pages.

### Alternative: set the API key directly
```bash
export APIFY_API_TOKEN="your_api_key_here"
uv run python google-news-api-example.py
```

Sample output from `--example digest --queries OpenAI Nvidia`:

```text
Searching Google News for 2 keyword(s): OpenAI, Nvidia (time_range=day)
Run qrxZuYUHIwJLDtCah finished with status SUCCEEDED.

News digest (day): 20 new article(s)

## OpenAI (10)
- [2026-10-13 15:01:12 UTC] An Off-The-Shelf OpenAI Model Found A Google Chrome Zero-Day Exploit (Forbes)
  https://www.forbes.com/sites/the-wiretap/2026/10/13/how-an-off-the-shelf-openai-model-found-three-google-chrome-zero-days/
- [2026-10-13 15:00:11 UTC] OpenAI CEO Sam Altman Warns Against Giving AI Religious Authority (Movieguide)
  https://www.movieguide.org/news-articles/openai-ceo-sam-altman-warns-against-giving-ai-religious-authority.html
...
## Nvidia (10)
- [2026-10-13 15:04:45 UTC] Nvidia RTX 5090 Reportedly Dead, but It's So Expensive That It Doesn't Really Matter (IGN Southeast Asia)
  https://sea.ign.com/nvidia-rtx-5090/250252/nvidia-rtx-5090-reportedly-dead-but-its-so-expensive-that-it-doesnt-really-matter
...
```

## Python Examples

The full script is [google-news-api-example.py](google-news-api-example.py). The snippets below are the core of each example, trimmed so you can paste them into your own code. They use `apify-client` 3.x, where `.call()` returns a run object with `default_dataset_id`.

### 1. Monitor several keywords in one run

Put the whole watchlist in `queries`. Each keyword is searched with the same settings, every page of every keyword is its own dataset item, and the keyword rides along in `search_parameters.q`.

```python
import os

from apify_client import ApifyClient

client = ApifyClient(os.environ["APIFY_API_TOKEN"])

run = client.actor("johnvc/GoogleNewsAPI").call(run_input={
    "queries": ["OpenAI", "Nvidia", "electric vehicles"],
    "time_range": "week",
    "gl": "us",
    "hl": "en",
    "max_pages": 1,  # page 1 holds 10 to 25 articles per keyword
})

for page in client.dataset(run.default_dataset_id).iterate_items():
    keyword = page.get("search_parameters", {}).get("q")
    for article in page.get("news_results", []):
        print(f"[{keyword}] {article['title']} ({article['source']})")
```

A keyword with no coverage in the window still gets one item, with `"no_results": true` and an empty `news_results` list, so nothing in your watchlist goes missing silently.

### 2. Past-24-hours news digest

Set `time_range` to `day`. Results come newest first and stop at the first article older than 24 hours, and `published_at` gives you an exact UTC time to sort and de-duplicate on.

```python
from collections import defaultdict

run = client.actor("johnvc/GoogleNewsAPI").call(run_input={
    "queries": ["OpenAI", "Nvidia"],
    "time_range": "day",  # past 24 hours, newest first, exact cutoff
    "gl": "us",
    "hl": "en",
    "max_pages": 1,
})

digest = defaultdict(list)
for page in client.dataset(run.default_dataset_id).iterate_items():
    keyword = page.get("search_parameters", {}).get("q")
    digest[keyword].extend(page.get("news_results", []))

for keyword, articles in digest.items():
    articles.sort(key=lambda a: a.get("published_at", ""), reverse=True)
    print(f"\n## {keyword} ({len(articles)} new)")
    for a in articles:
        print(f"- {a.get('published_at')}  {a['title']} ({a['source']})")
        print(f"  {a['link']}")
```

Run it every morning on a schedule (see [Recipes](#recipes)) and you have the daily digest Lite used to power. Switch to `"hour"` for a breaking-news check every hour.

### 3. One row per article, written to CSV

Lite returned one row per article. To get that shape back, flatten `news_results` and keep the keyword on each row:

```python
import csv

fields = ["query", "position", "title", "source", "link", "snippet", "date", "published_at", "thumbnail"]

rows = []
for page in client.dataset(run.default_dataset_id).iterate_items():
    keyword = page.get("search_parameters", {}).get("q")
    for article in page.get("news_results", []):
        rows.append({"query": keyword, **{f: article.get(f, "") for f in fields[1:]}})

with open("news_articles.csv", "w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
```

No code needed for a quick export: open the run's dataset in Apify Console and pick the **News Articles** view, or call `client.dataset(run.default_dataset_id).list_items(view="articles")`. That view gives one row per article, but it drops the keyword column, so flatten in Python as above when you search several keywords at once.

## Why Use the Google News API for News Monitoring?

**A whole watchlist per run.** `queries` takes as many keywords as you need. The setup fee is charged once per run, not per keyword, so one run for 50 brand names costs less than 50 runs.

**Recent news only, with a hard cutoff.** `time_range` limits results to the past hour, day, week, month, or year. Results are sorted newest first and paging stops at the first older article, so you only pay for pages of fresh news.

**Exact publish times.** Every article has `published_at` in UTC next to the relative `date`, which makes sorting a digest and skipping articles you already saw on the last run simple.

**Country and language targeting.** Set `gl` and `hl` (plus `location`, `lr`, or `google_domain` when you need them) to monitor news in a specific market.

**Structured JSON for Google News scraping without the upkeep.** You get the same fields for every publisher, with no HTML parsing and no browser to babysit.

**MCP-ready.** Load it as a tool in [Claude Code or Claude Cowork](https://claude.ai/referral/uIlpa7nPLg) (free trial), Claude on the web, Cursor, or ChatGPT and ask for today's headlines in plain language.

## Recipes

Ready-made tasks on Apify Store that match the jobs in this repo:

- [Monitor brand mentions in Google News for PR](https://apify.com/johnvc/GoogleNewsAPI/examples/monitor-brand-mentions-in-google-news-for-pr?fpr=9n7kx3): put your brand and product names in `queries` and get every mention with source, link, snippet, and date. In this repo: `uv run python google-news-api-example.py --queries "Your Brand" "Your Product"`.
- [Track Nvidia news headlines by keyword](https://apify.com/johnvc/GoogleNewsAPI/examples/track-nvidia-news-headlines-by-keyword?fpr=9n7kx3): one company, structured headlines for daily monitoring. In this repo: `--example digest --queries Nvidia`.
- [Export Google News Results to CSV](https://apify.com/johnvc/GoogleNewsAPI/examples/export-google-news-results-to-csv?fpr=9n7kx3): articles as a spreadsheet for Excel or Google Sheets. In this repo: `--example csv`.
- [Get Google News results by keyword as JSON](https://apify.com/johnvc/GoogleNewsAPI/examples/get-google-news-results-by-keyword-as-json?fpr=9n7kx3): the raw page items, ready for your own pipeline.
- [Pull Google News headlines into Claude via MCP](https://apify.com/johnvc/GoogleNewsAPI/examples/pull-google-news-headlines-into-claude-via-mcp?fpr=9n7kx3): the same data inside a chat. See the MCP sections below.

**Schedule tip:** for a daily digest, save your input (for example `queries` plus `time_range: "day"`) as a task in Apify Console, then add a schedule with the cron string `0 7 * * *` to run it every morning at 7 AM. Use `0 */6 * * *` to check every six hours, or `0 9 * * 1` for a Monday roundup. One schedule can trigger many tasks.

## Usage Examples

### Bulk keyword monitoring
```json
{
  "queries": ["OpenAI", "Nvidia", "electric vehicles"],
  "time_range": "week",
  "gl": "us",
  "hl": "en",
  "max_pages": 1
}
```

### Daily digest for one market
```json
{
  "queries": ["Siemens", "Volkswagen", "SAP"],
  "time_range": "day",
  "gl": "de",
  "hl": "de",
  "filter": "1",
  "max_pages": 2
}
```

## Input Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `q` | `string` | `q` or `queries` | - | One search query, e.g. `technology news`. |
| `queries` | `array` | `q` or `queries` | - | Several search queries in one run, e.g. `["Nvidia", "OpenAI", "Anthropic"]`. Each is searched separately with the same settings; repeats are skipped. The setup fee is charged once per run. |
| `time_range` | `string` | No | `any` | Only articles published within this window: `any`, `hour`, `day`, `week`, `month`, or `year`. Anything other than `any` sorts newest first and stops at the first older article. |
| `location` | `string` | No | - | Location for localized results, e.g. `Austin, TX, Texas, United States`. |
| `google_domain` | `string` | No | `google.com` | Google domain to search, e.g. `google.co.uk`. |
| `gl` | `string` | No | - | Country code (ISO 3166-1 alpha-2, lowercase), e.g. `us`, `gb`, `de`. |
| `hl` | `string` | No | - | Language code (ISO 639-1, lowercase), e.g. `en`, `es`, `de`. |
| `lr` | `string` | No | - | Language restriction, e.g. `lang_en`. |
| `safe` | `string` | No | `off` | Safe search: `active` or `off`. |
| `nfpr` | `string` | No | `0` | `1` excludes results from auto-corrected queries. |
| `filter` | `string` | No | `0` | `1` filters duplicate content. |
| `max_pages` | `integer` | No | `1` | Pages to fetch per query; `0` fetches all available pages (up to 30). Page 1 typically has 10 to 25 articles, later pages about 10. Each page is billed separately. |
| `output_file` | `string` | No | auto | Optional filename for a JSON copy of the results. |

## Output Format

One dataset item per results page per query. This is a real item from the digest run above, with `news_results` trimmed to two articles:

```json
{
  "search_parameters": {
    "q": "OpenAI",
    "gl": "us",
    "hl": "en",
    "safe": "off",
    "nfpr": 0,
    "filter": 0,
    "time_range": "day",
    "max_pages": 1
  },
  "search_metadata": {
    "total_results": 48500000,
    "news_count": 10,
    "pages_processed": 1,
    "max_pages_set": 1,
    "pagination_limit_reached": true
  },
  "search_information": {
    "query_displayed": "OpenAI",
    "total_results": 48500000
  },
  "search_timestamp": "2026-10-13T15:07:37.046873",
  "page_number": 1,
  "news_results": [
    {
      "position": 1,
      "title": "An Off-The-Shelf OpenAI Model Found A Google Chrome Zero-Day Exploit",
      "link": "https://www.forbes.com/sites/the-wiretap/2026/10/13/how-an-off-the-shelf-openai-model-found-three-google-chrome-zero-days/",
      "source": "Forbes",
      "snippet": "Xbow claims a $250000 prize after using GPT-5.6 to find multiple exploits in the popular Google browser's security.",
      "date": "6 minutes ago",
      "published_at": "2026-10-13 15:01:12 UTC"
    },
    {
      "position": 2,
      "title": "OpenAI CEO Sam Altman Warns Against Giving AI Religious Authority",
      "link": "https://www.movieguide.org/news-articles/openai-ceo-sam-altman-warns-against-giving-ai-religious-authority.html",
      "source": "Movieguide",
      "snippet": "OpenAI CEO Sam Altman wants people to keep their judgment firmly in human hands, not hand it over to a chatbot.",
      "date": "7 minutes ago",
      "published_at": "2026-10-13 15:00:11 UTC"
    }
  ]
}
```

Article fields:

- `position`: rank on the results page (1-indexed)
- `title`, `link`, `source`: headline, article URL, and publisher
- `snippet`: short excerpt; some page-1 top stories come without one
- `date`: relative time, e.g. `3 hours ago`
- `published_at`: absolute time in UTC, e.g. `2026-10-13 15:01:12 UTC`
- `thumbnail`: image URL, only when Google shows one (Lite called this `imageUrl`)

A query with no articles in the window yields one item with `"no_results": true`, an empty `news_results` list, and no page fee.

---

## Use from n8n

The Google News API is also an n8n community node: **[n8n-nodes-google-news-api](https://www.npmjs.com/package/n8n-nodes-google-news-api)**. In n8n, go to Settings, Community Nodes, install `n8n-nodes-google-news-api`, and chain a Schedule Trigger, the Google News node, and a Slack or email node for a no-code daily digest.

## Use it as a Claude or agent skill

Two open agent skills wrap this API around ready-made workflows and install in [Claude Code](https://claude.ai/referral/uIlpa7nPLg) (free trial), Cursor, and other skills-compatible agents:

- [News monitoring skill](https://github.com/johnisanerd/claude-skill-news-monitoring): a polled brand and topic watch with de-duplication and digests. `npx skills add johnisanerd/claude-skill-news-monitoring`
- [Google News API skill](https://github.com/johnisanerd/claude-skill-google-news-api): search Google News and get structured articles as JSON. `npx skills add johnisanerd/claude-skill-google-news-api`

---

## Use as an MCP tool

You can load the Google News API as an MCP tool so an assistant runs it for you. This MCP server URL preloads just this one Actor, plus Apify's `actors` and `docs` helper tools:

```
https://mcp.apify.com/?tools=actors,docs,johnvc/GoogleNewsAPI
```

Authenticate with OAuth in the browser when offered, or with your Apify API token (the same `APIFY_API_TOKEN` the Python example uses). Get a token at https://console.apify.com/settings/integrations and a free Apify account at https://apify.com?fpr=9n7kx3 .

Once it is connected, try a prompt like: *"Use the Google News API to get the past 24 hours of news for OpenAI, Nvidia, and Anthropic, then write me a short digest with links."* The assistant fills in `queries` and `time_range` for you.

## Install in Claude Cowork Desktop

![Install in Claude Cowork Desktop](https://raw.githubusercontent.com/johnisanerd/ApifyPublicData/main/assets/guides/install_mcp_into_claude_desktop.png)

Cowork is the desktop app's automation mode. To give it the Google News API as a tool, add the Apify MCP server as a connector.

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
        "https://mcp.apify.com/?tools=actors,docs,johnvc/GoogleNewsAPI"
      ]
    }
  }
}
```

3. Restart the app. When Cowork first calls the tool, complete the OAuth prompt in your browser, or add your Apify API token in the connector settings to skip OAuth.
4. In a Cowork chat, confirm the tool is available and ask it to run the Google News API.

Download the desktop app and start a free trial: https://claude.ai/referral/uIlpa7nPLg
More help: https://docs.apify.com/platform/integrations/claude-desktop

---

## Install in Claude Code

![Install in Claude Code](https://raw.githubusercontent.com/johnisanerd/ApifyPublicData/main/assets/guides/install_mcp_into_claude_code.png)

Claude Code is the command-line tool. Add the Actor's MCP server with one command:

```bash
claude mcp add --transport http apify \
  "https://mcp.apify.com/?tools=actors,docs,johnvc/GoogleNewsAPI"
```

To use a token instead of browser OAuth:

```bash
claude mcp add --transport http apify \
  "https://mcp.apify.com/?tools=actors,docs,johnvc/GoogleNewsAPI" \
  --header "Authorization: Bearer YOUR_APIFY_TOKEN"
```

Then verify with `claude mcp list`, or run `/mcp` inside a session. Ask Claude Code to call the Google News API.

Try Claude Code free: https://claude.ai/referral/uIlpa7nPLg
Claude Code MCP docs: https://code.claude.com/docs/en/mcp

---

## Install in Claude (website)

![Install in Claude (website)](https://raw.githubusercontent.com/johnisanerd/ApifyPublicData/main/assets/guides/install_mcp_into_claude_ai.png)

On claude.ai you add Apify as a connector, then enable just this Actor's tool.

1. Go to **Settings → Connectors → Browse connectors** and search for **Apify MCP server**. Install it (enable or update if prompted).
2. When connecting, authenticate with your Apify API token, and enable the tool `johnvc/GoogleNewsAPI`.
3. In any chat, open **+ → Connectors** and turn on **Apify**.
4. Alternatively, choose **Add custom connector** and paste the full MCP URL `https://mcp.apify.com/?tools=actors,docs,johnvc/GoogleNewsAPI`, using OAuth when prompted.
5. Ask Claude to run the Google News API.

Open Claude on the web: https://claude.ai/referral/uIlpa7nPLg

---

## Install in Cursor

![Install in Cursor](https://raw.githubusercontent.com/johnisanerd/ApifyPublicData/main/assets/guides/install_mcp_into_cursor.png)

Cursor reads MCP servers from a project file at `.cursor/mcp.json`.

1. In your project, create `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "apify": {
      "url": "https://mcp.apify.com/?tools=actors,docs,johnvc/GoogleNewsAPI"
    }
  }
}
```

2. If you prefer token auth over browser OAuth, add a header:

```json
{
  "mcpServers": {
    "apify": {
      "url": "https://mcp.apify.com/?tools=actors,docs,johnvc/GoogleNewsAPI",
      "headers": { "Authorization": "Bearer YOUR_APIFY_TOKEN" }
    }
  }
}
```

3. Open **Cursor → Settings → MCP** and confirm the **apify** server is connected (green dot).
4. In Composer or Chat, ask Cursor to call the Google News API.

New to Cursor? Get it here: https://cursor.com/referral?code=XQP4VBLI3NNX

---

## Install in ChatGPT

![Install in ChatGPT](https://raw.githubusercontent.com/johnisanerd/ApifyPublicData/main/assets/guides/install_mcp_into_ChatGPT.png)

ChatGPT connects to the Apify MCP server through Developer mode (available on ChatGPT Pro, Plus, Business, Enterprise, and Education plans).

1. Click your profile icon, then go to **Settings > Apps**. If you do not see a **Create app** button, open **Advanced settings** and enable **Developer mode**.
2. Click **Create app** and fill out the form:
   - **Name:** Apify
   - **MCP Server URL:** `https://mcp.apify.com/?tools=actors,docs,johnvc/GoogleNewsAPI`
   - **Authentication:** OAuth
3. Click **Create** and authorize the connection with Apify.
4. To use the app in a conversation, click **+** in the chat, choose **Developer mode**, and select **Apify**.

More help: https://docs.apify.com/platform/integrations/mcp

---

<!-- ask-ai:start -->
## 🤖 Ask an AI assistant about this Actor

Open a ready-to-send prompt about the Google News API in the AI of your choice:

- 💬 [ChatGPT](https://chatgpt.com/?q=Using%20the%20Google%20News%20API%20on%20Apify%20%28https://apify.com/johnvc/GoogleNewsAPI?fpr=9n7kx3%29%2C%20walk%20me%20through%20this%20use%20case:%20%22Monitor%20brand%20mentions%20in%20Google%20News%20for%20PR%22.%20Show%20me%20the%20input%20JSON%2C%20the%20output%20fields%2C%20and%20how%20to%20automate%20it%20with%20the%20API%20or%20MCP.)
- 🧠 [Claude](https://claude.ai/new?q=Using%20the%20Google%20News%20API%20on%20Apify%20%28https://apify.com/johnvc/GoogleNewsAPI?fpr=9n7kx3%29%2C%20walk%20me%20through%20this%20use%20case:%20%22Monitor%20brand%20mentions%20in%20Google%20News%20for%20PR%22.%20Show%20me%20the%20input%20JSON%2C%20the%20output%20fields%2C%20and%20how%20to%20automate%20it%20with%20the%20API%20or%20MCP.)
- 🔍 [Perplexity](https://www.perplexity.ai/search?q=Using%20the%20Google%20News%20API%20on%20Apify%20%28https://apify.com/johnvc/GoogleNewsAPI?fpr=9n7kx3%29%2C%20walk%20me%20through%20this%20use%20case:%20%22Monitor%20brand%20mentions%20in%20Google%20News%20for%20PR%22.%20Show%20me%20the%20input%20JSON%2C%20the%20output%20fields%2C%20and%20how%20to%20automate%20it%20with%20the%20API%20or%20MCP.)
- 🅒 [Copilot](https://copilot.microsoft.com/?q=Using%20the%20Google%20News%20API%20on%20Apify%20%28https://apify.com/johnvc/GoogleNewsAPI?fpr=9n7kx3%29%2C%20walk%20me%20through%20this%20use%20case:%20%22Monitor%20brand%20mentions%20in%20Google%20News%20for%20PR%22.%20Show%20me%20the%20input%20JSON%2C%20the%20output%20fields%2C%20and%20how%20to%20automate%20it%20with%20the%20API%20or%20MCP.)
<!-- ask-ai:end -->

## ❓ FAQ

### What happened to Google News Lite API?

It was retired in October 2026, and every run of `johnvc/google-news-lite-api` now fails with a migration notice. Everything it did (several search terms per run, time ranges, country and language targeting, article images) is available in the [Google News API](https://apify.com/johnvc/GoogleNewsAPI?fpr=9n7kx3), which searches the same Google News data. Use the mapping table at the top of this README to port your input.

### How do I move my Lite code to the Google News API?

Change the Actor ID to `johnvc/GoogleNewsAPI`, rename the input fields (`searchTerms` to `queries`, `timeRange` to `time_range`, `country` to `gl`, `language` to `hl`, `maxResultsPerSearch` to `max_pages`), and set `time_range`, `gl`, and `hl` explicitly because their defaults changed. On the output side, loop over each item's `news_results` instead of reading one article per item, read the keyword from `search_parameters.q`, and read `thumbnail` where you used `imageUrl`. The flatten snippet in [Python Examples](#3-one-row-per-article-written-to-csv) gives you Lite's one-row-per-article shape back.

### Can I monitor many keywords at once?

Yes. Put them all in `queries`, for example `["Acme Corp", "Globex", "Initech"]`. Each keyword is searched with the same time range, country, and language, and the setup fee is charged once per run, so batching keywords into one run is the cheapest way to watch a long list.

### How do I get only the last 24 hours of news?

Set `time_range` to `day` (or `hour` for the past hour). Results come newest first, each article has an exact `published_at` time, and the search stops at the first article older than the window, so you only pay for pages of recent news.

### How much does the Google News API cost?

It is pay per use with no subscription: a small setup fee once per run plus a fee per results page. Lite charged per article; here you control cost with `max_pages` and by batching keywords into one run. A keyword with no results costs no page fee. See the [Actor page](https://apify.com/johnvc/GoogleNewsAPI?fpr=9n7kx3) for current rates, and pass `--max-charge` to the example script to cap a run.

### Is this a Google News scraper?

It does the job of a Google News scraper, but you call it like an API: send keywords, get structured JSON back, with no HTML parsing, proxies, or browser to maintain. That makes Google News scraping for news monitoring a few lines of Python, as shown above.

### Can I run a daily news digest on a schedule?

Yes. Save your input as a task in Apify Console, then attach a schedule such as `0 7 * * *` for every morning at 7 AM. Pair it with a webhook, the n8n node, or the Python digest example to send the results to Slack or email.

### Can I use it from Claude, Cursor, or ChatGPT?

Yes, through the Apify MCP server at `https://mcp.apify.com/?tools=actors,docs,johnvc/GoogleNewsAPI`. Setup steps for [Claude Cowork and Claude Code](https://claude.ai/referral/uIlpa7nPLg) (free trial), Claude on the web, Cursor, and ChatGPT are above.

### Why does this repo still have "Lite" in its name?

The repo kept its name and history so existing links and clones keep working. The code and docs now target the Google News API.

---

## 🌐 About Alpha OSINT

This example repo is part of [Alpha OSINT](https://www.alphaosint.com), toolset of financial and operations data sources and APIs.
See the [Google News API source page](https://www.alphaosint.com/sources/google-news-api/) for related tools and use cases.
For support or requests for this actor, please start a ticket [directly on our support page](https://apify.com/johnvc/GoogleNewsAPI/issues/open?fpr=9n7kx3).

[**Made with care**](https://apify.com/johnvc?fpr=9n7kx3)

*Use the Google News API to power news monitoring, brand tracking, and daily digests with reliable, structured results.*

Last Updated: 2026.10.27
