#!/usr/bin/env python3
"""Build cross-run tables and plots from saved probe results."""

from __future__ import annotations

import argparse
import csv
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


MAIN_RUNS = {"E03", "E05b", "E06", "E06b", "E07", "E07b", "E08", "E08b"}
BASE_MAIN_RUNS = ["E03", "E06", "E07", "E08"]
FULL_MAIN_RUNS = ["E05b", "E06b", "E07b", "E08b"]
POOLING_RUNS = ["E03", "E04a", "E04b"]

TEMPLATE_PROBES = [
    "real_templates_random",
    "nonce_templates_random",
    "nonce_templates_heldout_roots",
    "train_real_test_nonce_overlap",
    "train_nonce_test_real_overlap",
]

FULL_TEMPLATE_PROBES = [
    "real_templates_random",
    "train_real_test_nonce_overlap",
    "train_nonce_test_real_overlap",
]

PROBE_LABELS = {
    "real_templates_random": "real templates",
    "nonce_templates_random": "nonce templates",
    "nonce_templates_heldout_roots": "nonce held-out roots",
    "train_real_test_nonce_overlap": "real -> nonce",
    "train_nonce_test_real_overlap": "nonce -> real",
    "real_roots_random": "real roots",
    "nonce_roots_random": "nonce roots",
    "nonce_roots_heldout_templates": "nonce roots held-out templates",
}

MODEL_LABELS = {
    "Qwen/Qwen3-1.7B-Base": "Qwen3-1.7B",
    "Qwen/Qwen3-8B": "Qwen3-8B",
    "QCRI/Fanar-1-9B": "Fanar-1-9B",
    "humain-ai/ALLaM-7B-Instruct-preview": "ALLaM-7B",
}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def short_model_name(model: str) -> str:
    if model in MODEL_LABELS:
        return MODEL_LABELS[model]
    return model.rsplit("/", maxsplit=1)[-1]


def as_float(value) -> float | None:
    if value is None:
        return None
    return float(value)


def fmt(value, digits: int = 3) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return f"{float(value):.{digits}f}"


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    out = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        out.append("| " + " | ".join(row) + " |")
    return "\n".join(out)


def collect_runs(results_dir: Path) -> list[dict]:
    runs = []
    for result_path in sorted(results_dir.glob("*/results.json")):
        run_dir = result_path.parent
        payload = read_json(result_path)
        experiment = run_dir.name
        model = payload.get("model", "")
        real_split = payload.get("real_split") or "item"
        run = {
            "experiment": experiment,
            "run_dir": run_dir,
            "model": model,
            "model_short": short_model_name(model),
            "surface": payload.get("surface", ""),
            "pooling": payload.get("pooling", ""),
            "real_split": real_split,
            "data": payload.get("data", ""),
            "main_set": experiment in MAIN_RUNS,
            "results": payload.get("results", {}),
            "tokenization_summary": payload.get("tokenization_summary", {}),
            "representation_summary": payload.get("representation_summary", {}),
        }
        tok_path = run_dir / "tokenization_diagnostics.json"
        rep_path = run_dir / "representation_diagnostics.json"
        run["tokenization_diagnostics"] = read_json(tok_path) if tok_path.exists() else {}
        run["representation_diagnostics"] = read_json(rep_path) if rep_path.exists() else {}
        runs.append(run)
    return runs


def collect_metric_rows(runs: list[dict]) -> list[dict]:
    rows = []
    for run in runs:
        for probe, result in run["results"].items():
            ngram = as_float(result.get("ngram_accuracy"))
            peak = as_float(result.get("peak_accuracy"))
            group_split = result.get("group_split") or {}
            target = "root" if probe.startswith(("real_roots", "nonce_roots")) else "template"
            rows.append(
                {
                    "experiment": run["experiment"],
                    "main_set": "yes" if run["main_set"] else "no",
                    "model": run["model"],
                    "model_short": run["model_short"],
                    "surface": run["surface"],
                    "pooling": run["pooling"],
                    "real_split": run["real_split"],
                    "probe": probe,
                    "probe_label": PROBE_LABELS.get(probe, probe),
                    "target": target,
                    "split_kind": result.get("split_kind", ""),
                    "n_items": result.get("n_items", ""),
                    "train_size": result.get("train_size", ""),
                    "test_size": result.get("test_size", ""),
                    "group_overlap": group_split.get("group_overlap", ""),
                    "peak_layer": result.get("peak_layer", ""),
                    "peak_depth": result.get("peak_normalized_depth", ""),
                    "peak_accuracy": peak,
                    "peak_control_accuracy": as_float(result.get("peak_control_accuracy")),
                    "peak_selectivity": as_float(result.get("peak_selectivity")),
                    "ngram_accuracy": ngram,
                    "ngram_gap": None if peak is None or ngram is None else peak - ngram,
                    "chance": as_float(result.get("chance")),
                }
            )
    return rows


def collect_token_count_rows(runs: list[dict]) -> list[dict]:
    rows = []
    for run in runs:
        for probe, result in run["results"].items():
            for n_tokens, entry in (result.get("token_count_accuracy_at_peak") or {}).items():
                rows.append(
                    {
                        "experiment": run["experiment"],
                        "model_short": run["model_short"],
                        "surface": run["surface"],
                        "pooling": run["pooling"],
                        "real_split": run["real_split"],
                        "probe": probe,
                        "probe_label": PROBE_LABELS.get(probe, probe),
                        "n_tokens": n_tokens,
                        "n": entry.get("n", ""),
                        "accuracy": entry.get("accuracy", ""),
                    }
                )
    return rows


def collect_tokenization_rows(runs: list[dict]) -> list[dict]:
    rows = []
    for run in runs:
        summary = run["tokenization_summary"] or run["tokenization_diagnostics"]
        distribution = summary.get("token_count_distribution", {})
        one_token = int(distribution.get("1", 0))
        n_texts = int(summary.get("n_texts") or 0)
        rows.append(
            {
                "experiment": run["experiment"],
                "main_set": "yes" if run["main_set"] else "no",
                "model": run["model"],
                "model_short": run["model_short"],
                "surface": run["surface"],
                "pooling": run["pooling"],
                "real_split": run["real_split"],
                "n_texts": n_texts,
                "min_tokens": summary.get("min_tokens", ""),
                "max_tokens": summary.get("max_tokens", ""),
                "mean_tokens": summary.get("mean_tokens", ""),
                "median_tokens": summary.get("median_tokens", ""),
                "one_token_count": one_token,
                "one_token_fraction": one_token / n_texts if n_texts else "",
                "token_count_distribution": json.dumps(distribution, ensure_ascii=False, sort_keys=True),
            }
        )
    return rows


def collect_geometry_rows(runs: list[dict]) -> list[dict]:
    rows = []
    for run in runs:
        diag = run["representation_diagnostics"]
        layers = diag.get("layers", [])
        if not layers:
            continue
        edim90 = [
            (
                layer.get("layer"),
                layer.get("effective_dimensions", {}).get("0.9", {}).get("n_components"),
                layer.get("effective_dimensions", {}).get("0.9", {}).get("fraction_of_rank"),
            )
            for layer in layers
        ]
        edim90 = [item for item in edim90 if item[1] is not None]
        min_layer, min_components, min_fraction = min(edim90, key=lambda item: item[1])
        max_layer = max(layers, key=lambda layer: layer.get("max_abs_activation", 0.0))
        collapse_layers = [layer for layer, n_components, _ in edim90 if n_components <= 2]
        rows.append(
            {
                "experiment": run["experiment"],
                "main_set": "yes" if run["main_set"] else "no",
                "model": run["model"],
                "model_short": run["model_short"],
                "surface": run["surface"],
                "pooling": run["pooling"],
                "real_split": run["real_split"],
                "n_texts": diag.get("n_texts", ""),
                "n_layers": diag.get("n_layers", ""),
                "hidden_size": diag.get("hidden_size", ""),
                "max_abs_activation": max_layer.get("max_abs_activation", ""),
                "max_abs_layer": max_layer.get("layer", ""),
                "min_edim90_components": min_components,
                "min_edim90_fraction": min_fraction,
                "min_edim90_layer": min_layer,
                "collapse_layers_edim90_le_2": len(collapse_layers),
                "collapse_layer_indices": " ".join(str(layer) for layer in collapse_layers),
            }
        )
    return rows


def rows_by_experiment(rows: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for row in rows:
        grouped.setdefault(row["experiment"], []).append(row)
    return grouped


def metric_lookup(rows: list[dict]) -> dict[tuple[str, str], dict]:
    return {(row["experiment"], row["probe"]): row for row in rows}


def run_label(row: dict) -> str:
    split = row.get("real_split") or ""
    surface = row.get("surface") or ""
    return f"{row['model_short']}\n{surface}/{split}"


def plot_grouped_bars(
    path: Path,
    title: str,
    group_labels: list[str],
    series: list[tuple[str, list[float | None]]],
    ylabel: str = "Accuracy",
    y_min: float = 0.0,
    y_max: float | None = 1.05,
) -> None:
    fig_width = max(8, len(group_labels) * 1.6)
    fig, ax = plt.subplots(figsize=(fig_width, 4.8))
    total_width = 0.82
    bar_width = total_width / max(1, len(series))
    x_positions = list(range(len(group_labels)))
    for index, (label, values) in enumerate(series):
        offsets = [
            x - total_width / 2 + bar_width / 2 + index * bar_width for x in x_positions
        ]
        ax.bar(offsets, [0 if value is None else value for value in values], width=bar_width, label=label)
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.set_xticks(x_positions)
    ax.set_xticklabels(group_labels, rotation=20, ha="right")
    if y_max is not None:
        ax.set_ylim(y_min, y_max)
    else:
        ax.set_ylim(bottom=y_min)
    ax.grid(axis="y", alpha=0.25)
    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.22),
        ncol=min(3, max(1, len(series))),
        fontsize=9,
    )
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def plot_base_template_comparison(metrics: list[dict], out_dir: Path) -> None:
    lookup = metric_lookup(metrics)
    run_rows = [lookup[(run, "real_templates_random")] for run in BASE_MAIN_RUNS if (run, "real_templates_random") in lookup]
    group_labels = [row["model_short"] for row in run_rows]
    series = []
    for probe in TEMPLATE_PROBES:
        values = [lookup.get((row["experiment"], probe), {}).get("peak_accuracy") for row in run_rows]
        series.append((PROBE_LABELS[probe], values))
    plot_grouped_bars(
        out_dir / "base_template_comparison.png",
        "Base forms: template probe accuracy",
        group_labels,
        series,
    )


def plot_full_template_comparison(metrics: list[dict], out_dir: Path) -> None:
    lookup = metric_lookup(metrics)
    run_rows = [lookup[(run, "real_templates_random")] for run in FULL_MAIN_RUNS if (run, "real_templates_random") in lookup]
    group_labels = [row["model_short"] for row in run_rows]
    series = []
    for probe in FULL_TEMPLATE_PROBES:
        values = [lookup.get((row["experiment"], probe), {}).get("peak_accuracy") for row in run_rows]
        series.append((PROBE_LABELS[probe], values))
    plot_grouped_bars(
        out_dir / "full_family_comparison.png",
        "Full forms: family split template accuracy",
        group_labels,
        series,
    )


def plot_transfer_comparison(metrics: list[dict], out_dir: Path) -> None:
    lookup = metric_lookup(metrics)
    run_order = BASE_MAIN_RUNS + FULL_MAIN_RUNS
    rows = [lookup[(run, "train_real_test_nonce_overlap")] for run in run_order if (run, "train_real_test_nonce_overlap") in lookup]
    group_labels = [run_label(row) for row in rows]
    series = [
        (
            "real -> nonce",
            [lookup.get((row["experiment"], "train_real_test_nonce_overlap"), {}).get("peak_accuracy") for row in rows],
        ),
        (
            "nonce -> real",
            [lookup.get((row["experiment"], "train_nonce_test_real_overlap"), {}).get("peak_accuracy") for row in rows],
        ),
    ]
    plot_grouped_bars(
        out_dir / "transfer_comparison.png",
        "Template transfer accuracy",
        group_labels,
        series,
    )


def mean_for_run(metrics: list[dict], experiment: str, field: str, probes: list[str]) -> float | None:
    values = [
        row[field]
        for row in metrics
        if row["experiment"] == experiment and row["probe"] in probes and row.get(field) is not None
    ]
    if not values:
        return None
    return sum(values) / len(values)


def plot_gap_and_selectivity(metrics: list[dict], out_dir: Path) -> None:
    lookup = metric_lookup(metrics)
    run_order = BASE_MAIN_RUNS + FULL_MAIN_RUNS
    rows = [lookup[(run, "real_templates_random")] for run in run_order if (run, "real_templates_random") in lookup]
    group_labels = [run_label(row) for row in rows]
    gap_values = [mean_for_run(metrics, row["experiment"], "ngram_gap", TEMPLATE_PROBES) for row in rows]
    selectivity_values = [
        mean_for_run(metrics, row["experiment"], "peak_selectivity", TEMPLATE_PROBES) for row in rows
    ]
    plot_grouped_bars(
        out_dir / "ngram_gap_comparison.png",
        "Mean template advantage over character n-grams",
        group_labels,
        [("probe - n-gram", gap_values)],
        ylabel="Accuracy gap",
        y_min=-0.25,
        y_max=0.75,
    )
    plot_grouped_bars(
        out_dir / "selectivity_comparison.png",
        "Mean template selectivity",
        group_labels,
        [("probe - shuffled-label control", selectivity_values)],
        ylabel="Selectivity",
        y_min=0.0,
        y_max=1.05,
    )


def plot_tokenization(token_rows: list[dict], out_dir: Path) -> None:
    rows = [row for row in token_rows if row["experiment"] in MAIN_RUNS]
    rows.sort(key=lambda row: (BASE_MAIN_RUNS + FULL_MAIN_RUNS).index(row["experiment"]))
    labels = [f"{row['model_short']}\n{row['surface']}" for row in rows]
    series = [
        ("mean tokens", [float(row["mean_tokens"]) for row in rows]),
        ("one-token fraction", [float(row["one_token_fraction"]) for row in rows]),
    ]
    plot_grouped_bars(
        out_dir / "tokenization_by_model.png",
        "Tokenization by run",
        labels,
        series,
        ylabel="Tokens / fraction",
        y_min=0.0,
        y_max=None,
    )


def plot_geometry(geometry_rows: list[dict], out_dir: Path) -> None:
    rows = [row for row in geometry_rows if row["experiment"] in MAIN_RUNS]
    rows.sort(key=lambda row: (BASE_MAIN_RUNS + FULL_MAIN_RUNS).index(row["experiment"]))
    labels = [f"{row['model_short']}\n{row['surface']}" for row in rows]
    series = [
        ("min 90% effective dims", [float(row["min_edim90_components"]) for row in rows]),
        ("collapsed layers", [float(row["collapse_layers_edim90_le_2"]) for row in rows]),
    ]
    plot_grouped_bars(
        out_dir / "geometry_effective_dims.png",
        "Representation geometry summary",
        labels,
        series,
        ylabel="Layer count / components",
        y_min=0.0,
        y_max=None,
    )


def plot_pooling_ablation(metrics: list[dict], out_dir: Path) -> None:
    lookup = metric_lookup(metrics)
    rows = [lookup[(run, "real_templates_random")] for run in POOLING_RUNS if (run, "real_templates_random") in lookup]
    group_labels = [row["pooling"] for row in rows]
    series = []
    for probe in TEMPLATE_PROBES:
        values = [lookup.get((row["experiment"], probe), {}).get("peak_accuracy") for row in rows]
        series.append((PROBE_LABELS[probe], values))
    plot_grouped_bars(
        out_dir / "pooling_ablation_qwen17b.png",
        "Qwen3-1.7B pooling ablation",
        group_labels,
        series,
    )


def find_metric(metrics: list[dict], experiment: str, probe: str) -> dict | None:
    for row in metrics:
        if row["experiment"] == experiment and row["probe"] == probe:
            return row
    return None


def build_markdown(metrics: list[dict], token_rows: list[dict], geometry_rows: list[dict]) -> str:
    lines = [
        "# Cross-Model Summary",
        "",
        "Generated from saved `results.json`, `tokenization_diagnostics.json`, and `representation_diagnostics.json` files.",
        "",
        "## Paper Contribution Framing",
        "",
        "Alakeel et al. evaluate Arabic root-pattern morphology through prompt-based generation, and they note that some model differences may reflect instruction-following behavior rather than morphology alone. This study is complementary: it asks whether template information is recoverable from hidden word representations when no prompt is being followed and no output text is being parsed.",
        "",
        "The probe result should still be stated carefully. It shows linear recoverability of template information, not a causal proof that the model uses this feature during generation.",
        "",
        "Source paper: https://arxiv.org/pdf/2603.15773",
        "",
        "## Base-Form Main Runs",
        "",
    ]
    base_rows = []
    for experiment in BASE_MAIN_RUNS:
        real = find_metric(metrics, experiment, "real_templates_random")
        if not real:
            continue
        base_rows.append(
            [
                experiment,
                real["model_short"],
                fmt(find_metric(metrics, experiment, "real_templates_random")["peak_accuracy"]),
                fmt(find_metric(metrics, experiment, "nonce_templates_heldout_roots")["peak_accuracy"]),
                fmt(find_metric(metrics, experiment, "train_real_test_nonce_overlap")["peak_accuracy"]),
                fmt(find_metric(metrics, experiment, "train_nonce_test_real_overlap")["peak_accuracy"]),
                fmt(mean_for_run(metrics, experiment, "ngram_gap", TEMPLATE_PROBES)),
            ]
        )
    lines.append(
        markdown_table(
            [
                "Run",
                "Model",
                "Real templates",
                "Nonce held-out roots",
                "Real -> nonce",
                "Nonce -> real",
                "Mean n-gram gap",
            ],
            base_rows,
        )
    )
    lines.extend(["", "## Full-Form Family Runs", ""])
    full_rows = []
    for experiment in FULL_MAIN_RUNS:
        real = find_metric(metrics, experiment, "real_templates_random")
        if not real:
            continue
        full_rows.append(
            [
                experiment,
                real["model_short"],
                fmt(find_metric(metrics, experiment, "real_templates_random")["peak_accuracy"]),
                fmt(find_metric(metrics, experiment, "real_templates_random")["ngram_accuracy"]),
                fmt(find_metric(metrics, experiment, "train_real_test_nonce_overlap")["peak_accuracy"]),
                fmt(find_metric(metrics, experiment, "train_nonce_test_real_overlap")["peak_accuracy"]),
                fmt(mean_for_run(metrics, experiment, "ngram_gap", TEMPLATE_PROBES)),
            ]
        )
    lines.append(
        markdown_table(
            [
                "Run",
                "Model",
                "Real templates",
                "Real n-gram",
                "Real -> nonce",
                "Nonce -> real",
                "Mean n-gram gap",
            ],
            full_rows,
        )
    )
    lines.extend(["", "## Tokenization", ""])
    token_table = []
    token_lookup = {row["experiment"]: row for row in token_rows}
    for experiment in BASE_MAIN_RUNS + FULL_MAIN_RUNS:
        row = token_lookup.get(experiment)
        if not row:
            continue
        token_table.append(
            [
                experiment,
                row["model_short"],
                row["surface"],
                fmt(row["mean_tokens"]),
                str(row["max_tokens"]),
                fmt(row["one_token_fraction"]),
            ]
        )
    lines.append(
        markdown_table(
            ["Run", "Model", "Surface", "Mean tokens", "Max tokens", "One-token fraction"],
            token_table,
        )
    )
    lines.extend(["", "## Representation Geometry", ""])
    geo_table = []
    geo_lookup = {row["experiment"]: row for row in geometry_rows}
    for experiment in BASE_MAIN_RUNS + FULL_MAIN_RUNS:
        row = geo_lookup.get(experiment)
        if not row:
            continue
        geo_table.append(
            [
                experiment,
                row["model_short"],
                row["surface"],
                str(row["min_edim90_components"]),
                str(row["min_edim90_layer"]),
                str(row["collapse_layers_edim90_le_2"]),
                fmt(row["max_abs_activation"], 1),
            ]
        )
    lines.append(
        markdown_table(
            [
                "Run",
                "Model",
                "Surface",
                "Min edim90",
                "Min edim90 layer",
                "Collapsed layers",
                "Max abs activation",
            ],
            geo_table,
        )
    )
    lines.extend(
        [
            "",
            "## Reading",
            "",
            "The strongest paper-level signal is template recoverability, especially the nonce held-out-root condition. All main models reach saturated accuracy there, so the result is not a one-model artifact.",
            "",
            "The model comparison is irregular in the same broad sense as Alakeel et al.: tokenizer compactness and Arabic-centric status do not produce a simple performance ordering. Qwen3-8B is strongest on transfer, Fanar is strongest on full-form family-split real templates and has the cleanest geometry, while ALLaM is compactly tokenized but weak on real/nonce transfer.",
            "",
            "The root probes should remain diagnostic. In the nonce condition, character n-grams nearly solve root identity, so root accuracy is not the main evidence for abstract morphology.",
            "",
            "## Generated Files",
            "",
            "- `probe_metrics.csv`: one row per probe per run.",
            "- `token_count_accuracy.csv`: token-count accuracy at each probe peak.",
            "- `tokenization_summary.csv`: tokenizer diagnostics per run.",
            "- `geometry_summary.csv`: representation geometry diagnostics per run.",
            "- `base_template_comparison.png`: base-form template probe comparison.",
            "- `full_family_comparison.png`: full-form family-split comparison.",
            "- `transfer_comparison.png`: real/nonce transfer comparison.",
            "- `ngram_gap_comparison.png`: mean template advantage over n-grams.",
            "- `selectivity_comparison.png`: mean template selectivity over shuffled-label control.",
            "- `tokenization_by_model.png`: tokenization comparison.",
            "- `geometry_effective_dims.png`: geometry comparison.",
            "- `pooling_ablation_qwen17b.png`: Qwen3-1.7B pooling control.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", default="results", type=Path)
    parser.add_argument("--out-dir", default="results/summary", type=Path)
    args = parser.parse_args()

    runs = collect_runs(args.results_dir)
    if not runs:
        raise SystemExit(f"No result files found under {args.results_dir}")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    metrics = collect_metric_rows(runs)
    token_count_rows = collect_token_count_rows(runs)
    token_rows = collect_tokenization_rows(runs)
    geometry_rows = collect_geometry_rows(runs)

    write_csv(
        args.out_dir / "probe_metrics.csv",
        metrics,
        [
            "experiment",
            "main_set",
            "model",
            "model_short",
            "surface",
            "pooling",
            "real_split",
            "probe",
            "probe_label",
            "target",
            "split_kind",
            "n_items",
            "train_size",
            "test_size",
            "group_overlap",
            "peak_layer",
            "peak_depth",
            "peak_accuracy",
            "peak_control_accuracy",
            "peak_selectivity",
            "ngram_accuracy",
            "ngram_gap",
            "chance",
        ],
    )
    write_csv(
        args.out_dir / "token_count_accuracy.csv",
        token_count_rows,
        [
            "experiment",
            "model_short",
            "surface",
            "pooling",
            "real_split",
            "probe",
            "probe_label",
            "n_tokens",
            "n",
            "accuracy",
        ],
    )
    write_csv(
        args.out_dir / "tokenization_summary.csv",
        token_rows,
        [
            "experiment",
            "main_set",
            "model",
            "model_short",
            "surface",
            "pooling",
            "real_split",
            "n_texts",
            "min_tokens",
            "max_tokens",
            "mean_tokens",
            "median_tokens",
            "one_token_count",
            "one_token_fraction",
            "token_count_distribution",
        ],
    )
    write_csv(
        args.out_dir / "geometry_summary.csv",
        geometry_rows,
        [
            "experiment",
            "main_set",
            "model",
            "model_short",
            "surface",
            "pooling",
            "real_split",
            "n_texts",
            "n_layers",
            "hidden_size",
            "max_abs_activation",
            "max_abs_layer",
            "min_edim90_components",
            "min_edim90_fraction",
            "min_edim90_layer",
            "collapse_layers_edim90_le_2",
            "collapse_layer_indices",
        ],
    )

    plot_base_template_comparison(metrics, args.out_dir)
    plot_full_template_comparison(metrics, args.out_dir)
    plot_transfer_comparison(metrics, args.out_dir)
    plot_gap_and_selectivity(metrics, args.out_dir)
    plot_tokenization(token_rows, args.out_dir)
    plot_geometry(geometry_rows, args.out_dir)
    plot_pooling_ablation(metrics, args.out_dir)

    (args.out_dir / "cross_model_summary.md").write_text(
        build_markdown(metrics, token_rows, geometry_rows),
        encoding="utf-8",
    )
    print(f"wrote {args.out_dir}")


if __name__ == "__main__":
    main()
