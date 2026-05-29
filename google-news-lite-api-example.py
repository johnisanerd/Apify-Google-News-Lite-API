"""
Google News Lite API: A Quick Start Example
See more at: https://apify.com/johnvc/google-news-lite-api?fpr=9n7kx3
Input schema: https://apify.com/johnvc/google-news-lite-api/input-schema?fpr=9n7kx3

This script shows how to call the Google News Lite API on Apify from Python and
read its structured JSON output. The API searches Google News for one or more
terms and returns one row per article (title, link, source, snippet, date, and
image). It exercises several input parameters so you can see what is
configurable, while keeping the run small so your first call stays cheap.

Get your free Apify API key at: https://apify.com?fpr=9n7kx3
"""

import os

from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()

# Initialize the Apify client with your API token (read from .env)
client = ApifyClient(os.getenv("APIFY_API_TOKEN"))

# Build the Actor input.
# Inputs are kept small (one search term, a few results) to keep this first run
# inexpensive: you are billed per article returned. Raise "maxResultsPerSearch"
# (up to 100) and add more terms to "searchTerms" once you know your budget.
run_input = {
    "searchTerms": ["OpenAI"],   # add more terms to monitor several topics at once
    "timeRange": "day",          # hour / day / week / month / year / any
    "country": "us",             # ISO 3166-1, e.g. us, gb, ca
    "language": "en",            # ISO 639-1, e.g. en, es, fr
    "maxResultsPerSearch": 5,    # 1-100; kept small to keep this first run cheap
}

# Run the Actor and wait for it to finish
run = client.actor("johnvc/google-news-lite-api").call(run_input=run_input)

# Read structured results from the run's default dataset (one row per article)
items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
print(f"Returned {len(items)} item(s).\n")

# Show a few key fields from each article.
for item in items:
    if item.get("result_type") != "news_article":
        # 'no_results' or 'error' rows carry a human-readable note instead.
        print("Note:", item.get("note") or item.get("error_message"))
        continue

    print(f"[{item.get('position')}] {item.get('title')}")
    print(f"    Search term: {item.get('searchTerm')}")
    print(f"    Source: {item.get('source')}  |  Date: {item.get('date')}")
    print(f"    Link: {item.get('link')}")
    snippet = item.get("snippet")
    if snippet:
        print(f"    Snippet: {snippet[:200]}")
    print()
