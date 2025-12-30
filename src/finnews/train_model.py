import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments

# --- 1. Load and Prepare Your Labeled Data ---
print("Loading financial sentiment data...")
try:
    # The 'latin1' encoding is often needed for this specific dataset
    df = pd.read_csv('./dev/data/sentiment_data.csv', encoding='latin1')
except FileNotFoundError:
    print("Error: 'sentiment_data.csv' not found. Make sure it's in the same folder.")

# Drop any rows with missing data
df.dropna(inplace=True)

# Create a mapping from category name to integer ID
unique_labels = df['Sentiment'].unique()
label2id = {label: i for i, label in enumerate(unique_labels)}
id2label = {i: label for i, label in enumerate(unique_labels)}

# Add a new column with the integer labels
df['label'] = df['Sentiment'].map(label2id)

print(f"Loaded {len(df)} labeled sentences.")
print(f"Categories found: {list(unique_labels)}")

# --- 2. Load Pre-trained FinBERT Tokenizer and Model ---
model_name = "ProsusAI/finbert"
print(f"Loading tokenizer and model for '{model_name}'...")

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(
    model_name,
    num_labels=len(unique_labels),
    id2label=id2label,
    label2id=label2id
)

# --- 3. Create a PyTorch Dataset ---
# Split your data into training and validation sets
train_df, val_df = train_test_split(df, test_size=0.2, random_state=42, stratify=df['label'])

# Tokenize the text
train_encodings = tokenizer(train_df['Sentence'].tolist(), truncation=True, padding=True)
val_encodings = tokenizer(val_df['Sentence'].tolist(), truncation=True, padding=True)

# Create a custom PyTorch Dataset class
class FinancialDataset(torch.utils.data.Dataset):
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels

    def __getitem__(self, idx):
        item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
        item['labels'] = torch.tensor(self.labels[idx])
        return item

    def __len__(self):
        return len(self.labels)
        
train_dataset = FinancialDataset(train_encodings, train_df['label'].tolist())
val_dataset = FinancialDataset(val_encodings, val_df['label'].tolist())

# --- 4. Fine-Tune the Model with the Trainer API ---
print("Configuring training...")

# Define the training arguments
training_args = TrainingArguments(
    output_dir='./final_model/checkpoints',          # Directory to save results
    num_train_epochs=3,              # Total number of training epochs
    per_device_train_batch_size=16,   # Batch size for training
    per_device_eval_batch_size=16,    # Batch size for evaluation
    bf16=False,                     # Use mixed precision training
    fp16=True,                     # Use mixed precision training
    optim="adamw_torch_fused",       # Use fused AdamW optimizer
    logging_dir='./final_model/logs',            # Directory for storing logs
    logging_steps=10,
    eval_strategy="epoch",     # Evaluate at the end of each epoch
    save_strategy="epoch",           # Save checkpoint at the end of each epoch
    load_best_model_at_end=True,     # Load the best model found during training
)

# Define a function to compute metrics
def compute_metrics(pred):
    labels = pred.label_ids
    preds = pred.predictions.argmax(-1)
    acc = accuracy_score(labels, preds)
    return {'accuracy': acc}

# Create the Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
    compute_metrics=compute_metrics,
)

# Start training!
print("Starting fine-tuning...")
trainer.train()
print("Fine-tuning complete.")

# --- 5. Evaluate the Final Model ---
print("\nEvaluating the fine-tuned model...")
eval_results = trainer.evaluate()
print(f"\nFinal evaluation accuracy: {eval_results['eval_accuracy'] * 100:.2f}%")

# --- 6. Save the Final Model ---
final_model_path = "./final_model/model"
trainer.save_model(final_model_path)
tokenizer.save_pretrained(final_model_path)
print(f"Model saved to {final_model_path}")


