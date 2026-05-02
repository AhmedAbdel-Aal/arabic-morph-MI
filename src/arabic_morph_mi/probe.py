from __future__ import annotations

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


def train_probe(X: np.ndarray, y: np.ndarray, train: np.ndarray, test: np.ndarray) -> tuple[float, np.ndarray]:
    clf = make_pipeline(
        StandardScaler(),
        LogisticRegression(max_iter=5000, C=1.0),
    )
    clf.fit(X[train], y[train])
    pred = clf.predict(X[test])
    return float(accuracy_score(y[test], pred)), pred


def char_ngram_score(texts: list[str], y: np.ndarray, train: np.ndarray, test: np.ndarray) -> float:
    vec = TfidfVectorizer(analyzer="char", ngram_range=(1, 4), lowercase=False)
    X_train = vec.fit_transform([texts[i] for i in train])
    X_test = vec.transform([texts[i] for i in test])
    clf = LogisticRegression(max_iter=5000, C=1.0)
    clf.fit(X_train, y[train])
    pred = clf.predict(X_test)
    return float(accuracy_score(y[test], pred))


def layer_probe(
    X: np.ndarray,
    y: list[int],
    labels: list[str],
    texts: list[str],
    train: np.ndarray,
    test: np.ndarray,
) -> dict:
    y_arr = np.asarray(y)
    accuracies = []
    for layer in range(X.shape[1]):
        score, _ = train_probe(X[:, layer, :], y_arr, train, test)
        accuracies.append(score)
        print(f"layer {layer:02d}: accuracy={score:.3f}")

    peak_layer = int(np.argmax(accuracies))
    peak_accuracy, pred = train_probe(X[:, peak_layer, :], y_arr, train, test)
    label_ids = list(range(len(labels)))

    return {
        "accuracy_per_layer": accuracies,
        "peak_layer": peak_layer,
        "peak_accuracy": float(peak_accuracy),
        "ngram_accuracy": char_ngram_score(texts, y_arr, train, test),
        "chance": 1 / len(labels),
        "confusion_matrix": confusion_matrix(y_arr[test], pred, labels=label_ids).tolist(),
        "classification_report": classification_report(
            y_arr[test],
            pred,
            labels=label_ids,
            target_names=labels,
            output_dict=True,
            zero_division=0,
        ),
    }
