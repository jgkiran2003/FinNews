import os, sqlite3, json
from datetime import datetime, timezone
from typing import Any, Dict, Optional, List

DB_PATH = "storage/finnews.db"
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"

def now_iso() -> str:
    """Return current UTC time as ISO8601 string with Z suffix."""
    return datetime.now(timezone.utc).replace(microsecond=0).strftime(ISO_FMT)

def get_conn() -> sqlite3.Connection:
    """Connect to the local SQLite database with WAL and foreign keys enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn

# ---------------------------------------------------------------------------
# Schema setup
# ---------------------------------------------------------------------------

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY,
    provider TEXT NOT NULL,
    external_id TEXT,
    url TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    published_at TEXT,
    source TEXT,
    language TEXT,
    tickers_json TEXT,
    raw_json TEXT NOT NULL,
    inserted_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_articles_published ON articles(published_at);
CREATE INDEX IF NOT EXISTS ix_articles_provider ON articles(provider);

CREATE TABLE IF NOT EXISTS sentiments (
    id INTEGER PRIMARY KEY,
    article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    engine TEXT NOT NULL,
    score REAL,
    label TEXT,
    inserted_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_sentiments_article ON sentiments(article_id);

CREATE TABLE IF NOT EXISTS price_moves (
    id INTEGER PRIMARY KEY,
    article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    symbol TEXT NOT NULL,
    t0_utc TEXT NOT NULL,
    t0_px REAL NOT NULL,
    tN_utc TEXT NOT NULL,
    tN_px REAL NOT NULL,
    delta_pct REAL NOT NULL,
    horizon_min INTEGER NOT NULL,
    inserted_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_moves_article ON price_moves(article_id);
CREATE INDEX IF NOT EXISTS ix_moves_symbol ON price_moves(symbol);
"""

def init_db() -> None:
    """Initialize tables and indices."""
    with get_conn() as conn:
        conn.executescript(SCHEMA_SQL)

# ---------------------------------------------------------------------------
# Simple upsert/save functions
# ---------------------------------------------------------------------------

def upsert_article(
    *,
    provider: str,
    external_id: Optional[str],
    url: str,
    title: str,
    published_at: Optional[str],
    source: Optional[str],
    language: Optional[str],
    tickers: Optional[List[str]],
    raw_obj: Dict[str, Any]
) -> int:
    tickers_json = json.dumps(tickers or [])
    raw_json = json.dumps(raw_obj, ensure_ascii=False)
    now = now_iso()

    with get_conn() as conn:
        row = conn.execute("SELECT id FROM articles WHERE url = ?", (url,)).fetchone()
        if row:
            conn.execute("""
                UPDATE articles SET
                    provider=?, external_id=?, title=?, published_at=?, source=?,
                    language=?, tickers_json=?, raw_json=?
                WHERE id=?
            """, (provider, external_id, title, published_at, source,
                  language, tickers_json, raw_json, row["id"]))
            return row["id"]

        cur = conn.execute("""
            INSERT INTO articles (
                provider, external_id, url, title, published_at, source,
                language, tickers_json, raw_json, inserted_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (provider, external_id, url, title, published_at, source,
              language, tickers_json, raw_json, now))
        return cur.lastrowid

def save_sentiment(article_id: int, engine: str, score: float, label: str) -> int:
    with get_conn() as conn:
        cur = conn.execute("""
            INSERT INTO sentiments(article_id, engine, score, label, inserted_at)
            VALUES (?, ?, ?, ?, ?)
        """, (article_id, engine, score, label, now_iso()))
        return cur.lastrowid

def save_price_move(
    article_id: int, symbol: str,
    t0_utc: str, t0_px: float,
    tN_utc: str, tN_px: float,
    delta_pct: float, horizon_min: int
) -> int:
    with get_conn() as conn:
        cur = conn.execute("""
            INSERT INTO price_moves(
                article_id, symbol, t0_utc, t0_px, tN_utc, tN_px,
                delta_pct, horizon_min, inserted_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (article_id, symbol, t0_utc, t0_px, tN_utc, tN_px,
              delta_pct, horizon_min, now_iso()))
        return cur.lastrowid
