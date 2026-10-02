from typing import Tuple, List
import json
import numpy as np
import os
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences


def tokenize_texts(texts: List[str], max_words: int = 10000, max_length: int = 200):
    tokenizer = Tokenizer(num_words=max_words, oov_token="<OOV>")
    tokenizer.fit_on_texts(texts)
    sequences = tokenizer.texts_to_sequences(texts)
    padded = pad_sequences(sequences, maxlen=max_length, padding="post", truncating="post")
    return padded, tokenizer


def save_tokenizer(tokenizer: Tokenizer, path: str, max_length: int = 200):
    data = {
        "word_index": tokenizer.word_index,
        "num_words": tokenizer.num_words,
        "max_length": max_length,
    }
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f)


def load_tokenizer(path: str):
    import json
    with open(path, "r") as f:
        data = json.load(f)
    tokenizer = Tokenizer(num_words=data.get("num_words"), oov_token="<OOV>")
    tokenizer.word_index = data.get("word_index", {})
    return tokenizer, data.get("max_length", 200)
