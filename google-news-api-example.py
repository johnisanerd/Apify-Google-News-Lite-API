"""
Google News API: bulk keyword monitoring and daily news digest example.

Actor page:   https://apify.com/johnvc/GoogleNewsAPI?fpr=9n7kx3
Input schema: https://apify.com/johnvc/GoogleNewsAPI/input-schema?fpr=9n7kx3
Free Apify API key: https://apify.com?fpr=9n7kx3

This script calls the Google News API Apify Actor from Python. It searches
several keywords in a single run with `queries`, limits results to a recent
window with `time_range`, and reads the structured JSON that comes back:
one dataset item per results page per query, each with a `news_results` list
of articles (title, link, source, snippet, date, published_at, thumbnail).

Three examples, picked with --example:

  monitor  (default) one run, several keywords, a short summary per keyword
  digest   a past-24-hours digest, grouped by keyword, newest first
  csv      flatten every article to one row and write news_articles.csv

Usage:
  uv run python google-news-api-example.py
  uv run python google-news-api-example.py --example digest
  uv run python google-news-api-example.py --example csv --out my_news.csv
  uv run python google-news-api-example.py --queries "OpenAI" "Nvidia" --time-range day

Put your token in .env as APIFY_API_TOKEN (see .env.example), or export
APIFY_API_TOKEN (APIFY_TOKEN also works) before running.
"""

import argparse
import csv
import os
from collections import defaultdict
from decimal import Decimal

from apify_client import ApifyClient
from dotenv import load_dotenv

ACTOR_ID = "johnvc/GoogleNewsAPI"

# Inputs are kept small on purpose so a first run stays inexpensive:
# a few keywords and max_pages=1 (page 1 holds 10 to 25 articles per keyword).
# The Actor charges a small setup fee once per run plus a fee per results page,
# so adding keywords to one run is cheaper than starting one run per keyword.
# Raise max_pages or add keywords once you know your budget.
DEFAULT_QUERIES = ["OpenAI", "Nvidia", "electric vehicles"]

CSV_FIELDS = [
    "query",
    "page_number",
    "position",
    "title",
    "source",
    "link",
    "snippet",
    "date",
    "published_at",
    "thumbnail",
]


def get_client() -> ApifyClient:
    """Build an Apify client from APIFY_API_TOKEN (or APIFY_TOKEN)."""
    load_dotenv()
    token = os.getenv("APIFY_API_TOKEN") or os.getenv("APIFY_TOKEN")
    if not token:
        raise SystemExit(
            "No Apify token found. Copy .env.example to .env and add your key, "
            "or run: export APIFY_API_TOKEN=your_api_key_here\n"
            "Get a free key at https://apify.com?fpr=9n7kx3"
        )
    return ApifyClient(token)


def build_input(queries: list[str], time_range: str, max_pages: int, gl: str, hl: str) -> dict:
    """Map the command-line options onto the Actor's input fields."""
    return {
        "queries": queries,        # several keywords, one run, setup fee charged once
        "time_range": time_range,  # any / hour / day / week / month / year
        "gl": gl,                  # country code, e.g. us, gb, ca
        "hl": hl,                  # language code, e.g. en, es, fr
        "max_pages": max_pages,    # pages per keyword; kept at 1 for a cheap first run
    }


def run_search(client: ApifyClient, run_input: dict, max_charge: Decimal | None = None) -> list[dict]:
    """Run the Actor, wait for it to finish, and return every dataset item.

    max_charge is an optional spending cap in USD for this run. The Actor checks
    the projected cost (setup fee plus pages for every query) before it starts,
    and returns an error item instead of results if the cap is too low.
    """
    print(f"Searching Google News for {len(run_input['queries'])} keyword(s): "
          f"{', '.join(run_input['queries'])} (time_range={run_input['time_range']})")
    run = client.actor(ACTOR_ID).call(
        run_input=run_input,
        max_total_charge_usd=max_charge,
        logger=None,  # keep the console quiet; remove to stream the Actor log
    )
    if run is None:
        raise SystemExit("The Actor run did not start. Check your API token and inputs.")
    print(f"Run {run.id} finished with status {run.status}.")
    return list(client.dataset(run.default_dataset_id).iterate_items())


def flatten_articles(pages: list[dict]) -> list[dict]:
    """Turn page items into one row per article, tagged with its keyword.

    Each dataset item is one results page for one query. The query lives in
    search_parameters.q, and the articles live in the news_results list.
    """
    rows = []
    for page in pages:
        query = (page.get("search_parameters") or {}).get("q", "")
        if page.get("error"):
            print(f"  Error for '{query}': {page.get('error_message')}")
            continue
        if page.get("no_results"):
            print(f"  No articles for '{query}' in this time range.")
            continue
        for article in page.get("news_results") or []:
            rows.append({
                "query": query,
                "page_number": page.get("page_number"),
                "position": article.get("position"),
                "title": article.get("title", ""),
                "source": article.get("source", ""),
                "link": article.get("link", ""),
                # Some page-1 top stories come without a snippet.
                "snippet": (article.get("snippet") or "").replace("\n", " ").strip(),
                "date": article.get("date", ""),
                "published_at": article.get("published_at", ""),
                "thumbnail": article.get("thumbnail", ""),
            })
    return rows


def group_by_query(rows: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[row["query"]].append(row)
    return grouped


def run_monitor(client: ApifyClient, args: argparse.Namespace) -> None:
    """Several keywords in one run, with a short summary per keyword."""
    run_input = build_input(args.queries, args.time_range or "week", args.max_pages, args.gl, args.hl)
    rows = flatten_articles(run_search(client, run_input, args.max_charge))
    print(f"\n{len(rows)} article(s) across {len(args.queries)} keyword(s).\n")

    for query, articles in group_by_query(rows).items():
        sources = {a["source"] for a in articles if a["source"]}
        print(f"== {query}: {len(articles)} articles from {len(sources)} sources")
        for article in articles[:3]:
            print(f"   {article['position']}. {article['title']}")
            print(f"      {article['source']} | {article['date']} | {article['link']}")
        print()


def run_digest(client: ApifyClient, args: argparse.Namespace) -> None:
    """Past-24-hours digest: newest first, grouped by keyword."""
    run_input = build_input(args.queries, args.time_range or "day", args.max_pages, args.gl, args.hl)
    rows = flatten_articles(run_search(client, run_input, args.max_charge))

    print(f"\nNews digest ({run_input['time_range']}): {len(rows)} new article(s)\n")
    for query, articles in group_by_query(rows).items():
        # published_at is an absolute UTC time ("2026-10-10 03:34:00 UTC"),
        # so a plain string sort puts the newest article first.
        articles.sort(key=lambda a: a["published_at"] or "", reverse=True)
        print(f"## {query} ({len(articles)})")
        for article in articles:
            print(f"- [{article['published_at'] or article['date']}] {article['title']} ({article['source']})")
            print(f"  {article['link']}")
        print()


def run_csv(client: ApifyClient, args: argparse.Namespace) -> None:
    """Flatten news_results to one row per article and write a CSV file."""
    run_input = build_input(args.queries, args.time_range or "week", args.max_pages, args.gl, args.hl)
    rows = flatten_articles(run_search(client, run_input, args.max_charge))

    with open(args.out, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nWrote {len(rows)} article row(s) to {args.out}")
    for row in rows[:5]:
        print(f"  {row['query']} | {row['source']} | {row['title'][:80]}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Google News API examples (bulk keywords, digests, CSV).")
    parser.add_argument("--example", choices=["monitor", "digest", "csv"], default="monitor",
                        help="Which example to run (default: monitor).")
    parser.add_argument("--queries", nargs="+", default=DEFAULT_QUERIES,
                        help="Keywords to search in one run.")
    parser.add_argument("--time-range", choices=["any", "hour", "day", "week", "month", "year"],
                        default=None,
                        help="Only articles from this window (default: week, or day for the digest).")
    parser.add_argument("--max-pages", type=int, default=1,
                        help="Results pages per keyword (default: 1, the cheapest).")
    parser.add_argument("--gl", default="us", help="Country code (default: us).")
    parser.add_argument("--hl", default="en", help="Language code (default: en).")
    parser.add_argument("--out", default="news_articles.csv", help="CSV path for --example csv.")
    parser.add_argument("--max-charge", type=Decimal, default=None,
                        help="Optional spending cap for the run in USD, e.g. 0.50.")
    args = parser.parse_args()

    client = get_client()
    {"monitor": run_monitor, "digest": run_digest, "csv": run_csv}[args.example](client, args)


if __name__ == "__main__":
    main()
