import tensorflow as tf
from tensorflow.keras import layers, models
from typing import List
import numpy as np
import os


def build_cnn_model(vocab_size: int = 10000, max_length: int = 200, embedding_dim: int = 100, num_classes: int = 6):
    model = models.Sequential([
        layers.Embedding(input_dim=vocab_size, output_dim=embedding_dim, input_length=max_length),
        layers.Conv1D(128, 5, activation="relu"),
        layers.GlobalMaxPooling1D(),
        layers.Dense(64, activation="relu"),
        layers.Dropout(0.5),
        layers.Dense(num_classes, activation="softmax"),
    ])
    model.compile(optimizer="adam", loss="sparse_categorical_crossentropy", metrics=["accuracy"])
    return model


def train_cnn_model(X: np.ndarray, y: np.ndarray, epochs: int = 5, batch_size: int = 32):
    model = build_cnn_model(num_classes=int(np.max(y)) + 1)
    # Training is also invoked from the API, where stdout may be closed if the
    # client disconnects or the server is launched with redirected output.
    # Keras' progress renderer writes to that stream and can abort training.
    model.fit(X, y, epochs=epochs, batch_size=batch_size, validation_split=0.1, verbose=0)
    return model


def save_cnn_model(model, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    model.save(path)


def load_cnn_model(path: str):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Model not found at {path}")
    return tf.keras.models.load_model(path)
