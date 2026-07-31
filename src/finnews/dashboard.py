"""
dashboard.py — FinNews Market Sentiment Dashboard (redesigned)

A dark, terminal-styled financial news sentiment dashboard.

Design notes:
  * Visual identity: a "market terminal" aesthetic — deep slate surfaces,
    semantic bull/bear/neutral colors, IBM Plex typography. Grounded in the
    look of the trading floor rather than the default light Streamlit skin.
  * Signature element: the "Market Mood" band — a net sentiment score rendered
    as one large evocative number with a diverging bar. This is the thesis.
  * Article feed: each headline is a card with a sentiment badge and a
    confidence meter, so you see not just the call but how sure the model is.
  * Charts: Plotly (interactive) for the mood donut, sentiment trend over
    time, and per-source breakdown — replacing the static matplotlib pie.
  * Filters: sentiment, source, date window, minimum confidence.
  * Confidence: reads the stored `score` column. Articles scored before the
    upgrade have NULL confidence and show a muted marker.
  * Robust: works with an empty or missing database with inviting empty states.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime
from typing import Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ───────────────────────── Page config ─────────────────────────
st.set_page_config(
    page_title="FinNews · Market Sentiment",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ───────────────────────── Theme ─────────────────────────
# Semantic + surface palette. Bull/bear/neutral carry meaning; accent is the
# one non-semantic highlight color used sparingly. Local variables below keep
# the CSS string free of f-string-quote nesting problems.
BG       = "#0B1117"
SURFACE  = "#141C26"
SURFACE2 = "#1B2530"
BORDER   = "#273140"
TEXT     = "#E6EDF3"
MUTED    = "#8B98A9"
POS      = "#26D07C"
NEG      = "#FF5C5C"
NEU      = "#E8B339"
ACCENT   = "#4CC2FF"

SENTIMENT_COLOR = {
    "positive": POS,
    "negative": NEG,
    "neutral":  NEU,
}

# Inject the visual identity as CSS. We use .format-style replacement via
# .replace() to stay quote-safe given how dense the CSS is.
_CSS_TEMPLATE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

html, body, [class*="css"] {
  font-family: 'IBM Plex Sans', sans-serif;
  color: __TEXT__;
}
.stApp { background: __BG__; }
.stApp > header { background: rgba(11,17,23,0.85); backdrop-filter: blur(8px); }
.stApp > header a { color: __TEXT__; }

.card {
  background: __SURFACE__;
  border: 1px solid __BORDER__;
  border-radius: 10px;
  padding: 1rem 1.1rem;
}
.kpi {
  background: __SURFACE__;
  border: 1px solid __BORDER__;
  border-radius: 10px;
  padding: 0.9rem 1rem;
}
.kpi .label { font-size: 0.72rem; letter-spacing: 0.08em; text-transform: uppercase; color: __MUTED__; }
.kpi .value { font-family: 'IBM Plex Mono', monospace; font-size: 1.7rem; font-weight: 600; margin-top: 0.15rem; line-height: 1.1; }

.badge {
  display: inline-block; font-size: 0.68rem; font-weight: 600;
  letter-spacing: 0.05em; text-transform: uppercase;
  padding: 0.16rem 0.5rem; border-radius: 999px;
}
.b-pos { background: __POS__22; color: __POS__; border: 1px solid __POS__55; }
.b-neg { background: __NEG__22; color: __NEG__; border: 1px solid __NEG__55; }
.b-neu { background: __NEU__22;  color: __NEU__;  border: 1px solid __NEU__55; }

.meter { height: 4px; background: __SURFACE2__; border-radius: 2px; overflow: hidden; margin-top: 0.4rem; }
.meter > span { display: block; height: 100%; border-radius: 2px; }

.article { border-top: 1px solid __BORDER__; padding: 0.65rem 0; }
.article:first-child { border-top: 0; padding-top: 0; }
.article .title { color: __TEXT__; font-weight: 500; font-size: 0.92rem; line-height: 1.35; }
.article .title:hover { color: __ACCENT__; }
.article .meta { color: __MUTED__; font-size: 0.72rem; margin-top: 0.2rem; font-family: 'IBM Plex Mono', monospace; }

.mood-num { font-family: 'IBM Plex Mono', monospace; font-size: 3rem; font-weight: 700; line-height: 1; }
.mood-bar {
  position: relative; height: 8px; border-radius: 4px; margin-top: 0.7rem;
  background: linear-gradient(90deg, __NEG__ 0%, __NEG__ 45%, __NEU__ 50%, __NEU__ 55%, __POS__ 100%);
}
.mood-marker {
  position: absolute; top: -4px; width: 4px; height: 16px; border-radius: 2px;
  background: __TEXT__; box-shadow: 0 0 0 2px __BG__;
}

h1, h2, h3 { color: __TEXT__; }
.eyebrow { font-size: 0.72rem; letter-spacing: 0.12em; text-transform: uppercase; color: __MUTED__; }

section[data-testid="stSidebar"] { background: __SURFACE__; border-right: 1px solid __BORDER__; }

.stDataFrame { background: __SURFACE__; border-radius: 10px; border: 1px solid __BORDER__; }

[data-testid="stMetric"] {
  background: __SURFACE__; border: 1px solid __BORDER__;
  border-radius: 10px; padding: 0.8rem 1rem;
}
[data-testid="stMetricLabel"] { color: __MUTED__; font-size: 0.72rem; letter-spacing: 0.06em; text-transform: uppercase; }
[data-testid="stMetricValue"] { font-family: 'IBM Plex Mono', monospace; color: __TEXT__; }

.block-container { padding-top: 2rem; max-width: 1400px; }

/* Push content below Streamlit's top header bar (hamburger/deploy) */
header[data-testid="stHeader"] {
  background: transparent;
  z-index: 999;
}
/* Hide the deploy/main-menu items that clutter the top bar */
header[data-testid="stHeader"] [data-testid="stToolbar"] { display: none; }
/* Give the main content room so the header doesn't overlap the title */
.stApp > header { height: 0px; min-height: 0px; }
.block-container { padding-top: 3.5rem; }
</style>
"""

_css = (_CSS_TEMPLATE
    .replace("__BG__", BG)
    .replace("__SURFACE2__", SURFACE2)
    .replace("__SURFACE__", SURFACE)
    .replace("__BORDER__", BORDER)
    .replace("__TEXT__", TEXT)
    .replace("__MUTED__", MUTED)
    .replace("__POS__", POS)
    .replace("__NEG__", NEG)
    .replace("__NEU__", NEU)
    .replace("__ACCENT__", ACCENT)
)
st.markdown(_css, unsafe_allow_html=True)


# ───────────────────────── Database ─────────────────────────
DB_FILENAME = "finnews.db"


def get_db_path() -> Optional[str]:
    """Locate finnews.db relative to this script (same dir, then storage/)."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    local = os.path.join(current_dir, DB_FILENAME)
    if os.path.exists(local):
        return local
    storage = os.path.join(current_dir, "storage", DB_FILENAME)
    return storage if os.path.exists(storage) else None


@st.cache_data(ttl=60)
def load_data(database_path: str) -> pd.DataFrame:
    """Fetch articles + stored sentiment (with confidence score) from SQLite."""
    if not database_path or not os.path.exists(database_path):
        return pd.DataFrame()

    try:
        import sqlite3
        conn = sqlite3.connect(database_path)
        query = """
            SELECT a.title, a.source, a.published_at,
                   s.label AS sentiment, s.score AS confidence, a.url
            FROM articles a
            LEFT JOIN sentiments s ON a.id = s.article_id
            ORDER BY a.published_at DESC
            LIMIT 500
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
    except Exception as e:
        st.error("Could not read database: " + str(e))
        return pd.DataFrame()

    if df.empty:
        return df

    df["published_at"] = pd.to_datetime(df["published_at"], errors="coerce", utc=True)
    df = df.dropna(subset=["published_at"]).copy()
    df["date"] = df["published_at"].dt.date
    df["sentiment"] = df["sentiment"].fillna("neutral").str.lower()
    return df


# ───────────────────────── Helpers ─────────────────────────
def mood_word(net: float) -> str:
    if net >= 0.25:
        return "Lean Bullish"
    if net <= -0.25:
        return "Lean Bearish"
    return "Balanced"


def mood_color(net: float) -> str:
    if net > 0.02:
        return POS
    if net < -0.02:
        return NEG
    return NEU


def sentiment_badge_html(label: str, confidence) -> str:
    cls = {"positive": "b-pos", "negative": "b-neg", "neutral": "b-neu"}.get(label, "b-neu")
    has_c = confidence is not None and confidence == confidence  # NaN check
    pct = "{:.0%}".format(confidence) if has_c else "—"
    bar_color = SENTIMENT_COLOR.get(label, MUTED)
    bar_w = int(confidence * 100) if has_c else 0
    return (
        '<span class="badge ' + cls + '">' + label + '</span>'
        + '<div style="display:flex;align-items:center;gap:0.5rem;margin-top:0.35rem;">'
        + '<span style="font-size:0.7rem;color:' + MUTED + ';font-family:\'IBM Plex Mono\',monospace;">conf ' + pct + '</span>'
        + '</div>'
        + '<div class="meter"><span style="width:' + str(bar_w) + '%;background:' + bar_color + ';"></span></div>'
    )


def article_row_html(title: str, source: str, when: str, sentiment: str, confidence, url: str) -> str:
    badge = sentiment_badge_html(sentiment, confidence)
    source = source or "Unknown"
    if url:
        link = '<a class="title" href="' + url + '" target="_blank" style="text-decoration:none;">' + title + '</a>'
    else:
        link = '<span class="title">' + title + '</span>'
    return (
        '<div class="article">'
        + '<div style="display:flex;justify-content:space-between;align-items:flex-start;gap:0.8rem;">'
        + '<div style="flex:1;min-width:0;">' + link
        + '<div class="meta">' + source + ' · ' + when + '</div>'
        + '</div>'
        + '<div style="min-width:96px;text-align:right;">' + badge + '</div>'
        + '</div></div>'
    )


# ───────────────────────── Load data ─────────────────────────
db_path = get_db_path()

if not db_path:
    st.markdown(
        '<div class="card" style="text-align:center;padding:3rem 1rem;margin-top:2rem;">'
        + '<div style="font-size:2rem;">📡</div>'
        + '<h3 style="margin:0.5rem 0 0.3rem;">No data yet</h3>'
        + '<p style="color:' + MUTED + ';margin:0 auto;max-width:28rem;">'
        + 'Run the collector to start pulling headlines. Once articles are stored, '
        + "they'll appear here with sentiment and confidence scores."
        + '</p>'
        + '<p style="color:' + MUTED + ";font-family:'IBM Plex Mono',monospace;font-size:0.78rem;margin-top:1rem;\">"
        + 'python src/finnews/app.py</p>'
        + '</div>',
        unsafe_allow_html=True,
    )
    st.stop()

df = load_data(db_path)

if df.empty:
    st.markdown(
        '<div class="card" style="text-align:center;padding:3rem 1rem;margin-top:2rem;">'
        + '<div style="font-size:2rem;">🗞️</div>'
        + '<h3 style="margin:0.5rem 0 0.3rem;">The feed is empty</h3>'
        + '<p style="color:' + MUTED + ';margin:0 auto;max-width:28rem;">'
        + "Articles will show up here once the collector has run. Pull the latest "
        + 'business headlines to populate the dashboard.'
        + '</p>'
        + '</div>',
        unsafe_allow_html=True,
    )
    st.stop()


# ───────────────────────── Sidebar filters ─────────────────────────
with st.sidebar:
    st.markdown('<div class="eyebrow">Filters</div>', unsafe_allow_html=True)
    st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)

    sent_opts = ["positive", "negative", "neutral"]
    chosen_sent = st.multiselect("Sentiment", sent_opts, default=sent_opts)

    all_sources = sorted(df["source"].dropna().unique().tolist())
    chosen_sources = st.multiselect("Sources", all_sources, default=all_sources)

    dates = df["published_at"].dt.tz_convert(None).dt.date
    dmin, dmax = dates.min(), dates.max()
    date_range = st.date_input(
        "Date range",
        value=(dmin, dmax),
        min_value=dmin,
        max_value=dmax,
    )
    if isinstance(date_range, tuple) and len(date_range) == 2:
        lo, hi = date_range
    else:
        lo, hi = dmin, dmax

    has_conf = df["confidence"].notna().any()
    min_conf = 0.0
    if has_conf:
        min_conf = st.slider("Min confidence", 0.0, 1.0, 0.0, 0.05)

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    # Fetch latest headlines + score them with FinBERT in one click
    if st.button("⬇ Fetch latest headlines", use_container_width=True, type="primary"):
        try:
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from app import collect_and_score  # type: ignore
            with st.spinner("Fetching headlines and scoring with FinBERT…"):
                result = collect_and_score()
            if result.get("error"):
                st.error(f"Fetch failed: {result['error']}")
            else:
                msg_parts = [f"{result['new']} new", f"{result['scored']} scored"]
                if result["errors"]:
                    msg_parts.append(f"{result['errors']} errors")
                st.success(" · ".join(msg_parts) + f" of {result['fetched']} fetched.")
                if result["alerts"]:
                    with st.expander(f"🔔 {len(result['alerts'])} sentiment alert(s)"):
                        for a in result["alerts"]:
                            st.write(a)
                st.cache_data.clear()
                st.rerun()
        except Exception as e:
            st.error(f"Could not fetch headlines: {e}")

    if st.button("↻ Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# Apply filters
view = df.copy()
if chosen_sent:
    view = view[view["sentiment"].isin(chosen_sent)]
if chosen_sources:
    view = view[view["source"].isin(chosen_sources)]
view_dates = view["published_at"].dt.tz_convert(None).dt.date
view = view[(view_dates >= lo) & (view_dates <= hi)]
if has_conf:
    view = view[(view["confidence"].isna()) | (view["confidence"] >= min_conf)]

view = view.sort_values("published_at", ascending=False)


# ───────────────────────── Header ─────────────────────────
st.markdown(
    '<div style="display:flex;align-items:baseline;justify-content:space-between;flex-wrap:wrap;gap:0.5rem;">'
    + '<div><div class="eyebrow">FinNews</div>'
    + '<h1 style="margin:0;font-size:1.6rem;">Market Sentiment Terminal</h1></div>'
    + '<div style="color:' + MUTED + ";font-family:'IBM Plex Mono',monospace;font-size:0.78rem;\">"
    + str(len(view)) + ' articles · updated ' + datetime.now().strftime('%H:%M') + '</div>'
    + '</div>',
    unsafe_allow_html=True,
)
st.markdown("---")


# ───────────────────────── Mood band (signature hero) ─────────────────────────
total = len(view)
counts = view["sentiment"].value_counts()
pos = int(counts.get("positive", 0))
neg = int(counts.get("negative", 0))
neu = int(counts.get("neutral", 0))
net = (pos - neg) / total if total else 0.0
net_pct = net * 100

word = mood_word(net)
mc = mood_color(net)
marker_left = (net + 1) / 2 * 100

st.markdown(
    '<div class="card" style="margin-bottom:1.2rem;">'
    + '<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:1rem;">'
    + '<div><div class="eyebrow">Market Mood</div>'
    + '<div class="mood-num" style="color:' + mc + ';">' + ("{:+.0f}".format(net_pct)) + '</div>'
    + '<div style="color:' + MUTED + ';font-size:0.8rem;margin-top:0.2rem;">net sentiment index &nbsp;·&nbsp; '
    + '<span style="color:' + mc + ';font-weight:600;">' + word + '</span></div></div>'
    + '<div style="text-align:right;"><div class="eyebrow">Breakdown</div>'
    + "<div style=\"font-family:'IBM Plex Mono',monospace;font-size:0.85rem;margin-top:0.3rem;line-height:1.6;\">"
    + '<span style="color:' + POS + ';">▲ ' + str(pos) + '</span>&nbsp;&nbsp;'
    + '<span style="color:' + NEU + ';">● ' + str(neu) + '</span>&nbsp;&nbsp;'
    + '<span style="color:' + NEG + ';">▼ ' + str(neg) + '</span></div>'
    + '<div style="color:' + MUTED + ';font-size:0.72rem;margin-top:0.2rem;">of ' + str(total) + ' articles</div></div>'
    + '</div>'
    + '<div class="mood-bar"><span class="mood-marker" style="left:' + "{:.1f}".format(marker_left) + '%;"></span></div>'
    + '</div>',
    unsafe_allow_html=True,
)


# ───────────────────────── KPI row ─────────────────────────
def avg_confidence(d: pd.DataFrame) -> Optional[float]:
    s = d["confidence"].dropna()
    return float(s.mean()) if len(s) else None

avg_c = avg_confidence(view)
k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    st.metric("Total Articles", total)
with k2:
    st.metric("Bullish", "{:.0%}".format(pos / total) if total else "—")
with k3:
    st.metric("Bearish", "{:.0%}".format(neg / total) if total else "—")
with k4:
    st.metric("Neutral", "{:.0%}".format(neu / total) if total else "—")
with k5:
    st.metric("Avg Confidence", "{:.0%}".format(avg_c) if avg_c is not None else "—")

st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)


# ───────────────────────── Main grid ─────────────────────────
col_feed, col_charts = st.columns([3, 2], gap="medium")

# ---- Article feed ----
with col_feed:
    st.markdown('<div class="eyebrow" style="margin-bottom:0.6rem;">Latest Headlines</div>', unsafe_allow_html=True)
    feed_html = '<div class="card" style="max-height:720px;overflow-y:auto;">'
    show = view.head(60)
    for _, row in show.iterrows():
        ts = row["published_at"]
        when = ts.strftime("%b %d, %H:%M") if pd.notna(ts) else ""
        feed_html += article_row_html(
            str(row["title"]), str(row["source"]), when,
            row["sentiment"], row["confidence"], str(row.get("url") or ""),
        )
    if len(show) == 0:
        feed_html += '<div style="color:' + MUTED + ';padding:1rem 0;">No articles match the current filters.</div>'
    feed_html += "</div>"
    st.markdown(feed_html, unsafe_allow_html=True)


# ---- Charts column ----
with col_charts:
    # Mood donut
    st.markdown('<div class="eyebrow" style="margin-bottom:0.6rem;">Sentiment Mix</div>', unsafe_allow_html=True)
    donut_df = (
        view["sentiment"].value_counts().reindex(["positive", "negative", "neutral"]).fillna(0).reset_index()
    )
    donut_df.columns = ["sentiment", "count"]
    donut = go.Figure(go.Pie(
        labels=donut_df["sentiment"],
        values=donut_df["count"],
        hole=0.62,
        marker=dict(colors=[SENTIMENT_COLOR[s] for s in donut_df["sentiment"]]),
        textinfo="percent",
        textfont=dict(color=TEXT, size=12),
        showlegend=True,
    ))
    donut.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=MUTED, family="IBM Plex Sans"),
        margin=dict(l=0, r=0, t=0, b=40),
        height=280,
        legend=dict(orientation="h", yanchor="bottom", y=0.02, xanchor="center", x=0.5, font=dict(size=11)),
    )
    st.plotly_chart(donut, use_container_width=True, config=dict(displayModeBar=False))

    st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)

    # Sentiment trend over time (stacked area)
    st.markdown('<div class="eyebrow" style="margin-bottom:0.6rem;">Sentiment Trend</div>', unsafe_allow_html=True)
    trend = (
        view.assign(date=view["published_at"].dt.date)
        .groupby(["date", "sentiment"]).size().unstack(fill_value=0)
    )
    for s in ["positive", "negative", "neutral"]:
        if s not in trend.columns:
            trend[s] = 0
    trend = trend.sort_index()

    trend_fig = go.Figure()
    for s, col in [("positive", POS), ("negative", NEG), ("neutral", NEU)]:
        trend_fig.add_trace(go.Scatter(
            x=trend.index, y=trend[s], name=s.capitalize(),
            mode="lines", line=dict(color=col, width=1.5, shape="spline"),
            stackgroup="one",
        ))
    trend_fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=MUTED, family="IBM Plex Sans", size=10),
        margin=dict(l=0, r=0, t=0, b=40),
        height=250,
        legend=dict(orientation="h", yanchor="bottom", y=0.02, xanchor="center", x=0.5, font=dict(size=10)),
        xaxis=dict(gridcolor=BORDER, zeroline=False),
        yaxis=dict(gridcolor=BORDER, zeroline=False),
    )
    st.plotly_chart(trend_fig, use_container_width=True, config=dict(displayModeBar=False))

    st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)

    # Per-source breakdown (stacked horizontal bars)
    st.markdown('<div class="eyebrow" style="margin-bottom:0.6rem;">By Source</div>', unsafe_allow_html=True)
    src = (
        view.groupby(["source", "sentiment"]).size().unstack(fill_value=0)
    )
    top_sources = src.sum(axis=1).sort_values(ascending=False).head(8).index
    src = src.loc[top_sources]
    src_fig = go.Figure()
    for s, col in [("positive", POS), ("negative", NEG), ("neutral", NEU)]:
        if s in src.columns:
            src_fig.add_trace(go.Bar(
                y=src.index, x=src[s], name=s.capitalize(),
                orientation="h", marker_color=col,
            ))
    src_fig.update_layout(
        barmode="stack",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=MUTED, family="IBM Plex Sans", size=10),
        margin=dict(l=0, r=0, t=0, b=40),
        height=290,
        legend=dict(orientation="h", yanchor="bottom", y=0.02, xanchor="center", x=0.5, font=dict(size=10)),
        xaxis=dict(gridcolor=BORDER, zeroline=False),
        yaxis=dict(gridcolor=BORDER, zeroline=False, autorange="reversed"),
    )
    st.plotly_chart(src_fig, use_container_width=True, config=dict(displayModeBar=False))


# ───────────────────────── Live headline tester ─────────────────────────
st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)
with st.expander("🧪 Score a headline live"):
    st.caption(
        "Runs the fine-tuned FinBERT on any headline you paste. "
        "The model loads once per session and is reused across the dashboard."
    )
    user_text = st.text_input(
        "Headline",
        placeholder="e.g. Apple beats Q3 expectations, raises dividend",
        label_visibility="collapsed",
    )
    if user_text and user_text.strip():
        try:
            import sys
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            import predict_text  # type: ignore
            res = predict_text.predict_sentiment_detailed(user_text.strip())
            pred_c = SENTIMENT_COLOR.get(res["label"], MUTED)
            col_a, col_b = st.columns([2, 3])
            with col_a:
                st.markdown(
                    '<div class="card" style="text-align:center;">'
                    + '<div class="eyebrow">Prediction</div>'
                    + '<div style="font-size:1.6rem;font-weight:700;color:' + pred_c + ';text-transform:capitalize;margin-top:0.3rem;">' + res["label"] + '</div>'
                    + '<div style="color:' + MUTED + ";font-family:'IBM Plex Mono',monospace;font-size:0.85rem;margin-top:0.2rem;\">"
                    + "confidence {:.1%}".format(res["confidence"]) + '</div>'
                    + '</div>',
                    unsafe_allow_html=True,
                )
            with col_b:
                probs = res["probs"]
                bar_html = ""
                for lab in ["positive", "negative", "neutral"]:
                    p = probs.get(lab, 0.0)
                    bar_html += (
                        '<div style="margin-bottom:0.6rem;">'
                        + '<div style="display:flex;justify-content:space-between;font-size:0.78rem;">'
                        + '<span style="color:' + SENTIMENT_COLOR[lab] + ';text-transform:capitalize;">' + lab + '</span>'
                        + '<span style="color:' + MUTED + ";font-family:'IBM Plex Mono',monospace;\">" + "{:.1%}".format(p) + '</span>'
                        + '</div>'
                        + '<div class="meter"><span style="width:' + "{:.1f}".format(p * 100) + '%;background:' + SENTIMENT_COLOR[lab] + ';"></span></div>'
                        + '</div>'
                    )
                st.markdown('<div class="card">' + bar_html + '</div>', unsafe_allow_html=True)
        except Exception as e:
            st.error("Could not run the model: " + str(e))
