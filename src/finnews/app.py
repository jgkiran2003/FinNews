"""
app.py — FinNews collection + sentiment pipeline.

For each new business headline pulled from NewsAPI, this script:
  1. Upserts the article into the local SQLite store.
  2. Runs the fine-tuned FinBERT to predict sentiment (label + confidence).
  3. Persists the sentiment so the dashboard can read it later.

Can be run standalone (`python app.py`) or imported by the dashboard:
    from app import collect_and_score
    summary = collect_and_score()
"""

import os
import sys
from typing import Dict, Any

from news_adapter import NewsAPIClientAdapter
import predict_text

# Prefer package import; fall back to relative when run as module
try:
    from storage import db as store
except Exception:
    from .storage import db as store  # type: ignore


def collect_and_score() -> Dict[str, Any]:
    """Fetch latest headlines, score them with FinBERT, store in SQLite.

    Returns a summary dict:
        {fetched, new, scored, errors, alerts, error}
    Safe to call from the dashboard — errors are caught and reported, not raised.
    """
    summary: Dict[str, Any] = {
        "fetched": 0, "new": 0, "scored": 0,
        "errors": 0, "alerts": [], "error": None,
    }

    try:
        store.init_db()
        adapter = NewsAPIClientAdapter()
        articles = adapter.top_headlines(
            categories=['business'], countries=['us'], normalize=True
        )
        summary["fetched"] = len(articles)

        for article in articles:
            url = article.get('url')
            if not url:
                continue
            title = article.get('title') or ''

            try:
                existing_id = store.get_article_id_by_url(url)

                article_id = store.upsert_article(
                    provider="newsapi",
                    external_id=None,
                    url=url,
                    title=title,
                    published_at=article.get('published_at'),
                    source=article.get('source'),
                    language=article.get('language'),
                    tickers=article.get('tickers'),
                    raw_obj=article.get('_raw', article),
                )

                is_new = existing_id is None
                if is_new:
                    summary["new"] += 1
                    print(f"  -> New article: {title}")

                # Score with FinBERT (label + confidence)
                result = predict_text.predict_sentiment_detailed(title)
                sentiment = result["label"]
                confidence = result["confidence"]

                if not store.has_sentiment(article_id):
                    store.save_sentiment(
                        article_id=article_id,
                        engine="predict_text",
                        score=confidence,
                        label=sentiment,
                    )
                    summary["scored"] += 1

                if sentiment in ('positive', 'negative'):
                    summary["alerts"].append(
                        f"{sentiment.upper()}: {title} ({confidence:.0%})"
                    )

            except Exception as e:
                summary["errors"] += 1
                print(f"  -> Error on '{title[:60]}': {e}")

    except Exception as e:
        summary["error"] = str(e)
        print(f"Error in collect_and_score: {e}")

    return summary


def main_loop():
    summary = collect_and_score()
    print()
    print(f"Fetched:  {summary['fetched']}")
    print(f"New:      {summary['new']}")
    print(f"Scored:   {summary['scored']}")
    if summary['errors']:
        print(f"Errors:   {summary['errors']}")
    if summary['error']:
        print(f"Fatal:    {summary['error']}")
    if summary['alerts']:
        print(f"\nAlerts ({len(summary['alerts'])}):")
        for a in summary['alerts']:
            print(f"  ! {a}")
    if summary['new'] == 0:
        print("No new articles found — all fetched headlines were already stored.")


if __name__ == "__main__":
    main_loop()
