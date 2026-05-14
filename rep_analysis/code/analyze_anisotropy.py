#!/usr/bin/env python3
"""Create an explicit layer-wise anisotropy report from geometry metrics."""

from __future__ import annotations

import argparse
import csv
import math
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

cache_root = Path(tempfile.gettempdir()) / "arabic_morph_mi_cache"
cache_root.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(cache_root / "matplotlib"))
os.environ.setdefault("XDG_CACHE_HOME", str(cache_root / "xdg"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


MODELS = ["Qwen3-1.7B", "Qwen3-8B", "Fanar-1-9B", "ALLaM-7B"]
SURFACES = ["base", "full"]

COLORS = {
    "Qwen3-1.7B": "#1f77b4",
    "Qwen3-8B": "#d62728",
    "Fanar-1-9B": "#2ca02c",
    "ALLaM-7B": "#9467bd",
}


def read_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def savefig(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(path, dpi=200)
    plt.close()


def as_float(row: dict, key: str) -> float:
    return float(row[key])


def as_int(row: dict, key: str) -> int:
    return int(float(row[key]))


def add_anisotropy_flags(rows: list[dict]) -> list[dict]:
    out = []
    for row in rows:
        top_pc = as_float(row, "top_pc_variance_ratio")
        edim90 = as_float(row, "edim90_fraction")
        effective_rank = as_float(row, "effective_rank_fraction")
        mean_cos = as_float(row, "mean_pairwise_cosine")

        if top_pc >= 0.9 or edim90 <= 0.02:
            bucket = "collapsed"
        elif top_pc >= 0.5 or edim90 <= 0.1:
            bucket = "high"
        elif top_pc >= 0.25 or edim90 <= 0.3:
            bucket = "moderate"
        else:
            bucket = "low"

        new_row = dict(row)
        new_row.update(
            {
                "pc1_anisotropy": top_pc,
                "edim90_fraction": edim90,
                "effective_rank_fraction": effective_rank,
                "mean_pairwise_cosine": mean_cos,
                "anisotropy_bucket": bucket,
            }
        )
        out.append(new_row)
    return out


def summarize(rows: list[dict]) -> list[dict]:
    summary = []
    for surface in SURFACES:
        for model in MODELS:
            model_rows = [r for r in rows if r["surface"] == surface and r["model"] == model]
            if not model_rows:
                continue

            n_layers = len(model_rows)
            top_pc = [as_float(r, "pc1_anisotropy") for r in model_rows]
            edim90 = [as_float(r, "edim90_fraction") for r in model_rows]
            effective_rank = [as_float(r, "effective_rank_fraction") for r in model_rows]
            mean_cos = [as_float(r, "mean_pairwise_cosine") for r in model_rows]
            collapsed_layers = [
                as_int(r, "layer")
                for r in model_rows
                if as_float(r, "pc1_anisotropy") >= 0.9 or as_float(r, "edim90_fraction") <= 0.02
            ]
            first_collapsed = collapsed_layers[0] if collapsed_layers else ""
            last_collapsed = collapsed_layers[-1] if collapsed_layers else ""
            summary.append(
                {
                    "model": model,
                    "surface": surface,
                    "n_layers": n_layers,
                    "max_pc1_anisotropy": max(top_pc),
                    "mean_pc1_anisotropy": sum(top_pc) / n_layers,
                    "min_edim90_fraction": min(edim90),
                    "mean_edim90_fraction": sum(edim90) / n_layers,
                    "min_effective_rank_fraction": min(effective_rank),
                    "mean_effective_rank_fraction": sum(effective_rank) / n_layers,
                    "max_mean_pairwise_cosine": max(mean_cos),
                    "mean_pairwise_cosine": sum(mean_cos) / n_layers,
                    "collapsed_layer_count": len(collapsed_layers),
                    "collapsed_layer_fraction": len(collapsed_layers) / n_layers,
                    "first_collapsed_layer": first_collapsed,
                    "last_collapsed_layer": last_collapsed,
                }
            )
    return summary


def plot_metric(rows: list[dict], metric: str, title: str, ylabel: str, filename: str, out_dir: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(14, 5), sharey=False)
    for ax, surface in zip(axes, SURFACES):
        for model in MODELS:
            series = [r for r in rows if r["surface"] == surface and r["model"] == model]
            if not series:
                continue
            ax.plot(
                [as_int(r, "layer") for r in series],
                [as_float(r, metric) for r in series],
                marker="o",
                markersize=3,
                linewidth=1.8,
                color=COLORS[model],
                label=model,
            )
        ax.set_title(surface)
        ax.set_xlabel("layer")
        ax.set_ylabel(ylabel)
        ax.grid(alpha=0.25)
        if metric != "mean_pairwise_cosine":
            ax.set_ylim(0, 1.02)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=4, frameon=True)
    fig.suptitle(title)
    fig.tight_layout(rect=(0.0, 0.13, 1.0, 0.92))
    savefig(out_dir / filename)


def plot_dashboard(rows: list[dict], out_dir: Path) -> None:
    metrics = [
        ("pc1_anisotropy", "PC1 variance share"),
        ("edim90_fraction", "fraction of rank for 90% variance"),
        ("effective_rank_fraction", "effective rank fraction"),
        ("mean_pairwise_cosine", "mean pairwise cosine"),
    ]
    fig, axes = plt.subplots(len(metrics), 2, figsize=(14, 15), sharex=False)
    for row_idx, (metric, label) in enumerate(metrics):
        for col_idx, surface in enumerate(SURFACES):
            ax = axes[row_idx][col_idx]
            for model in MODELS:
                series = [r for r in rows if r["surface"] == surface and r["model"] == model]
                if not series:
                    continue
                ax.plot(
                    [as_int(r, "layer") for r in series],
                    [as_float(r, metric) for r in series],
                    marker="o",
                    markersize=2.5,
                    linewidth=1.5,
                    color=COLORS[model],
                    label=model,
                )
            ax.set_title(f"{surface}: {label}")
            ax.set_xlabel("layer")
            ax.set_ylabel(label)
            ax.grid(alpha=0.25)
            if metric != "mean_pairwise_cosine":
                ax.set_ylim(0, 1.02)
    handles, labels = axes[0][0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=4, frameon=True)
    fig.suptitle("Layer-wise anisotropy dashboard")
    fig.tight_layout(rect=(0.0, 0.06, 1.0, 0.97))
    savefig(out_dir / "anisotropy_dashboard.png")


def fmt(value: object) -> str:
    if value == "":
        return ""
    value_float = float(value)
    if math.isnan(value_float):
        return "nan"
    return f"{value_float:.3f}"


def write_report(summary_rows: list[dict], out_dir: Path) -> None:
    lines = [
        "# Layer-Wise Anisotropy Analysis",
        "",
        "This is the explicit anisotropy analysis we discussed. It is computed from saved pooled hidden states, using the geometry metrics in `rep_analysis/results/01_geometry/geometry_metrics.csv`.",
        "",
        "## What Was Measured",
        "",
        "- `pc1_anisotropy`: variance share of the first principal component. High values mean the representations are dominated by one direction.",
        "- `edim90_fraction`: fraction of available rank needed to explain 90% variance. Low values mean the representation is effectively low-dimensional.",
        "- `effective_rank_fraction`: entropy-based effective rank divided by rank. Low values mean variance is concentrated in few directions.",
        "- `mean_pairwise_cosine`: average raw cosine similarity between examples. High values mean vectors occupy a narrow cone.",
        "",
        "I mark a layer as `collapsed` when `pc1_anisotropy >= 0.90` or `edim90_fraction <= 0.02`.",
        "",
        "## Summary",
        "",
        "| Model | Surface | max PC1 | mean PC1 | min edim90 | mean edim90 | collapsed layers | first collapsed | last collapsed |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary_rows:
        lines.append(
            f"| {row['model']} | {row['surface']} | {fmt(row['max_pc1_anisotropy'])} | "
            f"{fmt(row['mean_pc1_anisotropy'])} | {fmt(row['min_edim90_fraction'])} | "
            f"{fmt(row['mean_edim90_fraction'])} | {row['collapsed_layer_count']} | "
            f"{row['first_collapsed_layer']} | {row['last_collapsed_layer']} |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "1. Qwen3-1.7B, Qwen3-8B, and ALLaM show severe anisotropy/collapse in many layers. In those layers, one principal direction can explain almost all variance and edim90 drops near zero.",
            "2. Fanar is qualitatively different. It never reaches the collapse threshold in these runs; its variance remains distributed across many more directions.",
            "3. This does not mean Fanar is automatically more morphological. It means Fanar's representation space is less dominated by a global common direction, so cosine/centroid analyses are easier to trust.",
            "4. For Qwen and ALLaM, probe accuracy must be read together with PC-removal and nuisance analyses. A high probe score in a collapsed layer may reflect morphology, tokenization, source/domain structure, or a mixture.",
            "5. The important contrast is therefore not just `which model probes best`; it is `which model has recoverable template information in layers whose geometry is not dominated by nuisance directions`.",
            "",
            "## Files",
            "",
            "- `anisotropy_by_layer.csv`: layer-wise metrics and collapse labels.",
            "- `anisotropy_summary.csv`: model/surface summary table.",
            "- `anisotropy_dashboard.png`: all anisotropy metrics in one figure.",
            "- `pc1_anisotropy_by_layer.png`: PC1 variance share by layer.",
            "- `edim90_fraction_by_layer.png`: effective dimensionality by layer.",
            "- `effective_rank_fraction_by_layer.png`: entropy effective-rank by layer.",
            "- `mean_pairwise_cosine_by_layer.png`: raw cone anisotropy by layer.",
            "",
        ]
    )
    (out_dir / "ANISOTROPY.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--geometry",
        type=Path,
        default=ROOT / "rep_analysis/results/01_geometry/geometry_metrics.csv",
    )
    parser.add_argument("--out-dir", type=Path, default=ROOT / "rep_analysis/results/00_anisotropy")
    args = parser.parse_args()

    rows = add_anisotropy_flags(read_rows(args.geometry))
    summary_rows = summarize(rows)

    write_csv(
        args.out_dir / "anisotropy_by_layer.csv",
        rows,
        [
            "run_id",
            "model",
            "surface",
            "real_split",
            "n_texts",
            "n_layers",
            "hidden_size",
            "layer",
            "normalized_depth",
            "rank",
            "pc1_anisotropy",
            "edim90_components",
            "edim90_fraction",
            "effective_rank",
            "effective_rank_fraction",
            "participation_ratio",
            "participation_ratio_fraction",
            "mean_pairwise_cosine",
            "anisotropy_bucket",
        ],
    )
    write_csv(
        args.out_dir / "anisotropy_summary.csv",
        summary_rows,
        [
            "model",
            "surface",
            "n_layers",
            "max_pc1_anisotropy",
            "mean_pc1_anisotropy",
            "min_edim90_fraction",
            "mean_edim90_fraction",
            "min_effective_rank_fraction",
            "mean_effective_rank_fraction",
            "max_mean_pairwise_cosine",
            "mean_pairwise_cosine",
            "collapsed_layer_count",
            "collapsed_layer_fraction",
            "first_collapsed_layer",
            "last_collapsed_layer",
        ],
    )

    plot_metric(
        rows,
        "pc1_anisotropy",
        "Layer-wise anisotropy: first PC variance share",
        "PC1 variance share",
        "pc1_anisotropy_by_layer.png",
        args.out_dir,
    )
    plot_metric(
        rows,
        "edim90_fraction",
        "Layer-wise anisotropy: components needed for 90% variance",
        "edim90 fraction",
        "edim90_fraction_by_layer.png",
        args.out_dir,
    )
    plot_metric(
        rows,
        "effective_rank_fraction",
        "Layer-wise anisotropy: effective rank",
        "effective rank fraction",
        "effective_rank_fraction_by_layer.png",
        args.out_dir,
    )
    plot_metric(
        rows,
        "mean_pairwise_cosine",
        "Layer-wise anisotropy: raw mean pairwise cosine",
        "mean pairwise cosine",
        "mean_pairwise_cosine_by_layer.png",
        args.out_dir,
    )
    plot_dashboard(rows, args.out_dir)
    write_report(summary_rows, args.out_dir)
    print(f"wrote {args.out_dir}")


if __name__ == "__main__":
    main()
