import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# Convert to an absolute string and force forward slashes for Hugging Face
model_path = "./final_model/model"

print(f"Loading model from: {model_path}")

# Load model and tokenizer
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
    # print(f"Predicted sentiment: {predicted_label}")
    return predicted_label

if __name__ == "__main__":
    sample_text = """
    The company reported its quarterly earnings today, significantly exceeding analyst expectations.
    Revenue growth was strong across all major divisions, climbing 15% year-over-year to a record $2.5 billion.
    This impressive performance was driven by robust demand for its new product line and successful expansion into international markets.
    Citing these positive trends, the management team has upwardly revised its forecast for the full fiscal year and remains confident in its ability to deliver strong shareholder value.
    """
    predict_sentiment(sample_text)
