# src/finnews/test_db_storage.py
from pathlib import Path
from pprint import pprint

# Robust import for various run modes
try:
    # When 'src' is on PYTHONPATH
    from finnews.storage import db as store
except Exception:
    try:
        # When running from project root with package layout
        from storage import db as store  # type: ignore
    except Exception:
        # Fallback: add 'src' to sys.path dynamically
        import sys
        from pathlib import Path as _P
        sys.path.append(str(_P(__file__).resolve().parents[2]))  # .../src
        from finnews.storage import db as store  # type: ignore

def main():
    # Fresh start for the demo (delete DB file)
    db_file = Path("src/finnews/storage/finnews.db")
    if db_file.exists():
        db_file.unlink()

    # 1) Init schema
    store.init_db()

    # 2) Upsert an article
    url = "https://example.com/article-123"
    aid1 = store.upsert_article(
        provider="newsapi",
        external_id=None,
        url=url,
        title="Example Headline",
        published_at="2024-01-02T03:04:05Z",
        source="Example Source",
        language="en",
        tickers=["AAPL", "MSFT"],
        raw_obj={"foo": "bar"},
    )
    print("Inserted article_id:", aid1)

    # 3) Upsert same article (update fields)
    aid2 = store.upsert_article(
        provider="newsapi",
        external_id="ext-123",
        url=url,
        title="Example Headline Updated",
        published_at="2024-01-02T03:04:05Z",
        source="Example Source",
        language="en",
        tickers=["AAPL"],
        raw_obj={"foo": "baz", "version": 2},
    )
    print("Upsert returned same article_id:", aid2 == aid1)

    # 4) Lookup by URL
    aid_lookup = store.get_article_id_by_url(url)
    print("Lookup article_id matches:", aid_lookup == aid1)

    # 5) Save sentiment once and verify de-dup guard
    sid = store.save_sentiment(article_id=aid1, engine="unit-test", score=0.87, label="positive")
    print("Inserted sentiment_id:", sid)
    print("Has sentiment:", store.has_sentiment(aid1))

    # 6) Insert a price move
    pmid = store.save_price_move(
        article_id=aid1,
        symbol="AAPL",
        t0_utc="2024-01-02T10:00:00Z",
        t0_px=190.0,
        tN_utc="2024-01-02T10:30:00Z",
        tN_px=193.8,
        delta_pct=2.0,
        horizon_min=30,
    )
    print("Inserted price_move_id:", pmid)

    # 7) Dump a quick view using sqlite3 to confirm rows exist
    import sqlite3
    conn = sqlite3.connect("storage/finnews.db")
    conn.row_factory = sqlite3.Row

    print("\nArticles:")
    for r in conn.execute("SELECT id, url, title, provider, published_at FROM articles"):
        pprint(dict(r))

    print("\nSentiments:")
    for r in conn.execute("SELECT id, article_id, engine, score, label FROM sentiments"):
        pprint(dict(r))

    print("\nPrice Moves:")
    for r in conn.execute("SELECT id, article_id, symbol, delta_pct, horizon_min FROM price_moves"):
        pprint(dict(r))

    conn.close()

if __name__ == "__main__":
    main()
