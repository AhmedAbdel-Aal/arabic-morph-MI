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


def word_type_control_labels(texts: list[str], y: np.ndarray, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    labels, counts = np.unique(y, return_counts=True)
    probs = counts / counts.sum()
    word_types = sorted(set(texts))
    label_by_type = {text: int(rng.choice(labels, p=probs)) for text in word_types}
    return np.array([label_by_type[text] for text in texts])


def layer_probe(
    X: np.ndarray,
    y: list[int],
    labels: list[str],
    texts: list[str],
    train: np.ndarray,
    test: np.ndarray,
    control_seed: int = 0,
    token_counts: list[int] | None = None,
) -> dict:
    y_arr = np.asarray(y)
    y_control = word_type_control_labels(texts, y_arr, control_seed)
    accuracies = []
    control_accuracies = []
    for layer in range(X.shape[1]):
        score, _ = train_probe(X[:, layer, :], y_arr, train, test)
        control_score, _ = train_probe(X[:, layer, :], y_control, train, test)
        accuracies.append(score)
        control_accuracies.append(control_score)
        print(f"layer {layer:02d}: accuracy={score:.3f} control={control_score:.3f}")

    peak_layer = int(np.argmax(accuracies))
    peak_accuracy, pred = train_probe(X[:, peak_layer, :], y_arr, train, test)
    label_ids = list(range(len(labels)))
    selectivity = np.array(accuracies) - np.array(control_accuracies)
    layer_indices = list(range(X.shape[1]))
    if X.shape[1] == 1:
        depths = [0.0]
    else:
        depths = [idx / (X.shape[1] - 1) for idx in layer_indices]

    token_count_accuracy = {}
    if token_counts is not None:
        token_counts_arr = np.asarray(token_counts)
        for count in sorted(set(token_counts_arr[test].tolist())):
            mask = token_counts_arr[test] == count
            token_count_accuracy[str(int(count))] = {
                "n": int(mask.sum()),
                "accuracy": float(accuracy_score(y_arr[test][mask], pred[mask])),
            }

    return {
        "layer_indices": layer_indices,
        "normalized_layer_depth": depths,
        "accuracy_per_layer": accuracies,
        "control_accuracy_per_layer": control_accuracies,
        "selectivity_per_layer": selectivity.tolist(),
        "peak_layer": peak_layer,
        "peak_normalized_depth": depths[peak_layer],
        "peak_accuracy": float(peak_accuracy),
        "peak_control_accuracy": float(control_accuracies[peak_layer]),
        "peak_selectivity": float(selectivity[peak_layer]),
        "ngram_accuracy": char_ngram_score(texts, y_arr, train, test),
        "chance": 1 / len(labels),
        "token_count_accuracy_at_peak": token_count_accuracy,
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
