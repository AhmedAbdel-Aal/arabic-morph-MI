#!/usr/bin/env python3
"""Run local representation analyses over saved hidden states."""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

cache_root = Path(tempfile.gettempdir()) / "arabic_morph_mi_cache"
cache_root.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(cache_root / "matplotlib"))
os.environ.setdefault("XDG_CACHE_HOME", str(cache_root / "xdg"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.utils.extmath import randomized_svd

from arabic_morph_mi.data import Item, family_key, load_productivity_dataset, make_items, overlap_by_label, with_labels
from arabic_morph_mi.splits import grouped_random_split, heldout_root_split, random_split


RUNS = [
    ("REP01_E03", "Qwen3-1.7B", "base", "item"),
    ("REP01_E05b", "Qwen3-1.7B", "full", "family"),
    ("REP01_E06", "Qwen3-8B", "base", "item"),
    ("REP01_E06b", "Qwen3-8B", "full", "family"),
    ("REP01_E07", "Fanar-1-9B", "base", "item"),
    ("REP01_E07b", "Fanar-1-9B", "full", "family"),
    ("REP01_E08", "ALLaM-7B", "base", "item"),
    ("REP01_E08b", "ALLaM-7B", "full", "family"),
]

MAIN_PROBES = [
    ("real_templates_random", "real templates"),
    ("nonce_templates_heldout_roots", "nonce held-out roots"),
    ("train_real_test_nonce_overlap", "real -> nonce"),
    ("train_nonce_test_real_overlap", "nonce -> real"),
]

PC_K_VALUES = [0, 1, 2, 5, 10]

COLORS = {
    "Qwen3-1.7B": "#1f77b4",
    "Qwen3-8B": "#d62728",
    "Fanar-1-9B": "#2ca02c",
    "ALLaM-7B": "#9467bd",
}


@dataclass(frozen=True)
class RunInfo:
    run_id: str
    model_short: str
    surface: str
    real_split: str
    results_dir: Path

    @property
    def run_dir(self) -> Path:
        return self.results_dir / self.run_id


@dataclass
class ProbeSpec:
    name: str
    label: str
    items: list[Item]
    labels: list[str]
    y: list[int]
    train: np.ndarray
    test: np.ndarray


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def savefig(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(path, dpi=200)
    plt.close()


def load_run_hidden(run: RunInfo) -> tuple[np.ndarray, list[str]]:
    payload = np.load(run.run_dir / "hidden_representations.npz", allow_pickle=False)
    hidden = payload["hidden"].astype(np.float32)
    texts = [str(text) for text in payload["texts"].tolist()]
    return hidden, texts


def explicit_split(
    train_items: list[Item],
    test_items: list[Item],
    target: str,
) -> tuple[list[Item], list[str], list[int], np.ndarray, np.ndarray]:
    items = train_items + test_items
    labels, y = with_labels(items, target)
    train = np.arange(len(train_items))
    test = np.arange(len(train_items), len(items))
    return items, labels, y, train, test


def build_template_probe_specs(data_path: Path, surface: str, real_split: str) -> list[ProbeSpec]:
    payload = load_productivity_dataset(data_path)
    real = make_items(payload, "real", surface)
    nonce = make_items(payload, "nonce", "base")
    real_overlap, nonce_overlap = overlap_by_label(real, nonce)

    specs = []

    labels, y = with_labels(real, "template")
    if real_split == "family":
        train, test = grouped_random_split(real, y, test_size=0.2, seed=42)
    else:
        train, test = random_split(y, test_size=0.2, seed=42)
    specs.append(ProbeSpec("real_templates_random", "real templates", real, labels, y, train, test))

    labels, y = with_labels(nonce, "template")
    train, test = heldout_root_split(nonce, y, test_size=0.2, seed=44)
    specs.append(ProbeSpec("nonce_templates_heldout_roots", "nonce held-out roots", nonce, labels, y, train, test))

    items, labels, y, train, test = explicit_split(real_overlap, nonce_overlap, "template")
    specs.append(ProbeSpec("train_real_test_nonce_overlap", "real -> nonce", items, labels, y, train, test))

    items, labels, y, train, test = explicit_split(nonce_overlap, real_overlap, "template")
    specs.append(ProbeSpec("train_nonce_test_real_overlap", "nonce -> real", items, labels, y, train, test))

    return specs


def hidden_for_items(hidden: np.ndarray, text_to_index: dict[str, int], items: list[Item]) -> np.ndarray:
    indices = [text_to_index[item.text] for item in items]
    return hidden[np.asarray(indices)]


def label_eta_squared(X: np.ndarray, labels: list[str]) -> float:
    X = np.asarray(X, dtype=np.float32)
    if X.ndim == 1:
        X = X[:, None]
    labels_arr = np.asarray(labels)
    unique_labels = sorted(set(labels_arr.tolist()))
    if len(unique_labels) < 2 or len(labels_arr) != X.shape[0]:
        return float("nan")

    grand = X.mean(axis=0, keepdims=True)
    total = float(np.sum((X - grand) ** 2))
    if total <= 0:
        return float("nan")

    between = 0.0
    for label in unique_labels:
        mask = labels_arr == label
        if not np.any(mask):
            continue
        mean = X[mask].mean(axis=0, keepdims=True)
        between += float(mask.sum() * np.sum((mean - grand) ** 2))
    return between / total


def has_repeated_groups(labels: list[str]) -> bool:
    counts: dict[str, int] = {}
    for label in labels:
        counts[label] = counts.get(label, 0) + 1
    return any(count > 1 for count in counts.values())


def vector_cosine_matrix(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    A_norm = np.linalg.norm(A, axis=1, keepdims=True)
    B_norm = np.linalg.norm(B, axis=1, keepdims=True)
    A_safe = A / np.maximum(A_norm, 1e-12)
    B_safe = B / np.maximum(B_norm, 1e-12)
    return A_safe @ B_safe.T


def mean_off_diagonal(matrix: np.ndarray) -> float:
    if matrix.shape[0] != matrix.shape[1] or matrix.shape[0] < 2:
        return float("nan")
    mask = ~np.eye(matrix.shape[0], dtype=bool)
    return float(matrix[mask].mean())


def centroid_by_label(X: np.ndarray, labels: list[str], ordered_labels: list[str]) -> np.ndarray:
    labels_arr = np.asarray(labels)
    centroids = []
    for label in ordered_labels:
        mask = labels_arr == label
        if not np.any(mask):
            raise ValueError(f"Missing centroid label: {label}")
        centroids.append(X[mask].mean(axis=0))
    return np.asarray(centroids, dtype=np.float32)


def train_probe_fast(X: np.ndarray, y: np.ndarray, train: np.ndarray, test: np.ndarray) -> float:
    clf = make_pipeline(
        StandardScaler(),
        LogisticRegression(max_iter=1200, C=1.0),
    )
    clf.fit(X[train], y[train])
    pred = clf.predict(X[test])
    return float(accuracy_score(y[test], pred))


def geometry_metrics_for_layer(X: np.ndarray) -> dict:
    X = X.astype(np.float32)
    centered = X - X.mean(axis=0, keepdims=True)
    singular_values = np.linalg.svd(centered, full_matrices=False, compute_uv=False)
    variance = singular_values**2
    total = float(variance.sum())
    rank = int(len(singular_values))

    if total <= 0:
        top_pc_ratio = 0.0
        edim90 = 0
        edim90_fraction = 0.0
        effective_rank = 0.0
        effective_rank_fraction = 0.0
        participation_ratio = 0.0
        participation_ratio_fraction = 0.0
    else:
        probs = variance / total
        cumulative = np.cumsum(probs)
        top_pc_ratio = float(probs[0])
        edim90 = int(np.searchsorted(cumulative, 0.9) + 1)
        edim90_fraction = float(edim90 / max(1, rank))
        entropy = float(-(probs[probs > 0] * np.log(probs[probs > 0])).sum())
        effective_rank = float(math.exp(entropy))
        effective_rank_fraction = float(effective_rank / max(1, rank))
        participation_ratio = float(total**2 / np.sum(variance**2))
        participation_ratio_fraction = float(participation_ratio / max(1, rank))

    norms = np.linalg.norm(X, axis=1)
    valid = norms > 0
    if int(valid.sum()) < 2:
        mean_pairwise_cosine = 0.0
    else:
        Xn = X[valid] / norms[valid, None]
        sims = Xn @ Xn.T
        n = sims.shape[0]
        mean_pairwise_cosine = float((sims.sum() - np.trace(sims)) / (n * (n - 1)))

    return {
        "rank": rank,
        "top_pc_variance_ratio": top_pc_ratio,
        "edim90_components": edim90,
        "edim90_fraction": edim90_fraction,
        "effective_rank": effective_rank,
        "effective_rank_fraction": effective_rank_fraction,
        "participation_ratio": participation_ratio,
        "participation_ratio_fraction": participation_ratio_fraction,
        "mean_pairwise_cosine": mean_pairwise_cosine,
        "max_abs_activation": float(np.max(np.abs(X))),
        "mean_abs_activation": float(np.mean(np.abs(X))),
        "std_activation": float(np.std(X)),
    }


def run_geometry_analysis(runs: list[RunInfo], out_dir: Path) -> list[dict]:
    rows = []
    for run in runs:
        print(f"[geometry] {run.run_id}")
        hidden, _texts = load_run_hidden(run)
        n_texts, n_layers, hidden_size = hidden.shape
        for layer in range(n_layers):
            row = {
                "run_id": run.run_id,
                "model": run.model_short,
                "surface": run.surface,
                "real_split": run.real_split,
                "n_texts": n_texts,
                "n_layers": n_layers,
                "hidden_size": hidden_size,
                "layer": layer,
                "normalized_depth": layer / (n_layers - 1) if n_layers > 1 else 0.0,
            }
            row.update(geometry_metrics_for_layer(hidden[:, layer, :]))
            rows.append(row)

    write_csv(
        out_dir / "geometry_metrics.csv",
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
            "top_pc_variance_ratio",
            "edim90_components",
            "edim90_fraction",
            "effective_rank",
            "effective_rank_fraction",
            "participation_ratio",
            "participation_ratio_fraction",
            "mean_pairwise_cosine",
            "max_abs_activation",
            "mean_abs_activation",
            "std_activation",
        ],
    )
    plot_geometry(rows, out_dir)
    return rows


def plot_geometry(rows: list[dict], out_dir: Path) -> None:
    metrics = [
        ("top_pc_variance_ratio", "Top PC variance ratio", "top_pc_variance_ratio_by_layer.png", 0, 1),
        ("edim90_fraction", "edim90 fraction of rank", "edim90_fraction_by_layer.png", 0, 1),
        ("effective_rank_fraction", "Effective rank fraction", "effective_rank_fraction_by_layer.png", 0, 1),
        ("mean_pairwise_cosine", "Mean pairwise cosine", "mean_pairwise_cosine_by_layer.png", None, None),
    ]
    for metric, title, filename, ymin, ymax in metrics:
        fig, axes = plt.subplots(1, 2, figsize=(14, 5), sharey=False)
        for ax, surface in zip(axes, ["base", "full"]):
            for model in ["Qwen3-1.7B", "Qwen3-8B", "Fanar-1-9B", "ALLaM-7B"]:
                series = [r for r in rows if r["surface"] == surface and r["model"] == model]
                if not series:
                    continue
                ax.plot(
                    [r["layer"] for r in series],
                    [r[metric] for r in series],
                    marker="o",
                    markersize=3,
                    linewidth=1.8,
                    color=COLORS[model],
                    label=model,
                )
            ax.set_title(surface)
            ax.set_xlabel("layer")
            ax.set_ylabel(title)
            ax.grid(alpha=0.25)
            if ymin is not None and ymax is not None:
                ax.set_ylim(ymin, ymax)
        handles, labels = axes[0].get_legend_handles_labels()
        fig.legend(handles, labels, loc="lower center", ncol=4, frameon=True)
        fig.suptitle(title)
        fig.tight_layout(rect=(0.0, 0.13, 1.0, 0.92))
        savefig(out_dir / filename)


def join_probe_geometry(runs: list[RunInfo], geometry_rows: list[dict], out_dir: Path) -> list[dict]:
    geometry_by_run_layer = {(row["run_id"], int(row["layer"])): row for row in geometry_rows}
    joined = []
    for run in runs:
        result_payload = read_json(run.run_dir / "results.json")
        for probe_name, probe_label in MAIN_PROBES:
            result = result_payload["results"][probe_name]
            for layer, acc, control, selectivity in zip(
                result["layer_indices"],
                result["accuracy_per_layer"],
                result["control_accuracy_per_layer"],
                result["selectivity_per_layer"],
            ):
                geom = geometry_by_run_layer[(run.run_id, int(layer))]
                joined.append(
                    {
                        "run_id": run.run_id,
                        "model": run.model_short,
                        "surface": run.surface,
                        "probe": probe_name,
                        "probe_label": probe_label,
                        "layer": int(layer),
                        "normalized_depth": geom["normalized_depth"],
                        "accuracy": float(acc),
                        "control_accuracy": float(control),
                        "selectivity": float(selectivity),
                        "ngram_accuracy": float(result["ngram_accuracy"]),
                        "top_pc_variance_ratio": geom["top_pc_variance_ratio"],
                        "edim90_fraction": geom["edim90_fraction"],
                        "effective_rank_fraction": geom["effective_rank_fraction"],
                        "mean_pairwise_cosine": geom["mean_pairwise_cosine"],
                    }
                )
    write_csv(
        out_dir / "probe_geometry_by_layer.csv",
        joined,
        [
            "run_id",
            "model",
            "surface",
            "probe",
            "probe_label",
            "layer",
            "normalized_depth",
            "accuracy",
            "control_accuracy",
            "selectivity",
            "ngram_accuracy",
            "top_pc_variance_ratio",
            "edim90_fraction",
            "effective_rank_fraction",
            "mean_pairwise_cosine",
        ],
    )
    plot_probe_geometry(joined, out_dir)
    return joined


def plot_probe_geometry(rows: list[dict], out_dir: Path) -> None:
    for surface in ["base", "full"]:
        fig, axes = plt.subplots(4, 4, figsize=(18, 14), sharex=False)
        for row_idx, model in enumerate(["Qwen3-1.7B", "Qwen3-8B", "Fanar-1-9B", "ALLaM-7B"]):
            for col_idx, (probe, probe_label) in enumerate(MAIN_PROBES):
                ax = axes[row_idx][col_idx]
                series = [r for r in rows if r["surface"] == surface and r["model"] == model and r["probe"] == probe]
                ax.plot(
                    [r["layer"] for r in series],
                    [r["accuracy"] for r in series],
                    color="#1f77b4",
                    marker="o",
                    markersize=2.5,
                    linewidth=1.5,
                )
                if series:
                    ax.axhline(series[0]["ngram_accuracy"], color="#1f77b4", linestyle=":", linewidth=1.1)
                ax.set_ylim(0, 1.05)
                ax.grid(alpha=0.25)
                ax.set_xlabel("layer")
                if col_idx == 0:
                    ax.set_ylabel(f"{model}\naccuracy")
                if row_idx == 0:
                    ax.set_title(probe_label)
                twin = ax.twinx()
                twin.plot(
                    [r["layer"] for r in series],
                    [r["top_pc_variance_ratio"] for r in series],
                    color="#d62728",
                    linestyle="--",
                    linewidth=1.2,
                )
                twin.set_ylim(0, 1)
                if col_idx == 3:
                    twin.set_ylabel("top PC ratio")
                else:
                    twin.set_yticklabels([])
        fig.suptitle(f"{surface}: probe accuracy vs top-PC anisotropy")
        handles = [
            plt.Line2D([0], [0], color="#1f77b4", marker="o", linewidth=1.5, label="probe accuracy"),
            plt.Line2D([0], [0], color="#1f77b4", linestyle=":", linewidth=1.1, label="n-gram baseline"),
            plt.Line2D([0], [0], color="#d62728", linestyle="--", linewidth=1.2, label="top PC variance ratio"),
        ]
        fig.legend(handles=handles, loc="lower center", ncol=3, frameon=True)
        fig.tight_layout(rect=(0.0, 0.06, 1.0, 0.96))
        savefig(out_dir / f"{surface}_probe_top_pc_overlay.png")


def compute_top_pcs(hidden: np.ndarray, max_k: int) -> tuple[list[np.ndarray], list[np.ndarray]]:
    means = []
    pcs = []
    n_texts, n_layers, hidden_size = hidden.shape
    n_components = min(max_k, n_texts - 1, hidden_size)
    for layer in range(n_layers):
        X = hidden[:, layer, :].astype(np.float32)
        mean = X.mean(axis=0, keepdims=True)
        centered = X - mean
        if n_components > 0:
            _u, _s, vt = randomized_svd(centered, n_components=n_components, n_iter=5, random_state=layer)
        else:
            vt = np.empty((0, hidden_size), dtype=np.float32)
        means.append(mean.astype(np.float32))
        pcs.append(vt.astype(np.float32))
    return means, pcs


def remove_top_pcs(X: np.ndarray, mean: np.ndarray, vt: np.ndarray, k: int) -> np.ndarray:
    if k <= 0:
        return X.astype(np.float32)
    V = vt[:k]
    centered = X.astype(np.float32) - mean
    return X.astype(np.float32) - (centered @ V.T) @ V


def run_pc_removal_analysis(runs: list[RunInfo], data_path: Path, out_dir: Path) -> list[dict]:
    rows = []
    for run in runs:
        print(f"[pc-removal] {run.run_id}")
        hidden, texts = load_run_hidden(run)
        text_to_index = {text: idx for idx, text in enumerate(texts)}
        specs = build_template_probe_specs(data_path, run.surface, run.real_split)
        means, pcs = compute_top_pcs(hidden, max(PC_K_VALUES))

        for spec in specs:
            X_probe = hidden_for_items(hidden, text_to_index, spec.items)
            y_arr = np.asarray(spec.y)
            for k in PC_K_VALUES:
                layer_scores = []
                for layer in range(X_probe.shape[1]):
                    X_layer = remove_top_pcs(X_probe[:, layer, :], means[layer], pcs[layer], k)
                    score = train_probe_fast(X_layer, y_arr, spec.train, spec.test)
                    layer_scores.append(score)
                peak_layer = int(np.argmax(layer_scores))
                rows.append(
                    {
                        "run_id": run.run_id,
                        "model": run.model_short,
                        "surface": run.surface,
                        "real_split": run.real_split,
                        "probe": spec.name,
                        "probe_label": spec.label,
                        "removed_pcs": k,
                        "peak_accuracy": float(layer_scores[peak_layer]),
                        "peak_layer": peak_layer,
                        "mean_accuracy": float(np.mean(layer_scores)),
                        "early_accuracy": float(np.mean(layer_scores[: max(1, len(layer_scores) // 4)])),
                        "middle_accuracy": float(np.mean(layer_scores[len(layer_scores) // 4 : 3 * len(layer_scores) // 4])),
                        "late_accuracy": float(np.mean(layer_scores[3 * len(layer_scores) // 4 :])),
                        "accuracy_per_layer": " ".join(f"{value:.6f}" for value in layer_scores),
                    }
                )
                print(
                    f"  {spec.name} remove={k}: peak={layer_scores[peak_layer]:.3f} layer={peak_layer}"
                )

    write_csv(
        out_dir / "pc_removal_probe_summary.csv",
        rows,
        [
            "run_id",
            "model",
            "surface",
            "real_split",
            "probe",
            "probe_label",
            "removed_pcs",
            "peak_accuracy",
            "peak_layer",
            "mean_accuracy",
            "early_accuracy",
            "middle_accuracy",
            "late_accuracy",
            "accuracy_per_layer",
        ],
    )
    plot_pc_removal(rows, out_dir)
    return rows


def plot_pc_removal(rows: list[dict], out_dir: Path) -> None:
    for surface in ["base", "full"]:
        fig, axes = plt.subplots(2, 2, figsize=(12, 8), sharex=True, sharey=True)
        axes_flat = axes.ravel()
        for ax, (probe, probe_label) in zip(axes_flat, MAIN_PROBES):
            for model in ["Qwen3-1.7B", "Qwen3-8B", "Fanar-1-9B", "ALLaM-7B"]:
                series = [
                    r for r in rows if r["surface"] == surface and r["model"] == model and r["probe"] == probe
                ]
                series.sort(key=lambda r: int(r["removed_pcs"]))
                if not series:
                    continue
                ax.plot(
                    [r["removed_pcs"] for r in series],
                    [r["peak_accuracy"] for r in series],
                    color=COLORS[model],
                    marker="o",
                    linewidth=1.8,
                    label=model,
                )
            ax.set_title(probe_label)
            ax.set_xlabel("removed top PCs")
            ax.set_ylabel("peak accuracy")
            ax.set_ylim(0, 1.05)
            ax.grid(alpha=0.25)
        handles, labels = axes_flat[0].get_legend_handles_labels()
        fig.legend(handles, labels, loc="lower center", ncol=4, frameon=True)
        fig.suptitle(f"{surface}: PC-removal robustness")
        fig.tight_layout(rect=(0.0, 0.10, 1.0, 0.94))
        savefig(out_dir / f"{surface}_pc_removal_peak_accuracy.png")

    for surface in ["base", "full"]:
        fig, axes = plt.subplots(4, 4, figsize=(18, 13), sharex=False, sharey=True)
        for row_idx, model in enumerate(["Qwen3-1.7B", "Qwen3-8B", "Fanar-1-9B", "ALLaM-7B"]):
            for col_idx, (probe, probe_label) in enumerate(MAIN_PROBES):
                ax = axes[row_idx][col_idx]
                for k, linestyle in [(0, "-"), (1, "--"), (5, ":"), (10, "-.")]:
                    series = [
                        r
                        for r in rows
                        if r["surface"] == surface
                        and r["model"] == model
                        and r["probe"] == probe
                        and int(r["removed_pcs"]) == k
                    ]
                    if not series:
                        continue
                    values = [float(v) for v in series[0]["accuracy_per_layer"].split()]
                    ax.plot(range(len(values)), values, linestyle=linestyle, linewidth=1.4, label=f"remove {k}")
                ax.set_ylim(0, 1.05)
                ax.grid(alpha=0.25)
                ax.set_xlabel("layer")
                if col_idx == 0:
                    ax.set_ylabel(f"{model}\naccuracy")
                if row_idx == 0:
                    ax.set_title(probe_label)
        handles, labels = axes[0][0].get_legend_handles_labels()
        fig.legend(handles, labels, loc="lower center", ncol=4, frameon=True)
        fig.suptitle(f"{surface}: layer curves after PC removal")
        fig.tight_layout(rect=(0.0, 0.07, 1.0, 0.96))
        savefig(out_dir / f"{surface}_pc_removal_layer_curves.png")


def run_variance_decomposition(runs: list[RunInfo], data_path: Path, out_dir: Path) -> tuple[list[dict], list[dict]]:
    payload = load_productivity_dataset(data_path)
    variance_rows = []
    top_pc_rows = []

    for run in runs:
        print(f"[variance] {run.run_id}")
        hidden, texts = load_run_hidden(run)
        text_to_index = {text: idx for idx, text in enumerate(texts)}
        tokenization = read_json(run.run_dir / "tokenization_diagnostics.json")
        token_count_by_text = {item["text"]: int(item["n_tokens"]) for item in tokenization["items"]}

        real = make_items(payload, "real", run.surface)
        nonce = make_items(payload, "nonce", "base")
        real_overlap, nonce_overlap = overlap_by_label(real, nonce)
        overlap = real_overlap + nonce_overlap
        all_items = real + nonce

        X_overlap = hidden_for_items(hidden, text_to_index, overlap)
        X_real = hidden_for_items(hidden, text_to_index, real)
        X_all = hidden_for_items(hidden, text_to_index, all_items)

        overlap_template = [item.template for item in overlap]
        overlap_source = [item.source for item in overlap]
        real_template = [item.template for item in real]
        real_root = [item.root for item in real]
        real_family = [family_key(item) for item in real]
        real_affix = ["affixed" if item.has_affix else "base" for item in real]
        all_source = [item.source for item in all_items]
        all_template = [item.template for item in all_items]
        all_token_count = np.asarray([token_count_by_text[item.text] for item in all_items], dtype=np.float32)

        for layer in range(hidden.shape[1]):
            row = {
                "run_id": run.run_id,
                "model": run.model_short,
                "surface": run.surface,
                "real_split": run.real_split,
                "layer": layer,
                "normalized_depth": layer / (hidden.shape[1] - 1) if hidden.shape[1] > 1 else 0.0,
                "overlap_template_eta2": label_eta_squared(X_overlap[:, layer, :], overlap_template),
                "overlap_source_eta2": label_eta_squared(X_overlap[:, layer, :], overlap_source),
                "real_template_eta2": label_eta_squared(X_real[:, layer, :], real_template),
                "real_root_eta2": label_eta_squared(X_real[:, layer, :], real_root),
                "real_family_eta2": label_eta_squared(X_real[:, layer, :], real_family)
                if has_repeated_groups(real_family)
                else float("nan"),
                "real_affix_eta2": label_eta_squared(X_real[:, layer, :], real_affix)
                if has_repeated_groups(real_affix)
                else float("nan"),
            }
            variance_rows.append(row)

            X_layer = X_all[:, layer, :].astype(np.float32)
            centered = X_layer - X_layer.mean(axis=0, keepdims=True)
            _u, _s, vt = randomized_svd(centered, n_components=1, n_iter=5, random_state=layer)
            pc1_scores = centered @ vt[0]
            if np.std(pc1_scores) > 0 and np.std(all_token_count) > 0:
                token_count_r2 = float(np.corrcoef(pc1_scores, all_token_count)[0, 1] ** 2)
            else:
                token_count_r2 = float("nan")
            top_pc_rows.append(
                {
                    "run_id": run.run_id,
                    "model": run.model_short,
                    "surface": run.surface,
                    "real_split": run.real_split,
                    "layer": layer,
                    "normalized_depth": layer / (hidden.shape[1] - 1) if hidden.shape[1] > 1 else 0.0,
                    "source_eta2_on_pc1": label_eta_squared(pc1_scores, all_source),
                    "template_eta2_on_pc1": label_eta_squared(pc1_scores, all_template),
                    "real_template_eta2_on_pc1": label_eta_squared(pc1_scores[: len(real)], real_template),
                    "real_affix_eta2_on_pc1": label_eta_squared(pc1_scores[: len(real)], real_affix)
                    if has_repeated_groups(real_affix)
                    else float("nan"),
                    "token_count_r2_on_pc1": token_count_r2,
                }
            )

    write_csv(
        out_dir / "variance_decomposition.csv",
        variance_rows,
        [
            "run_id",
            "model",
            "surface",
            "real_split",
            "layer",
            "normalized_depth",
            "overlap_template_eta2",
            "overlap_source_eta2",
            "real_template_eta2",
            "real_root_eta2",
            "real_family_eta2",
            "real_affix_eta2",
        ],
    )
    write_csv(
        out_dir / "top_pc_label_effects.csv",
        top_pc_rows,
        [
            "run_id",
            "model",
            "surface",
            "real_split",
            "layer",
            "normalized_depth",
            "source_eta2_on_pc1",
            "template_eta2_on_pc1",
            "real_template_eta2_on_pc1",
            "real_affix_eta2_on_pc1",
            "token_count_r2_on_pc1",
        ],
    )
    plot_variance_decomposition(variance_rows, top_pc_rows, out_dir)
    return variance_rows, top_pc_rows


def plot_variance_decomposition(variance_rows: list[dict], top_pc_rows: list[dict], out_dir: Path) -> None:
    variance_metrics = [
        ("overlap_template_eta2", "template eta2\n(real+nonce overlap)"),
        ("overlap_source_eta2", "source eta2\n(real vs nonce)"),
        ("real_template_eta2", "template eta2\n(real only)"),
        ("real_affix_eta2", "affix eta2\n(real only)"),
    ]
    for surface in ["base", "full"]:
        fig, axes = plt.subplots(2, 2, figsize=(13, 8), sharex=False, sharey=True)
        for ax, (metric, title) in zip(axes.ravel(), variance_metrics):
            for model in ["Qwen3-1.7B", "Qwen3-8B", "Fanar-1-9B", "ALLaM-7B"]:
                series = [r for r in variance_rows if r["surface"] == surface and r["model"] == model]
                if not series:
                    continue
                values = [float(r[metric]) for r in series]
                if all(np.isnan(values)):
                    continue
                ax.plot(
                    [r["layer"] for r in series],
                    values,
                    marker="o",
                    markersize=2.5,
                    linewidth=1.6,
                    color=COLORS[model],
                    label=model,
                )
            ax.set_title(title)
            ax.set_xlabel("layer")
            ax.set_ylabel("eta squared")
            ax.set_ylim(0, 1.02)
            ax.grid(alpha=0.25)
        handles, labels = axes[0][0].get_legend_handles_labels()
        fig.legend(handles, labels, loc="lower center", ncol=4, frameon=True)
        fig.suptitle(f"{surface}: variance explained by labels")
        fig.tight_layout(rect=(0.0, 0.11, 1.0, 0.93))
        savefig(out_dir / f"{surface}_variance_decomposition.png")

    pc_metrics = [
        ("source_eta2_on_pc1", "source eta2 on PC1"),
        ("template_eta2_on_pc1", "template eta2 on PC1"),
        ("token_count_r2_on_pc1", "token-count R2 on PC1"),
    ]
    for surface in ["base", "full"]:
        fig, axes = plt.subplots(1, 3, figsize=(15, 4.5), sharex=False, sharey=True)
        for ax, (metric, title) in zip(axes, pc_metrics):
            for model in ["Qwen3-1.7B", "Qwen3-8B", "Fanar-1-9B", "ALLaM-7B"]:
                series = [r for r in top_pc_rows if r["surface"] == surface and r["model"] == model]
                if not series:
                    continue
                ax.plot(
                    [r["layer"] for r in series],
                    [float(r[metric]) for r in series],
                    marker="o",
                    markersize=2.5,
                    linewidth=1.6,
                    color=COLORS[model],
                    label=model,
                )
            ax.set_title(title)
            ax.set_xlabel("layer")
            ax.set_ylabel("eta squared / R2")
            ax.set_ylim(0, 1.02)
            ax.grid(alpha=0.25)
        handles, labels = axes[0].get_legend_handles_labels()
        fig.legend(handles, labels, loc="lower center", ncol=4, frameon=True)
        fig.suptitle(f"{surface}: what the dominant PC tracks")
        fig.tight_layout(rect=(0.0, 0.18, 1.0, 0.90))
        savefig(out_dir / f"{surface}_top_pc_label_effects.png")


def run_centroid_alignment(runs: list[RunInfo], data_path: Path, out_dir: Path) -> list[dict]:
    payload = load_productivity_dataset(data_path)
    rows = []

    for run in runs:
        print(f"[alignment] {run.run_id}")
        hidden, texts = load_run_hidden(run)
        text_to_index = {text: idx for idx, text in enumerate(texts)}
        real = make_items(payload, "real", run.surface)
        nonce = make_items(payload, "nonce", "base")
        real_overlap, nonce_overlap = overlap_by_label(real, nonce)
        templates = sorted({item.template for item in real_overlap} & {item.template for item in nonce_overlap})
        X_real = hidden_for_items(hidden, text_to_index, real_overlap)
        X_nonce = hidden_for_items(hidden, text_to_index, nonce_overlap)
        real_labels = [item.template for item in real_overlap]
        nonce_labels = [item.template for item in nonce_overlap]

        for layer in range(hidden.shape[1]):
            real_layer = X_real[:, layer, :].astype(np.float32)
            nonce_layer = X_nonce[:, layer, :].astype(np.float32)
            combined_mean = np.vstack([real_layer, nonce_layer]).mean(axis=0, keepdims=True)

            real_centroids = centroid_by_label(real_layer, real_labels, templates)
            nonce_centroids = centroid_by_label(nonce_layer, nonce_labels, templates)
            raw_cos = vector_cosine_matrix(real_centroids, nonce_centroids)

            centered_real_centroids = centroid_by_label(real_layer - combined_mean, real_labels, templates)
            centered_nonce_centroids = centroid_by_label(nonce_layer - combined_mean, nonce_labels, templates)
            centered_cos = vector_cosine_matrix(centered_real_centroids, centered_nonce_centroids)

            eye = np.eye(len(templates), dtype=bool)
            real_to_nonce = float(np.mean(np.argmax(centered_cos, axis=1) == np.arange(len(templates))))
            nonce_to_real = float(np.mean(np.argmax(centered_cos, axis=0) == np.arange(len(templates))))
            rows.append(
                {
                    "run_id": run.run_id,
                    "model": run.model_short,
                    "surface": run.surface,
                    "real_split": run.real_split,
                    "layer": layer,
                    "normalized_depth": layer / (hidden.shape[1] - 1) if hidden.shape[1] > 1 else 0.0,
                    "n_templates": len(templates),
                    "raw_same_template_cos": float(raw_cos[eye].mean()),
                    "raw_other_template_cos": mean_off_diagonal(raw_cos),
                    "raw_alignment_margin": float(raw_cos[eye].mean() - mean_off_diagonal(raw_cos)),
                    "centered_same_template_cos": float(centered_cos[eye].mean()),
                    "centered_other_template_cos": mean_off_diagonal(centered_cos),
                    "centered_alignment_margin": float(centered_cos[eye].mean() - mean_off_diagonal(centered_cos)),
                    "nearest_template_accuracy": float((real_to_nonce + nonce_to_real) / 2),
                    "real_to_nonce_nearest_accuracy": real_to_nonce,
                    "nonce_to_real_nearest_accuracy": nonce_to_real,
                }
            )

    write_csv(
        out_dir / "template_centroid_alignment.csv",
        rows,
        [
            "run_id",
            "model",
            "surface",
            "real_split",
            "layer",
            "normalized_depth",
            "n_templates",
            "raw_same_template_cos",
            "raw_other_template_cos",
            "raw_alignment_margin",
            "centered_same_template_cos",
            "centered_other_template_cos",
            "centered_alignment_margin",
            "nearest_template_accuracy",
            "real_to_nonce_nearest_accuracy",
            "nonce_to_real_nearest_accuracy",
        ],
    )
    plot_centroid_alignment(rows, out_dir)
    return rows


def plot_centroid_alignment(rows: list[dict], out_dir: Path) -> None:
    metrics = [
        ("centered_alignment_margin", "centered same-vs-other margin"),
        ("nearest_template_accuracy", "nearest template accuracy"),
    ]
    for surface in ["base", "full"]:
        fig, axes = plt.subplots(1, 2, figsize=(13, 4.5), sharex=False)
        for ax, (metric, title) in zip(axes, metrics):
            for model in ["Qwen3-1.7B", "Qwen3-8B", "Fanar-1-9B", "ALLaM-7B"]:
                series = [r for r in rows if r["surface"] == surface and r["model"] == model]
                if not series:
                    continue
                ax.plot(
                    [r["layer"] for r in series],
                    [float(r[metric]) for r in series],
                    marker="o",
                    markersize=2.5,
                    linewidth=1.6,
                    color=COLORS[model],
                    label=model,
                )
            ax.set_title(title)
            ax.set_xlabel("layer")
            ax.grid(alpha=0.25)
            if metric.endswith("accuracy"):
                ax.set_ylim(0, 1.05)
            ax.set_ylabel(metric)
        handles, labels = axes[0].get_legend_handles_labels()
        fig.legend(handles, labels, loc="lower center", ncol=4, frameon=True)
        fig.suptitle(f"{surface}: real/nonce template-centroid alignment")
        fig.tight_layout(rect=(0.0, 0.18, 1.0, 0.90))
        savefig(out_dir / f"{surface}_template_centroid_alignment.png")


def run_affix_invariance(runs: list[RunInfo], data_path: Path, out_dir: Path) -> list[dict]:
    payload = load_productivity_dataset(data_path)
    rows = []

    for run in [run for run in runs if run.surface == "full"]:
        print(f"[affix] {run.run_id}")
        hidden, texts = load_run_hidden(run)
        text_to_index = {text: idx for idx, text in enumerate(texts)}
        real = make_items(payload, "real", "full")
        X_real = hidden_for_items(hidden, text_to_index, real)
        by_family: dict[str, dict[str, list[int] | int]] = {}
        for idx, item in enumerate(real):
            group = by_family.setdefault(family_key(item), {"base": [], "affixed": []})
            key = "affixed" if item.has_affix else "base"
            group[key].append(idx)  # type: ignore[index]

        valid_families = [
            family
            for family, members in by_family.items()
            if len(members["base"]) >= 1 and len(members["affixed"]) >= 1  # type: ignore[arg-type]
        ]
        affixed_indices = np.asarray([idx for idx, item in enumerate(real) if item.has_affix])
        affixed_templates = np.asarray([item.template for item in real if item.has_affix])

        for layer in range(hidden.shape[1]):
            X = X_real[:, layer, :].astype(np.float32)
            centered = X - X.mean(axis=0, keepdims=True)
            norms = np.linalg.norm(centered, axis=1, keepdims=True)
            Xn = centered / np.maximum(norms, 1e-12)

            within = []
            same_template_other_family = []
            different_template = []
            for family in valid_families:
                members = by_family[family]
                base_idx = int(members["base"][0])  # type: ignore[index]
                affix_list = [int(idx) for idx in members["affixed"]]  # type: ignore[union-attr]
                template = real[base_idx].template
                for affix_idx in affix_list:
                    within.append(float(Xn[base_idx] @ Xn[affix_idx]))

                other_same = [
                    int(idx)
                    for idx, affix_template in zip(affixed_indices, affixed_templates)
                    if affix_template == template and family_key(real[int(idx)]) != family
                ]
                other_diff = [
                    int(idx)
                    for idx, affix_template in zip(affixed_indices, affixed_templates)
                    if affix_template != template
                ]
                if other_same:
                    same_template_other_family.append(float(np.mean(Xn[base_idx] @ Xn[np.asarray(other_same)].T)))
                if other_diff:
                    different_template.append(float(np.mean(Xn[base_idx] @ Xn[np.asarray(other_diff)].T)))

            within_mean = float(np.mean(within))
            same_template_mean = float(np.mean(same_template_other_family))
            different_template_mean = float(np.mean(different_template))
            rows.append(
                {
                    "run_id": run.run_id,
                    "model": run.model_short,
                    "surface": run.surface,
                    "real_split": run.real_split,
                    "layer": layer,
                    "normalized_depth": layer / (hidden.shape[1] - 1) if hidden.shape[1] > 1 else 0.0,
                    "n_families": len(valid_families),
                    "within_family_base_affix_cos": within_mean,
                    "same_template_other_family_cos": same_template_mean,
                    "different_template_cos": different_template_mean,
                    "family_margin_vs_same_template": within_mean - same_template_mean,
                    "family_margin_vs_different_template": within_mean - different_template_mean,
                    "template_margin_inside_affix": same_template_mean - different_template_mean,
                }
            )

    write_csv(
        out_dir / "affix_invariance.csv",
        rows,
        [
            "run_id",
            "model",
            "surface",
            "real_split",
            "layer",
            "normalized_depth",
            "n_families",
            "within_family_base_affix_cos",
            "same_template_other_family_cos",
            "different_template_cos",
            "family_margin_vs_same_template",
            "family_margin_vs_different_template",
            "template_margin_inside_affix",
        ],
    )
    plot_affix_invariance(rows, out_dir)
    return rows


def plot_affix_invariance(rows: list[dict], out_dir: Path) -> None:
    metrics = [
        ("within_family_base_affix_cos", "base-affix cosine within family"),
        ("family_margin_vs_same_template", "family margin vs same template"),
        ("template_margin_inside_affix", "same-template margin over different template"),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.5), sharex=False)
    for ax, (metric, title) in zip(axes, metrics):
        for model in ["Qwen3-1.7B", "Qwen3-8B", "Fanar-1-9B", "ALLaM-7B"]:
            series = [r for r in rows if r["model"] == model]
            if not series:
                continue
            ax.plot(
                [r["layer"] for r in series],
                [float(r[metric]) for r in series],
                marker="o",
                markersize=2.5,
                linewidth=1.6,
                color=COLORS[model],
                label=model,
            )
        ax.set_title(title)
        ax.set_xlabel("layer")
        ax.set_ylabel(metric)
        ax.grid(alpha=0.25)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=4, frameon=True)
    fig.suptitle("full surface: affix invariance and template structure")
    fig.tight_layout(rect=(0.0, 0.18, 1.0, 0.90))
    savefig(out_dir / "affix_invariance_by_layer.png")


def run_layer_concordance(
    runs: list[RunInfo],
    probe_rows: list[dict],
    variance_rows: list[dict],
    top_pc_rows: list[dict],
    alignment_rows: list[dict],
    out_dir: Path,
) -> tuple[list[dict], list[dict]]:
    rows = []
    best_rows = []
    variance_by_key = {(r["run_id"], int(r["layer"])): r for r in variance_rows}
    top_pc_by_key = {(r["run_id"], int(r["layer"])): r for r in top_pc_rows}
    alignment_by_key = {(r["run_id"], int(r["layer"])): r for r in alignment_rows}
    probe_by_key = {(r["run_id"], r["probe"], int(r["layer"])): r for r in probe_rows}

    for run in runs:
        layers = sorted({int(r["layer"]) for r in alignment_rows if r["run_id"] == run.run_id})
        for layer in layers:
            key = (run.run_id, layer)
            real_to_nonce = probe_by_key[(run.run_id, "train_real_test_nonce_overlap", layer)]
            nonce_to_real = probe_by_key[(run.run_id, "train_nonce_test_real_overlap", layer)]
            real_templates = probe_by_key[(run.run_id, "real_templates_random", layer)]
            nonce_heldout = probe_by_key[(run.run_id, "nonce_templates_heldout_roots", layer)]
            variance = variance_by_key[key]
            top_pc = top_pc_by_key[key]
            alignment = alignment_by_key[key]
            transfer_mean = (float(real_to_nonce["accuracy"]) + float(nonce_to_real["accuracy"])) / 2
            balanced_score = (
                transfer_mean
                + float(alignment["nearest_template_accuracy"])
                + float(alignment["centered_alignment_margin"])
                - float(variance["overlap_source_eta2"])
                - 0.25 * float(top_pc["token_count_r2_on_pc1"])
            )
            rows.append(
                {
                    "run_id": run.run_id,
                    "model": run.model_short,
                    "surface": run.surface,
                    "real_split": run.real_split,
                    "layer": layer,
                    "normalized_depth": layer / (len(layers) - 1) if len(layers) > 1 else 0.0,
                    "real_template_accuracy": real_templates["accuracy"],
                    "nonce_heldout_accuracy": nonce_heldout["accuracy"],
                    "real_to_nonce_accuracy": real_to_nonce["accuracy"],
                    "nonce_to_real_accuracy": nonce_to_real["accuracy"],
                    "transfer_mean_accuracy": transfer_mean,
                    "centroid_nearest_accuracy": alignment["nearest_template_accuracy"],
                    "centroid_alignment_margin": alignment["centered_alignment_margin"],
                    "overlap_template_eta2": variance["overlap_template_eta2"],
                    "overlap_source_eta2": variance["overlap_source_eta2"],
                    "source_eta2_on_pc1": top_pc["source_eta2_on_pc1"],
                    "token_count_r2_on_pc1": top_pc["token_count_r2_on_pc1"],
                    "balanced_layer_score": balanced_score,
                }
            )

    for run in runs:
        run_rows = [r for r in rows if r["run_id"] == run.run_id]
        if not run_rows:
            continue
        for criterion, field in [
            ("best_transfer", "transfer_mean_accuracy"),
            ("best_centroid_alignment", "centroid_alignment_margin"),
            ("best_balanced", "balanced_layer_score"),
        ]:
            best = max(run_rows, key=lambda r: float(r[field]))
            best_rows.append(
                {
                    "run_id": run.run_id,
                    "model": run.model_short,
                    "surface": run.surface,
                    "criterion": criterion,
                    "layer": best["layer"],
                    "real_template_accuracy": best["real_template_accuracy"],
                    "nonce_heldout_accuracy": best["nonce_heldout_accuracy"],
                    "real_to_nonce_accuracy": best["real_to_nonce_accuracy"],
                    "nonce_to_real_accuracy": best["nonce_to_real_accuracy"],
                    "transfer_mean_accuracy": best["transfer_mean_accuracy"],
                    "centroid_nearest_accuracy": best["centroid_nearest_accuracy"],
                    "centroid_alignment_margin": best["centroid_alignment_margin"],
                    "overlap_source_eta2": best["overlap_source_eta2"],
                    "token_count_r2_on_pc1": best["token_count_r2_on_pc1"],
                    "balanced_layer_score": best["balanced_layer_score"],
                }
            )

    fieldnames = [
        "run_id",
        "model",
        "surface",
        "real_split",
        "layer",
        "normalized_depth",
        "real_template_accuracy",
        "nonce_heldout_accuracy",
        "real_to_nonce_accuracy",
        "nonce_to_real_accuracy",
        "transfer_mean_accuracy",
        "centroid_nearest_accuracy",
        "centroid_alignment_margin",
        "overlap_template_eta2",
        "overlap_source_eta2",
        "source_eta2_on_pc1",
        "token_count_r2_on_pc1",
        "balanced_layer_score",
    ]
    write_csv(out_dir / "layer_concordance.csv", rows, fieldnames)
    write_csv(
        out_dir / "best_layers_by_run.csv",
        best_rows,
        [
            "run_id",
            "model",
            "surface",
            "criterion",
            "layer",
            "real_template_accuracy",
            "nonce_heldout_accuracy",
            "real_to_nonce_accuracy",
            "nonce_to_real_accuracy",
            "transfer_mean_accuracy",
            "centroid_nearest_accuracy",
            "centroid_alignment_margin",
            "overlap_source_eta2",
            "token_count_r2_on_pc1",
            "balanced_layer_score",
        ],
    )
    plot_layer_concordance(rows, out_dir)
    return rows, best_rows


def plot_layer_concordance(rows: list[dict], out_dir: Path) -> None:
    for surface in ["base", "full"]:
        fig, axes = plt.subplots(4, 1, figsize=(12, 12), sharex=False, sharey=True)
        for ax, model in zip(axes, ["Qwen3-1.7B", "Qwen3-8B", "Fanar-1-9B", "ALLaM-7B"]):
            series = [r for r in rows if r["surface"] == surface and r["model"] == model]
            if not series:
                continue
            layers = [int(r["layer"]) for r in series]
            ax.plot(
                layers,
                [float(r["transfer_mean_accuracy"]) for r in series],
                color="#1f77b4",
                marker="o",
                markersize=2.5,
                linewidth=1.5,
                label="transfer mean",
            )
            ax.plot(
                layers,
                [float(r["centroid_nearest_accuracy"]) for r in series],
                color="#2ca02c",
                marker="o",
                markersize=2.5,
                linewidth=1.5,
                label="centroid nearest",
            )
            ax.plot(
                layers,
                [float(r["overlap_source_eta2"]) for r in series],
                color="#d62728",
                linestyle="--",
                linewidth=1.3,
                label="source eta2",
            )
            ax.plot(
                layers,
                [float(r["token_count_r2_on_pc1"]) for r in series],
                color="#9467bd",
                linestyle=":",
                linewidth=1.3,
                label="token-count R2 on PC1",
            )
            ax.set_ylim(0, 1.05)
            ax.set_title(model)
            ax.set_xlabel("layer")
            ax.set_ylabel("value")
            ax.grid(alpha=0.25)
        handles, labels = axes[0].get_legend_handles_labels()
        fig.legend(handles, labels, loc="lower center", ncol=4, frameon=True)
        fig.suptitle(f"{surface}: transfer, centroid alignment, and nuisance structure")
        fig.tight_layout(rect=(0.0, 0.07, 1.0, 0.96))
        savefig(out_dir / f"{surface}_layer_concordance.png")


def write_initial_report(
    geometry_rows: list[dict],
    pc_rows: list[dict],
    variance_rows: list[dict],
    top_pc_rows: list[dict],
    alignment_rows: list[dict],
    affix_rows: list[dict],
    best_layer_rows: list[dict],
    out_path: Path,
) -> None:
    def summarize_geometry(surface: str) -> list[str]:
        lines = []
        for model in ["Qwen3-1.7B", "Qwen3-8B", "Fanar-1-9B", "ALLaM-7B"]:
            rows = [r for r in geometry_rows if r["surface"] == surface and r["model"] == model]
            if not rows:
                continue
            max_top = max(r["top_pc_variance_ratio"] for r in rows)
            min_edim = min(r["edim90_fraction"] for r in rows)
            mean_edim = sum(r["edim90_fraction"] for r in rows) / len(rows)
            collapsed = sum(1 for r in rows if r["edim90_fraction"] <= 0.02)
            lines.append(
                f"| {model} | {max_top:.3f} | {min_edim:.3f} | {mean_edim:.3f} | {collapsed} |"
            )
        return lines

    def summarize_pc(surface: str, probe: str) -> list[str]:
        lines = []
        for model in ["Qwen3-1.7B", "Qwen3-8B", "Fanar-1-9B", "ALLaM-7B"]:
            rows = [
                r for r in pc_rows if r["surface"] == surface and r["model"] == model and r["probe"] == probe
            ]
            by_k = {int(r["removed_pcs"]): float(r["peak_accuracy"]) for r in rows}
            if not by_k:
                continue
            lines.append(
                f"| {model} | {by_k.get(0, float('nan')):.3f} | {by_k.get(1, float('nan')):.3f} | "
                f"{by_k.get(5, float('nan')):.3f} | {by_k.get(10, float('nan')):.3f} | "
                f"{by_k.get(10, 0.0) - by_k.get(0, 0.0):+.3f} |"
            )
        return lines

    def fmt(value: float) -> str:
        return "nan" if math.isnan(float(value)) else f"{float(value):.3f}"

    def summarize_variance(surface: str) -> list[str]:
        lines = []
        for model in ["Qwen3-1.7B", "Qwen3-8B", "Fanar-1-9B", "ALLaM-7B"]:
            rows = [r for r in variance_rows if r["surface"] == surface and r["model"] == model]
            pc_model_rows = [r for r in top_pc_rows if r["surface"] == surface and r["model"] == model]
            if not rows or not pc_model_rows:
                continue
            affix_values = [float(r["real_affix_eta2"]) for r in rows if not math.isnan(float(r["real_affix_eta2"]))]
            lines.append(
                "| "
                + " | ".join(
                    [
                        model,
                        fmt(max(float(r["overlap_template_eta2"]) for r in rows)),
                        fmt(max(float(r["overlap_source_eta2"]) for r in rows)),
                        fmt(max(float(r["real_template_eta2"]) for r in rows)),
                        fmt(max(affix_values) if affix_values else float("nan")),
                        fmt(max(float(r["source_eta2_on_pc1"]) for r in pc_model_rows)),
                        fmt(max(float(r["token_count_r2_on_pc1"]) for r in pc_model_rows)),
                    ]
                )
                + " |"
            )
        return lines

    def summarize_alignment(surface: str) -> list[str]:
        lines = []
        for model in ["Qwen3-1.7B", "Qwen3-8B", "Fanar-1-9B", "ALLaM-7B"]:
            rows = [r for r in alignment_rows if r["surface"] == surface and r["model"] == model]
            if not rows:
                continue
            best_margin = max(rows, key=lambda r: float(r["centered_alignment_margin"]))
            best_nearest = max(rows, key=lambda r: float(r["nearest_template_accuracy"]))
            lines.append(
                f"| {model} | {float(best_margin['centered_alignment_margin']):.3f} | "
                f"{int(best_margin['layer'])} | {float(best_nearest['nearest_template_accuracy']):.3f} | "
                f"{int(best_nearest['layer'])} |"
            )
        return lines

    def summarize_affix() -> list[str]:
        lines = []
        for model in ["Qwen3-1.7B", "Qwen3-8B", "Fanar-1-9B", "ALLaM-7B"]:
            rows = [r for r in affix_rows if r["model"] == model]
            if not rows:
                continue
            best_family = max(rows, key=lambda r: float(r["family_margin_vs_same_template"]))
            best_template = max(rows, key=lambda r: float(r["template_margin_inside_affix"]))
            lines.append(
                f"| {model} | {float(best_family['within_family_base_affix_cos']):.3f} | "
                f"{float(best_family['family_margin_vs_same_template']):.3f} | {int(best_family['layer'])} | "
                f"{float(best_template['template_margin_inside_affix']):.3f} | {int(best_template['layer'])} |"
            )
        return lines

    def summarize_best_balanced(surface: str) -> list[str]:
        lines = []
        for model in ["Qwen3-1.7B", "Qwen3-8B", "Fanar-1-9B", "ALLaM-7B"]:
            rows = [
                r
                for r in best_layer_rows
                if r["surface"] == surface and r["model"] == model and r["criterion"] == "best_balanced"
            ]
            if not rows:
                continue
            row = rows[0]
            lines.append(
                f"| {model} | {int(row['layer'])} | {float(row['transfer_mean_accuracy']):.3f} | "
                f"{float(row['centroid_nearest_accuracy']):.3f} | "
                f"{float(row['centroid_alignment_margin']):.3f} | "
                f"{float(row['overlap_source_eta2']):.3f} | "
                f"{float(row['token_count_r2_on_pc1']):.3f} |"
            )
        return lines

    lines = [
        "# Representation Analysis Conclusions",
        "",
        "This report is generated from saved pooled hidden states in `results/REP01_*`.",
        "",
        "## Experiment 00: Layer-Wise Anisotropy",
        "",
        "The explicit anisotropy analysis is in `00_anisotropy/ANISOTROPY.md`. The main question is whether hidden states are spread across many directions or collapse into a few dominant directions.",
        "",
        "The headline result is sharp: Qwen3-1.7B, Qwen3-8B, and ALLaM have many collapsed layers, while Fanar has none under the current threshold. This is why Fanar's cosine and centroid geometry is easier to interpret, and why Qwen/ALLaM probe results need PC-removal and nuisance checks.",
        "",
        "## Experiment 01: Geometry Metrics",
        "",
        "Metrics:",
        "",
        "- `top_pc_variance_ratio`: fraction of variance explained by the first principal component.",
        "- `edim90_fraction`: fraction of available PCA rank needed to explain 90% variance.",
        "- `effective_rank_fraction`: entropy-based effective rank divided by rank.",
        "- `mean_pairwise_cosine`: average cosine similarity across word vectors.",
        "",
        "### Base Geometry Summary",
        "",
        "| Model | Max top-PC ratio | Min edim90 fraction | Mean edim90 fraction | Layers edim90 <= 2% |",
        "|---|---:|---:|---:|---:|",
        *summarize_geometry("base"),
        "",
        "### Full Geometry Summary",
        "",
        "| Model | Max top-PC ratio | Min edim90 fraction | Mean edim90 fraction | Layers edim90 <= 2% |",
        "|---|---:|---:|---:|---:|",
        *summarize_geometry("full"),
        "",
        "## Experiment 02: Probe-Geometry Overlay",
        "",
        "This joins the original layer-wise probe curves with anisotropy metrics. It is mainly a visual diagnostic: high probe accuracy should be read together with the layer's geometry, because a classifier can exploit dominant directions that may also encode token count or source/domain structure.",
        "",
        "## Experiment 03: PC-Removal Robustness",
        "",
        "The key test is whether peak template-probe accuracy survives after removing dominant PCA directions.",
        "",
        "### Base: Real Templates",
        "",
        "| Model | raw | remove 1 | remove 5 | remove 10 | remove10 - raw |",
        "|---|---:|---:|---:|---:|---:|",
        *summarize_pc("base", "real_templates_random"),
        "",
        "### Base: Nonce Held-Out Roots",
        "",
        "| Model | raw | remove 1 | remove 5 | remove 10 | remove10 - raw |",
        "|---|---:|---:|---:|---:|---:|",
        *summarize_pc("base", "nonce_templates_heldout_roots"),
        "",
        "### Full: Real Templates",
        "",
        "| Model | raw | remove 1 | remove 5 | remove 10 | remove10 - raw |",
        "|---|---:|---:|---:|---:|---:|",
        *summarize_pc("full", "real_templates_random"),
        "",
        "### Full: Nonce -> Real",
        "",
        "| Model | raw | remove 1 | remove 5 | remove 10 | remove10 - raw |",
        "|---|---:|---:|---:|---:|---:|",
        *summarize_pc("full", "train_nonce_test_real_overlap"),
        "",
        "## Experiment 04: Variance Decomposition",
        "",
        "This asks a simpler question than probing: how much of the raw representation variance is organized by template, by real-vs-nonce source, by affix status, and by token count.",
        "",
        "### Base",
        "",
        "| Model | max overlap-template eta2 | max source eta2 | max real-template eta2 | max affix eta2 | max source eta2 on PC1 | max token-count R2 on PC1 |",
        "|---|---:|---:|---:|---:|---:|---:|",
        *summarize_variance("base"),
        "",
        "### Full",
        "",
        "| Model | max overlap-template eta2 | max source eta2 | max real-template eta2 | max affix eta2 | max source eta2 on PC1 | max token-count R2 on PC1 |",
        "|---|---:|---:|---:|---:|---:|---:|",
        *summarize_variance("full"),
        "",
        "## Experiment 05: Real/Nonce Template-Centroid Alignment",
        "",
        "This avoids fitting a classifier. For each shared template, it compares the real-template centroid with the nonce-template centroid. A high nearest-template score means the geometry itself aligns real and nonce templates.",
        "",
        "### Base",
        "",
        "| Model | best centered margin | layer | best nearest-template accuracy | layer |",
        "|---|---:|---:|---:|---:|",
        *summarize_alignment("base"),
        "",
        "### Full",
        "",
        "| Model | best centered margin | layer | best nearest-template accuracy | layer |",
        "|---|---:|---:|---:|---:|",
        *summarize_alignment("full"),
        "",
        "## Experiment 06: Affix Invariance",
        "",
        "This uses only full-surface real words. It checks whether a base word is closer to its own affixed variants than to other affixed words with the same template.",
        "",
        "| Model | within-family cosine at best family layer | best family margin | layer | best template margin among affixed forms | layer |",
        "|---|---:|---:|---:|---:|---:|",
        *summarize_affix(),
        "",
        "## Experiment 07: Layer Concordance",
        "",
        "This joins the probe curves, centroid alignment, and nuisance/domain metrics layer by layer. The `best balanced` layer is a triage heuristic, not a statistical test: it rewards transfer and centroid alignment while penalizing real-vs-nonce source separation and token-count dominance.",
        "",
        "### Base",
        "",
        "| Model | layer | transfer mean | centroid nearest | centroid margin | source eta2 | token-count R2 on PC1 |",
        "|---|---:|---:|---:|---:|---:|---:|",
        *summarize_best_balanced("base"),
        "",
        "### Full",
        "",
        "| Model | layer | transfer mean | centroid nearest | centroid margin | source eta2 | token-count R2 on PC1 |",
        "|---|---:|---:|---:|---:|---:|---:|",
        *summarize_best_balanced("full"),
        "",
        "## Scientific Read",
        "",
        "The representation evidence is not just another probe result. It separates three effects: morphology signal, real-vs-nonce/domain separation, and global representation geometry.",
        "",
        "1. Qwen and ALLaM have severe dominant-direction geometry, while Fanar is much broader. This makes raw cosine and raw PCA plots dangerous unless centered or stress-tested.",
        "2. Template probing survives on nonce held-out roots even after removing top PCs. That supports a surface/template-shape interpretation for nonce, not yet a strong claim about abstract morphology.",
        "3. Real and transfer probes often lose accuracy after removing top PCs. This does not mean the result is fake; it means useful template information is partly carried by high-variance directions.",
        "4. ALLaM is the exception: removing a small number of PCs can improve real/nonce transfer. Its dominant directions look more like nuisance/domain structure than useful morphology structure.",
        "5. Qwen3-8B and Fanar have the cleanest real/nonce template alignment. Their centroid-nearest scores reach 0.9-1.0, which means the geometry itself often maps real and nonce examples of the same template together without training a classifier.",
        "6. ALLaM remains the weak case. It can probe template labels, but the centroid alignment is poor and source/token-count effects are large. I would not use ALLaM as evidence for abstract template representations yet.",
        "7. Affixation does not destroy family identity: base forms are closer to their own affixed variants than to other forms. However, this mostly says lexical-family information survives affixation; it is not by itself proof of template abstraction.",
        "",
        "## Files",
        "",
        "- `00_anisotropy/ANISOTROPY.md`",
        "- `00_anisotropy/anisotropy_summary.csv`",
        "- `00_anisotropy/anisotropy_dashboard.png`",
        "- `01_geometry/geometry_metrics.csv`",
        "- `02_probe_geometry/probe_geometry_by_layer.csv`",
        "- `03_pc_removal/pc_removal_probe_summary.csv`",
        "- `04_variance_decomposition/variance_decomposition.csv`",
        "- `04_variance_decomposition/top_pc_label_effects.csv`",
        "- `05_centroid_alignment/template_centroid_alignment.csv`",
        "- `06_affix_invariance/affix_invariance.csv`",
        "- `07_layer_concordance/layer_concordance.csv`",
        "- `07_layer_concordance/best_layers_by_run.csv`",
        "",
    ]
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=ROOT)
    parser.add_argument("--results-dir", type=Path, default=ROOT / "results")
    parser.add_argument("--data", type=Path, default=ROOT / "data/productivity_dataset.json")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "rep_analysis/results")
    args = parser.parse_args()

    runs = [RunInfo(run_id, model, surface, real_split, args.results_dir) for run_id, model, surface, real_split in RUNS]
    for run in runs:
        if not (run.run_dir / "hidden_representations.npz").exists():
            raise SystemExit(f"Missing representations: {run.run_dir / 'hidden_representations.npz'}")

    geometry_rows = run_geometry_analysis(runs, args.out_dir / "01_geometry")
    probe_rows = join_probe_geometry(runs, geometry_rows, args.out_dir / "02_probe_geometry")
    pc_rows = run_pc_removal_analysis(runs, args.data, args.out_dir / "03_pc_removal")
    variance_rows, top_pc_rows = run_variance_decomposition(runs, args.data, args.out_dir / "04_variance_decomposition")
    alignment_rows = run_centroid_alignment(runs, args.data, args.out_dir / "05_centroid_alignment")
    affix_rows = run_affix_invariance(runs, args.data, args.out_dir / "06_affix_invariance")
    _concordance_rows, best_layer_rows = run_layer_concordance(
        runs,
        probe_rows,
        variance_rows,
        top_pc_rows,
        alignment_rows,
        args.out_dir / "07_layer_concordance",
    )
    write_initial_report(
        geometry_rows,
        pc_rows,
        variance_rows,
        top_pc_rows,
        alignment_rows,
        affix_rows,
        best_layer_rows,
        args.out_dir / "CONCLUSIONS.md",
    )
    print(f"wrote {args.out_dir}")


if __name__ == "__main__":
    main()
