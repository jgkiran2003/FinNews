import os, sqlite3, json
from datetime import datetime, timezone
from typing import Any, Dict, Optional, List

# Resolve paths
DB_PATH = "storage/finnews.db"
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")
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

def init_db() -> None:
    """Initialize tables and indices."""
    with get_conn() as conn:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            conn.executescript(f.read())

# ---------------------------------------------------------------------------
# Introspection helpers (for orchestration)
# ---------------------------------------------------------------------------

def get_article_id_by_url(url: str) -> Optional[int]:
    with get_conn() as conn:
        row = conn.execute("SELECT id FROM articles WHERE url = ?", (url,)).fetchone()
        return int(row["id"]) if row else None

def has_sentiment(article_id: int) -> bool:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM sentiments WHERE article_id = ? LIMIT 1",
            (article_id,),
        ).fetchone()
        return row is not None

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
