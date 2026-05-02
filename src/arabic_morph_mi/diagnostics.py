from __future__ import annotations

import numpy as np


def normalized_layer_depth(n_layers: int) -> list[float]:
    if n_layers == 1:
        return [0.0]
    return [layer / (n_layers - 1) for layer in range(n_layers)]


def representation_diagnostics(hidden_by_text: dict[str, np.ndarray]) -> dict:
    texts = sorted(hidden_by_text)
    X = np.stack([hidden_by_text[text] for text in texts])
    n_texts, n_layers, hidden_size = X.shape

    layers = []
    for layer in range(n_layers):
        X_layer = X[:, layer, :]
        centered = X_layer - X_layer.mean(axis=0, keepdims=True)
        _, s, _ = np.linalg.svd(centered, full_matrices=False)
        variance = s**2
        total = float(variance.sum())
        cumulative = np.cumsum(variance) / total if total > 0 else np.zeros_like(variance)

        effective_dims = {}
        for threshold in [0.5, 0.9, 0.95]:
            if total <= 0:
                n_components = 0
            else:
                n_components = int(np.searchsorted(cumulative, threshold) + 1)
            effective_dims[str(threshold)] = {
                "n_components": n_components,
                "fraction_of_rank": float(n_components / max(1, len(s))),
            }

        layers.append(
            {
                "layer": layer,
                "normalized_depth": normalized_layer_depth(n_layers)[layer],
                "max_abs_activation": float(np.max(np.abs(X_layer))),
                "mean_abs_activation": float(np.mean(np.abs(X_layer))),
                "std_activation": float(np.std(X_layer)),
                "effective_dimensions": effective_dims,
            }
        )

    return {
        "n_texts": n_texts,
        "n_layers": n_layers,
        "hidden_size": hidden_size,
        "layers": layers,
    }
