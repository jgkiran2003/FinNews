import torch
from transformers import AutoTokenizer, AutoModel, Trainer, TrainingArguments
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error

# --- 1. Define the Custom Multi-Output Regression Model ---
# This is the same custom architecture we designed before.

class MultiOutputRegressionModel(torch.nn.Module):
    def __init__(self, model_name="distilbert-base-uncased", num_outputs=3):
        super(MultiOutputRegressionModel, self).__init__()
        self.bert_body = AutoModel.from_pretrained(model_name)
        self.regression_head = torch.nn.Linear(self.bert_body.config.hidden_size, num_outputs)

    def forward(self, input_ids, attention_mask, labels=None):
        outputs = self.bert_body(input_ids=input_ids, attention_mask=attention_mask)
        cls_output = outputs.last_hidden_state[:, 0]
        logits = self.regression_head(cls_output)
        
        # During training, the Trainer expects a loss value in the output
        loss = None
        if labels is not None:
            loss_fct = torch.nn.MSELoss()
            loss = loss_fct(logits, labels.float())
            
        return (loss, logits) if loss is not None else logits

# --- 2. Define the Custom Trainer ---
# This is the new part. We subclass the Trainer to ensure it uses the
# model's custom loss calculation correctly.

class RegressionTrainer(Trainer):
    def compute_loss(self, model, inputs, return_outputs=False):
        # Extract labels from the inputs
        labels = inputs.pop("labels")
        
        # Forward pass
        outputs = model(**inputs, labels=labels)
        loss, logits = outputs
        
        return (loss, {"logits": logits}) if return_outputs else loss

# --- 3. Prepare Your Data (Example) ---
# We'll use dummy data for this example. Replace this with loading your real data.
dummy_data = {
    'text': [
        "Company reports record profits, stock soars.",
        "New regulations could hurt the tech sector.",
        "Market remains flat despite good inflation news.",
        "Tech giant atorch.nnounces massive layoffs.",
        "New product launch exceeds all expectations."
    ],
    # Target values: [volatility, volume_change, price_change]
    'labels': [
        [0.05, 0.8, 1.5],
        [0.03, -0.2, -0.5],
        [0.01, 0.1, 0.1],
        [0.06, 0.3, -2.0],
        [0.07, 1.2, 3.0]
    ]
}
df = pd.DataFrame(dummy_data)
train_df, val_df = train_test_split(df, test_size=0.2, random_state=42)

# --- 4. Create PyTorch Datasets ---
tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
train_encodings = tokenizer(train_df['text'].tolist(), truncation=True, padding=True)
val_encodings = tokenizer(val_df['text'].tolist(), truncation=True, padding=True)

class RegressionDataset(torch.utils.data.Dataset):
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels

    def __getitem__(self, idx):
        item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
        item['labels'] = torch.tensor(self.labels[idx])
        return item

    def __len__(self):
        return len(self.labels)

train_dataset = RegressionDataset(train_encodings, train_df['labels'].tolist())
val_dataset = RegressionDataset(val_encodings, val_df['labels'].tolist())

# --- 5. Fine-Tune the Model ---
model = MultiOutputRegressionModel(num_outputs=3)

training_args = TrainingArguments(
    output_dir='./results_regression',
    num_train_epochs=5,
    per_device_train_batch_size=2,
    per_device_eval_batch_size=2,
    logging_dir='./logs_regression',
    evaluation_strategy="epoch",
)

def compute_metrics_for_regression(eval_pred):
    logits, labels = eval_pred
    rmse = mean_squared_error(labels, logits, squared=False)
    return {"rmse": rmse}

trainer = RegressionTrainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
    compute_metrics=compute_metrics_for_regression,
)

print("Starting fine-tuning for multi-output regression...")
trainer.train()

# --- 6. Make a final prediction ---
sample_text = "The company is expected to miss earnings estimates."
inputs = tokenizer(sample_text, return_tensors="pt")
model.eval()
with torch.no_grad():
    predictions = model(**inputs)
print(f"\nPrediction for '{sample_text}':")
print(f"  Volatility: {predictions[0][0]:.3f}, Volume Change: {predictions[0][1]:.3f}, Price Change: {predictions[0][2]:.3f}")