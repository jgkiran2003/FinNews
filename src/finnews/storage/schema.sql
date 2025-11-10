CREATE TABLE IF NOT EXISTS articles(
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

CREATE TABLE IF NOT EXISTS sentiments(
  id INTEGER PRIMARY KEY,
  article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
  engine TEXT NOT NULL,
  score REAL,
  label TEXT,
  inserted_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_sentiments_article ON sentiments(article_id);

CREATE TABLE IF NOT EXISTS price_moves(
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
