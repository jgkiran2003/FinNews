"""
predict_text.py — FinBERT sentiment inference with confidence scores.

Changes vs. v0:
  * Returns a structured result (label + confidence + full probability vector)
    instead of just the argmax label, so the dashboard can show how sure the
    model is and flag low-confidence calls.
  * Lazy-loads the model on first use and caches it. In the Streamlit
    dashboard we decorate with @st.cache_resource so the ~1s model load
    happens once per session, not once per article.
  * Robust path resolution that works whether the file is imported as a
    package module or run directly as a script.
  * Evaluates in eval()/no-grad mode and on the right device.
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Dict, Any, List

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification


# --- Model path resolution -------------------------------------------------
# src/finnews/predict_text.py -> ../../../dev/models/finbert_finetuned_v1
_BASE = Path(__file__).resolve().parent.parent.parent / "dev" / "models" / "finbert_finetuned_v1"
_MODEL_PATH = str(_BASE.resolve()).replace("\\", "/")

# Canonical labels in id order to match the fine-tuned model's config.
# config.json: id2label = {0: positive, 1: negative, 2: neutral}
LABELS: List[str] = ["positive", "negative", "neutral"]


# --- Lazy singleton loader -------------------------------------------------
_MODEL = None
_TOKENIZER = None
_LOCK = threading.Lock()


def load_model():
    """Load the model once (thread-safe) and return (tokenizer, model, device)."""
    global _MODEL, _TOKENIZER
    if _MODEL is None:
        with _LOCK:
            if _MODEL is None:
                print(f"[predict_text] Loading model from: {_MODEL_PATH}")
                device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
                tokenizer = AutoTokenizer.from_pretrained(_MODEL_PATH, local_files_only=True)
                model = AutoModelForSequenceClassification.from_pretrained(_MODEL_PATH, local_files_only=True)
                model.to(device)
                model.eval()
                _MODEL = model
                _TOKENIZER = tokenizer
                print(f"[predict_text] Model ready on {device}.")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return _TOKENIZER, _MODEL, device


# --- Public API ------------------------------------------------------------

def predict_sentiment(text: str) -> str:
    """Predict sentiment label for `text`. Returns just the label string.

    Kept for backward compatibility with app.py. For richer output use
    `predict_sentiment_detailed`.
    """
    result = predict_sentiment_detailed(text)
    return result["label"]


def predict_sentiment_detailed(text: str) -> Dict[str, Any]:
    """Predict sentiment with a full probability breakdown.

    Returns a dict: {"label", "confidence", "probs": {label -> prob}}.
    Raises ValueError on empty input so callers can handle blanks.
    """
    if not text or not str(text).strip():
        raise ValueError("Input text is empty; cannot predict sentiment.")

    tokenizer, model, device = load_model()

    inputs = tokenizer(str(text), return_tensors="pt", truncation=True, padding=True, max_length=512)
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        logits = model(**inputs).logits
        probs = torch.softmax(logits, dim=-1)[0]

    id2label = getattr(model.config, "id2label", {i: l for i, l in enumerate(LABELS)})
    probs_map = {id2label[i]: float(probs[i]) for i in range(len(probs))}

    pred_id = int(torch.argmax(probs).item())
    pred_label = id2label[pred_id]

    return {
        "label": pred_label,
        "confidence": float(probs[pred_id]),
        "probs": probs_map,
    }


def predict_batch(texts: List[str], batch_size: int = 32) -> List[Dict[str, Any]]:
    """Run inference over a list of texts efficiently in batches."""
    if not texts:
        return []

    tokenizer, model, device = load_model()
    results: List[Dict[str, Any]] = []
    id2label = getattr(model.config, "id2label", {i: l for i, l in enumerate(LABELS)})
    n_classes = len(id2label)

    for start in range(0, len(texts), batch_size):
        batch = texts[start:start + batch_size]
        inputs = tokenizer([str(t) for t in batch], return_tensors="pt", truncation=True, padding=True, max_length=512)
        inputs = {k: v.to(device) for k, v in inputs.items()}
        with torch.no_grad():
            logits = model(**inputs).logits
            probs = torch.softmax(logits, dim=-1)
        for i in range(len(batch)):
            pid = int(torch.argmax(probs[i]).item())
            results.append({
                "label": id2label[pid],
                "confidence": float(probs[i][pid]),
                "probs": {id2label[j]: float(probs[i][j]) for j in range(n_classes)},
            })

    return results


def get_cached_model():
    """Return (tokenizer, model, device) cached for a Streamlit session.

    Falls back to the plain singleton if streamlit is not available.
    """
    try:
        import streamlit as st  # type: ignore
    except ImportError:
        return load_model()

    @st.cache_resource(show_spinner="Loading FinBERT model…")
    def _cached():
        return load_model()

    return _cached()


# --- CLI smoke test --------------------------------------------------------
if __name__ == "__main__":
    sample = (
        "The company reported quarterly earnings today, significantly exceeding "
        "analyst expectations. Revenue grew 15% year-over-year to a record $2.5B."
    )
    out = predict_sentiment_detailed(sample)
    print(f"\nInput:   {sample}")
    print(f"Label:      {out['label']}")
    print(f"Confidence: {out['confidence']:.1%}")
    for lab, p in out["probs"].items():
        print(f"  {lab:<10}: {p:.1%}")
