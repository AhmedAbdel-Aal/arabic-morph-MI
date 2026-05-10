#!/usr/bin/env python3
"""Plot PCA effective dimensions by layer from saved diagnostics."""

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

THRESHOLDS = ["0.5", "0.9", "0.95"]


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_series(results_dir: Path, run_id: str, threshold: str) -> tuple[list[float], list[int]]:
    path = results_dir / run_id / "representation_diagnostics.json"
    payload = read_json(path)
    depths = []
    components = []
    for layer in payload["layers"]:
        depths.append(float(layer["normalized_depth"]))
        components.append(int(layer["effective_dimensions"][threshold]["n_components"]))
    return depths, components


def plot_effective_dimensions(results_dir: Path, output_path: Path) -> None:
    fig, axes = plt.subplots(
        nrows=2,
        ncols=3,
        figsize=(18, 10),
        sharex=True,
    )

    colors = {
        "Qwen3-1.7B": "#1f77b4",
        "Qwen3-8B": "#d62728",
        "Fanar-1-9B": "#2ca02c",
        "ALLaM-7B": "#9467bd",
    }

    for row_idx, surface in enumerate(["base", "full"]):
        for col_idx, threshold in enumerate(THRESHOLDS):
            ax = axes[row_idx][col_idx]
            for run_id, label in RUNS[surface]:
                depths, components = load_series(results_dir, run_id, threshold)
                ax.plot(
                    depths,
                    components,
                    marker="o",
                    markersize=3,
                    linewidth=1.8,
                    label=label,
                    color=colors.get(label),
                )

            percent = int(float(threshold) * 100)
            ax.set_title(f"{surface}: components for {percent}% variance")
            ax.set_xlabel("normalized layer depth")
            ax.set_ylabel("number of components")
            ax.grid(alpha=0.25)
            ax.set_xlim(0.0, 1.0)

    handles, labels = axes[0][0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=4, frameon=True)
    fig.suptitle("Effective dimensionality by layer", fontsize=16)
    fig.tight_layout(rect=(0.0, 0.08, 1.0, 0.96))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def load_fraction_series(results_dir: Path, run_id: str, threshold: str) -> tuple[list[int], list[float]]:
    path = results_dir / run_id / "representation_diagnostics.json"
    payload = read_json(path)
    layers = []
    fractions = []
    for layer in payload["layers"]:
        layers.append(int(layer["layer"]))
        fraction = layer["effective_dimensions"][threshold]["fraction_of_rank"]
        fractions.append(float(fraction) * 100.0)
    return layers, fractions


def plot_edim90_percent(results_dir: Path, output_path: Path) -> None:
    fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(14, 5), sharey=True)
    colors = {
        "Qwen3-1.7B": "#1f77b4",
        "Qwen3-8B": "#d62728",
        "Fanar-1-9B": "#2ca02c",
        "ALLaM-7B": "#9467bd",
    }

    for ax, surface in zip(axes, ["base", "full"]):
        for run_id, label in RUNS[surface]:
            layers, fractions = load_fraction_series(results_dir, run_id, "0.9")
            ax.plot(
                layers,
                fractions,
                marker="o",
                markersize=3,
                linewidth=1.8,
                label=label,
                color=colors.get(label),
            )
        ax.set_title(f"{surface}: components for 90% variance")
        ax.set_xlabel("layer")
        ax.set_ylabel("% of PCA rank")
        ax.grid(alpha=0.25)
        ax.set_ylim(0, 100)

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=4, frameon=True)
    fig.suptitle("Effective dimensionality: % of components needed for 90% variance", fontsize=14)
    fig.tight_layout(rect=(0.0, 0.13, 1.0, 0.93))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, default=Path("results"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/summary/effective_dimensions_by_layer.png"),
    )
    parser.add_argument(
        "--edim90-percent-output",
        type=Path,
        default=Path("results/summary/edim90_percent_by_layer.png"),
    )
    args = parser.parse_args()

    plot_effective_dimensions(args.results_dir, args.output)
    plot_edim90_percent(args.results_dir, args.edim90_percent_output)
    print(f"wrote {args.output}")
    print(f"wrote {args.edim90_percent_output}")


if __name__ == "__main__":
    main()
