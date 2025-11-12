"""
Clean News API tester script based on the test notebook.

Runs lightweight fetches against NewsAPI.org and MarketAux (if API keys are present)
and prints concise summaries. Designed for quick manual verification, not unit tests.

Env vars:
  - NEWSAPI_API_KEY
  - MARKETAUX_API_KEY

Run:
  python src/finnews/test/test_news_api.py
"""
from __future__ import annotations

import os
from dotenv import load_dotenv
load_dotenv()
from typing import Any, Dict, List, Optional


# Robust imports to support different run modes
def _import_clients():
    try:
        # When running as a package from project root with src on PYTHONPATH
        from finnews.news_apis.clients.newsapi_client import NewsAPIClientAdapter
        from finnews.news_apis.clients.marketaux_client import MarketAuxClient
        return NewsAPIClientAdapter, MarketAuxClient
    except Exception:
        try:
            # Direct relative-like import if running within src/finnews
            from news_apis.clients.newsapi_client import NewsAPIClientAdapter  # type: ignore
            from news_apis.clients.marketaux_client import MarketAuxClient  # type: ignore
            return NewsAPIClientAdapter, MarketAuxClient
        except Exception:
            # Final fallback: modify sys.path to include src
            import sys
            from pathlib import Path
            sys.path.append(str(Path(__file__).resolve().parents[2]))  # add .../src
            from finnews.news_apis.clients.newsapi_client import NewsAPIClientAdapter  # type: ignore
            from finnews.news_apis.clients.marketaux_client import MarketAuxClient  # type: ignore
            return NewsAPIClientAdapter, MarketAuxClient


NewsAPIClientAdapter, MarketAuxClient = _import_clients()


def _fmt_row(a: Dict[str, Any]) -> str:
    title = a.get("title") or a.get("headline") or "(no title)"
    src = (
        (a.get("source") or {}).get("name")
        if isinstance(a.get("source"), dict)
        else a.get("source")
    )
    src = src or a.get("source_domain") or "?"
    pub = a.get("publishedAt") or a.get("published_at") or "?"
    url = a.get("url") or "?"
    return f"- {title} | {src} | {pub} | {url}"


def run_newsapi_demo() -> None:
    key = os.getenv("NEWSAPI_API_KEY")
    if not key:
        print("[NewsAPI] Skipped (NEWSAPI_API_KEY not set)")
        return

    client = NewsAPIClientAdapter(api_key=key)
    print("[NewsAPI] top_headlines: business/technology in us,gb (normalized)")
    articles = client.top_headlines(
        categories=["business", "technology"],
        countries=["us", "gb"],
        page_size=50,
        normalize=True,
    )
    print(f"[NewsAPI] got {len(articles)} articles")
    for a in articles[:5]:
        print(_fmt_row(a if isinstance(a, dict) else {}))

    print("\n[NewsAPI] search_everything: query='stocks' (normalized)")
    search = client.search_everything(
        q="stocks",
        language="en",
        page_size=25,
        sort_by="publishedAt",
        normalize=True,
    )
    print(f"[NewsAPI] got {len(search)} articles")
    for a in search[:5]:
        print(_fmt_row(a if isinstance(a, dict) else {}))


def run_marketaux_demo() -> None:
    key = os.getenv("MARKETAUX_API_KEY")
    if not key:
        print("[MarketAux] Skipped (MARKETAUX_API_KEY not set)")
        return

    client = MarketAuxClient(api_key=key)
    print("[MarketAux] finance_market_news: symbols=AAPL,TSLA limit=10")
    data = client.finance_market_news(symbols="AAPL,TSLA", limit=10, page=1)
    # MarketAux returns an object with 'data' list
    rows: List[Dict[str, Any]] = data.get("data", []) if isinstance(data, dict) else []
    print(f"[MarketAux] got {len(rows)} articles")
    for a in rows[:5]:
        print(_fmt_row(a))

    print("\n[MarketAux] finance_market_news: search='earnings' limit=10")
    data2 = client.finance_market_news(search="earnings", limit=10, page=1)
    rows2: List[Dict[str, Any]] = data2.get("data", []) if isinstance(data2, dict) else []
    print(f"[MarketAux] got {len(rows2)} articles")
    for a in rows2[:5]:
        print(_fmt_row(a))


def main() -> None:
    print("=== News API Tester ===")
    run_newsapi_demo()
    print("")
    run_marketaux_demo()


if __name__ == "__main__":
    main()

