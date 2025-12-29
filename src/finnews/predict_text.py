import os
import torch
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# 1. Define the path relative to this script
# Going up to 'models' then into 'finbert_finetuned_v1'
base_path = Path(__file__).parent.parent.parent / "dev" / "models" / "finbert_finetuned_v1"

# 2. Convert to an absolute string and force forward slashes for Hugging Face
model_path = str(base_path.resolve()).replace("\\", "/")

print(f"Loading model from: {model_path}")

# 3. Load model and tokenizer
# local_files_only=True prevents it from trying to check the internet
tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
model = AutoModelForSequenceClassification.from_pretrained(model_path, local_files_only=True)


def predict_sentiment(text):
    """Predicts sentiment for a given text using the loaded model."""
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
    with torch.no_grad():
        logits = model(**inputs).logits
    predicted_class_id = torch.argmax(logits, dim=1).item()
    predicted_label = model.config.id2label[predicted_class_id]
    return predicted_label

if __name__ == "__main__":
    sample_text = """
    The company reported its quarterly earnings today, significantly exceeding analyst expectations.
    Revenue growth was strong across all major divisions, climbing 15% year-over-year to a record $2.5 billion.
    This impressive performance was driven by robust demand for its new product line and successful expansion into international markets.
    Citing these positive trends, the management team has upwardly revised its forecast for the full fiscal year and remains confident in its ability to deliver strong shareholder value.
    """
    predict_sentiment(sample_text)
