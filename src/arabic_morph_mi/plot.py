from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def plot_curves(results: dict[str, dict], path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    n = len(results)
    cols = 2
    rows = int(np.ceil(n / cols))
    fig, axes = plt.subplots(rows, cols, figsize=(13, 4 * rows), squeeze=False)

    for ax, (name, result) in zip(axes.reshape(-1), results.items()):
        layers = result.get("normalized_layer_depth") or np.arange(len(result["accuracy_per_layer"]))
        ax.plot(layers, result["accuracy_per_layer"], marker="o", label="model")
        ax.plot(layers, result["control_accuracy_per_layer"], marker="s", linestyle="-.", label="control")
        ax.axhline(result["ngram_accuracy"], color="black", linestyle="--", label="char n-gram")
        ax.axhline(result["chance"], color="gray", linestyle=":", label="chance")
        ax.set_title(f"{name}: peak {result['peak_accuracy']:.3f}, sel {result['peak_selectivity']:.3f}")
        ax.set_xlabel("normalized layer depth")
        ax.set_ylabel("accuracy")
        ax.set_ylim(0, 1)
        ax.grid(alpha=0.25)
        ax.legend(fontsize=8)

    for ax in axes.reshape(-1)[n:]:
        ax.axis("off")

    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
