from transformers import AutoTokenizer, AutoModelForSequenceClassification
from typing import List
import os
import torch
from torch.utils.data import Dataset, DataLoader


class TextTokenDataset(Dataset):
    """Tokenizes texts lazily in __getitem__ to avoid holding all tokens in memory."""

    def __init__(self, texts: List[str], labels: List[int], tokenizer, max_length: int = 128):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        enc = self.tokenizer(
            self.texts[idx],
            padding=False,
            truncation=True,
            max_length=self.max_length,
            return_tensors="pt",
        )
        return {
            "input_ids": enc["input_ids"].squeeze(0),
            "attention_mask": enc["attention_mask"].squeeze(0),
            "label": torch.tensor(self.labels[idx], dtype=torch.long),
        }


def build_bert_model(model_name: str = "distilbert-base-uncased", num_labels: int = 2):
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=num_labels)
    return tokenizer, model


def collate_fn(batch):
    from torch.nn.utils.rnn import pad_sequence
    input_ids = pad_sequence([item["input_ids"] for item in batch], batch_first=True, padding_value=0)
    attention_mask = pad_sequence([item["attention_mask"] for item in batch], batch_first=True, padding_value=0)
    labels = torch.stack([item["label"] for item in batch])
    return input_ids, attention_mask, labels


def train_bert_model(
    texts: List[str],
    labels: List[int],
    model_name: str = "distilbert-base-uncased",
    epochs: int = 3,
    batch_size: int = 16,
    max_length: int = 128,
    max_samples: int = None,
):
    import os as _os
    _os.environ.setdefault("OMP_NUM_THREADS", "4")
    torch.set_num_threads(4)

    tokenizer, model = build_bert_model(model_name)

    if max_samples is not None and len(texts) > max_samples:
        texts = texts[:max_samples]
        labels = labels[:max_samples]

    dataset = TextTokenDataset(texts, labels, tokenizer, max_length=max_length)
    loader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=True,
        collate_fn=collate_fn,
        num_workers=0,
    )

    optimizer = torch.optim.AdamW(model.parameters(), lr=3e-5)
    model.train()

    for epoch_idx in range(epochs):
        for batch_idx, batch in enumerate(loader):
            optimizer.zero_grad()
            input_ids, attention_mask, batch_labels = batch
            outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=batch_labels)
            loss = outputs.loss
            loss.backward()
            optimizer.step()
        if epoch_idx % 500 == 0:
            print(f"[bert_model] epoch {epoch_idx+1}/{epochs} batch {batch_idx} loss={loss.item():.4f}", flush=True)

    return model, tokenizer


def save_bert_model(model, tokenizer, path: str):
    os.makedirs(path, exist_ok=True)
    model.save_pretrained(path)
    tokenizer.save_pretrained(path)


def load_bert_model(path: str):
    tokenizer = AutoTokenizer.from_pretrained(path)
    model = AutoModelForSequenceClassification.from_pretrained(path)
    return tokenizer, model