#!/usr/bin/env python3
"""Overlay template probe curves with PCA effective dimensionality."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path

cache_root = Path(tempfile.gettempdir()) / "arabic_morph_mi_cache"
cache_root.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(cache_root / "matplotlib"))
os.environ.setdefault("XDG_CACHE_HOME", str(cache_root / "xdg"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


RUNS = {
    "base": [
        ("E03", "Qwen3-1.7B"),
        ("E06", "Qwen3-8B"),
        ("E07", "Fanar-1-9B"),
        ("E08", "ALLaM-7B"),
    ],
    "full": [
        ("E05b", "Qwen3-1.7B"),
        ("E06b", "Qwen3-8B"),
        ("E07b", "Fanar-1-9B"),
        ("E08b", "ALLaM-7B"),
    ],
}

PROBES = [
    ("real_templates_random", "real templates"),
    ("nonce_templates_heldout_roots", "nonce held-out roots"),
    ("train_real_test_nonce_overlap", "real -> nonce"),
    ("train_nonce_test_real_overlap", "nonce -> real"),
]


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_probe(results_dir: Path, run_id: str, probe: str) -> tuple[list[int], list[float], float, float]:
    payload = read_json(results_dir / run_id / "results.json")
    result = payload["results"][probe]
    layers = [int(layer) for layer in result["layer_indices"]]
    accuracy = [float(value) for value in result["accuracy_per_layer"]]
    ngram = float(result["ngram_accuracy"])
    control = float(result["peak_control_accuracy"])
    return layers, accuracy, ngram, control


def load_edim90(results_dir: Path, run_id: str) -> tuple[list[int], list[float]]:
    payload = read_json(results_dir / run_id / "representation_diagnostics.json")
    layers = []
    edim90 = []
    for layer in payload["layers"]:
        layers.append(int(layer["layer"]))
        fraction = layer["effective_dimensions"]["0.9"]["fraction_of_rank"]
        edim90.append(float(fraction) * 100.0)
    return layers, edim90


def plot_surface_overlay(results_dir: Path, surface: str, output_path: Path) -> None:
    fig, axes = plt.subplots(
        nrows=len(RUNS[surface]),
        ncols=len(PROBES),
        figsize=(18, 12),
        sharex=False,
        sharey="col",
    )

    if len(RUNS[surface]) == 1:
        axes = [axes]

    for row_idx, (run_id, model_label) in enumerate(RUNS[surface]):
        edim_layers, edim_values = load_edim90(results_dir, run_id)
        for col_idx, (probe, probe_label) in enumerate(PROBES):
            ax = axes[row_idx][col_idx]
            layers, accuracy, ngram, _control = load_probe(results_dir, run_id, probe)

            ax.plot(
                layers,
                accuracy,
                color="#1f77b4",
                marker="o",
                markersize=2.5,
                linewidth=1.7,
                label="probe accuracy",
            )
            ax.axhline(
                ngram,
                color="#1f77b4",
                linestyle=":",
                linewidth=1.1,
                alpha=0.75,
                label="n-gram baseline" if row_idx == 0 and col_idx == 0 else None,
            )
            ax.set_ylim(0.0, 1.05)
            ax.grid(alpha=0.25)
            ax.set_xlabel("layer")
            if col_idx == 0:
                ax.set_ylabel(f"{model_label}\naccuracy")
            if row_idx == 0:
                ax.set_title(probe_label)

            twin = ax.twinx()
            twin.plot(
                edim_layers,
                edim_values,
                color="#d62728",
                linestyle="--",
                linewidth=1.4,
                alpha=0.85,
                label="edim90 %",
            )
            twin.set_ylim(0, 100)
            if col_idx == len(PROBES) - 1:
                twin.set_ylabel("edim90 %")
            else:
                twin.set_yticklabels([])

    handles = [
        plt.Line2D([0], [0], color="#1f77b4", marker="o", linewidth=1.7, label="probe accuracy"),
        plt.Line2D([0], [0], color="#1f77b4", linestyle=":", linewidth=1.1, label="n-gram baseline"),
        plt.Line2D([0], [0], color="#d62728", linestyle="--", linewidth=1.4, label="edim90 %"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=3, frameon=True)
    fig.suptitle(f"{surface}: template probe accuracy vs effective dimensionality", fontsize=16)
    fig.tight_layout(rect=(0.0, 0.06, 1.0, 0.96))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, default=Path("results"))
    parser.add_argument("--out-dir", type=Path, default=Path("results/summary"))
    args = parser.parse_args()

    for surface in ["base", "full"]:
        output_path = args.out_dir / f"{surface}_probe_geometry_overlay.png"
        plot_surface_overlay(args.results_dir, surface, output_path)
        print(f"wrote {output_path}")


if __name__ == "__main__":
    main()
