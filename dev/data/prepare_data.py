"""
prepare_data.py — augment the Financial PhraseBank with public datasets.

This script is meant to be run ONCE, locally, on a machine with internet
access and the HuggingFace `datasets` library installed:

    pip install "datasets>=2.19.0" pandas

    cd dev/data
    python prepare_data.py

It fetches additional public financial-sentiment datasets, normalizes their
labels to {positive, negative, neutral}, de-duplicates on text, reports the
class balance before/after, and writes:

    dev/data/sentiment_data_augmented.csv

The training notebook will automatically use the augmented CSV when present,
falling back to the original `sentiment_data.csv` otherwise.

Rationale for the sources:
  1. Financial PhraseBank (your existing data) — formal company statements.
  2. zeroshot/twitter-financial-news-sentiment — informal financial tweets,
     a different register that broadens coverage and helps balance classes.

Each remote source is wrapped in try/except so a single failure (rename, auth,
deprecation) does not abort the whole merge. Inspect the printed summary and
drop/keep sources as you see fit.
"""

from __future__ import annotations

import csv
from pathlib import Path
from collections import Counter

import pandas as pd

HERE = Path(__file__).resolve().parent
BASE_CSV = HERE / "sentiment_data.csv"
OUT_CSV = HERE / "sentiment_data_augmented.csv"

# Canonical label set
LABELS = {"positive", "negative", "neutral"}

# Map various source labels onto the canonical set.
LABEL_MAP = {
    # canonical
    "positive": "positive",
    "negative": "negative",
    "neutral": "neutral",
    # Financial PhraseBank variants
    "Positive": "positive",
    "Negative": "negative",
    "Neutral": "neutral",
    # zeroshot/twitter-financial-news-sentiment
    "Bullish": "positive",
    "Bearish": "negative",
    "Neutral.0": "neutral",
}


def norm_label(x: object) -> str | None:
    if x is None:
        return None
    s = str(x).strip()
    if s in LABEL_MAP:
        return LABEL_MAP[s]
    s_low = s.lower()
    if s_low in LABELS:
        return s_low
    return None


def norm_text(x: object) -> str:
    if x is None:
        return ""
    s = str(x).strip().replace("\r", " ").replace("\n", " ")
    while "  " in s:
        s = s.replace("  ", " ")
    return s


def load_base() -> pd.DataFrame:
    """Load the existing Financial PhraseBank CSV as the foundation."""
    encodings = ["utf-8", "latin-1", "cp1252"]
    last_err: Exception | None = None
    for enc in encodings:
        try:
            df = pd.read_csv(BASE_CSV, encoding=enc)
        except UnicodeDecodeError as e:  # try next encoding
            last_err = e
            continue
        except FileNotFoundError:
            print(f"  [skip] base CSV not found at {BASE_CSV}")
            return pd.DataFrame(columns=["text", "label", "source"])
        # Heuristically locate the text and label columns.
        text_col = "Sentence" if "Sentence" in df.columns else df.columns[0]
        label_col = "Sentiment" if "Sentiment" in df.columns else df.columns[-1]
        out = pd.DataFrame(
            {
                "text": df[text_col].map(norm_text),
                "label": df[label_col].map(norm_label),
                "source": "financial_phrasebank",
            }
        )
        out = out[out["text"].str.len() > 0]
        print(f"  [ok] base: {len(out)} rows from {BASE_CSV.name}")
        return out
    raise last_err  # type: ignore[misc]


def load_zeroshot_twitter() -> pd.DataFrame:
    """zeroshot/twitter-financial-news-sentiment (FinanceInc tweet set).

    Label schema: 0=Bearish(negative), 1=Bullish(positive), 2=Neutral.
    The HF repo has occasionally used integer codes OR string codes across
    revisions; this helper handles both.
    """
    from datasets import load_dataset  # local import; only needed when fetching

    ds = load_dataset("zeroshot/twitter-financial-news-sentiment")
    rows = []
    for split in ds.keys():  # 'train', 'test', 'validation' if present
        for ex in ds[split]:
            text = norm_text(ex.get("text") or ex.get("sentence") or ex.get("tweet"))
            raw = ex.get("label") if ex.get("label") is not None else ex.get("sentiment")
            # Integer code mapping (per the dataset card):
            INT_MAP = {0: "negative", 1: "positive", 2: "neutral"}
            if isinstance(raw, int):
                lab = INT_MAP.get(raw)
            else:
                lab = norm_label(raw)
            if text and lab:
                rows.append({"text": text, "label": lab, "source": "zeroshot_twitter"})
    df = pd.DataFrame(rows)
    print(f"  [ok] zeroshot/twitter-financial-news-sentiment: {len(df)} rows")
    return df


def dedupe(rows: pd.DataFrame) -> pd.DataFrame:
    """Drop exact + near-exact duplicate text, keeping first occurrence."""
    rows = rows.copy()
    rows["__key"] = rows["text"].str.lower().str.strip()
    rows = rows.drop_duplicates(subset="__key", keep="first")
    return rows.drop(columns="__key")


def report(df: pd.DataFrame, title: str) -> None:
    counts = Counter(df["label"])
    total = sum(counts.values()) or 1
    print(f"\n{title}")
    print(f"  total: {total}")
    for lab in ("positive", "negative", "neutral"):
        c = counts.get(lab, 0)
        print(f"  {lab:<8}: {c:>5}  ({c/total:5.1%})")
    # per-source
    by_src = df.groupby("source")["label"].value_counts().unstack(fill_value=0)
    print("  per-source:")
    print(by_src.to_string().replace("\n", "\n    "))


def main() -> None:
    print("# Fetching and merging financial-sentiment datasets")
    frames: list[pd.DataFrame] = []

    base = load_base()
    if not base.empty:
        frames.append(base)

    # --- Add remote sources (each independently best-effort) ---
    remote_loaders = [
        ("zeroshot/twitter-financial-news-sentiment", load_zeroshot_twitter),
    ]
    for name, loader in remote_loaders:
        try:
            print(f"\n# Source: {name}")
            df = loader()
            if not df.empty:
                frames.append(df)
        except Exception as e:  # noqa: BLE001 - keep going if one source fails
            print(f"  [warn] could not load {name}: {type(e).__name__}: {e}")
            print("         continuing without it.")

    if not frames:
        raise SystemExit("No datasets loaded; nothing to write.")

    combined = pd.concat(frames, ignore_index=True)
    combined = combined[combined["label"].isin(LABELS)]
    combined = dedupe(combined)

    report(base, "## Before augmentation (base)")
    report(combined, "## After augmentation (combined)")

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(OUT_CSV, index=False, quoting=csv.QUOTE_MINIMAL)
    print(f"\nWrote {len(combined)} rows -> {OUT_CSV}")
    print("The training notebook will prefer this file when it exists.")


if __name__ == "__main__":
    main()
