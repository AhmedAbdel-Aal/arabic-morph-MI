#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np


MODELS = {
    "qwen17b": "Qwen/Qwen3-1.7B-Base",
    "qwen8b": "Qwen/Qwen3-8B",
    "fanar9b": "QCRI/Fanar-1-9B",
    "allam7b": "humain-ai/ALLaM-7B-Instruct-preview",
    "llama3_8b": "meta-llama/Meta-Llama-3-8B",
    "acegpt7b": "FreedomIntelligence/AceGPT-7B",
}

DATASETS = {
    "AKEEL30": "data/productivity_dataset.json",
    "NATURAL100": "data/productivity_dataset_natural_almost100.json",
}

CONFIGURATIONS = {
    "full": "family",
    "base": "item",
}

REQUIRED_FILES = (
    "results.json",
    "curves.png",
    "tokenization_diagnostics.json",
    "representation_diagnostics.json",
    "hidden_representations.npz",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def scalar_text(array: np.ndarray) -> str:
    return str(array.item())


def expected_runs() -> list[dict[str, str]]:
    runs = []
    for model_id, model in MODELS.items():
        for dataset_id, data_path in DATASETS.items():
            for surface, real_split in CONFIGURATIONS.items():
                run_id = f"{dataset_id}_{model_id}_{surface}_last_{real_split}"
                runs.append(
                    {
                        "run_id": run_id,
                        "dataset_id": dataset_id,
                        "data": data_path,
                        "model_id": model_id,
                        "model": model,
                        "surface": surface,
                        "pooling": "last",
                        "real_split": real_split,
                    }
                )
    return runs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="results/final_everything")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    errors: list[str] = []
    hashes: dict[str, list[dict[str, str]]] = defaultdict(list)
    runs = expected_runs()

    for expected in runs:
        run_id = expected["run_id"]
        run_dir = output_dir / run_id
        if not run_dir.is_dir():
            errors.append(f"{run_id}: missing run directory")
            continue

        for filename in REQUIRED_FILES:
            if not (run_dir / filename).is_file():
                errors.append(f"{run_id}: missing {filename}")

        results_path = run_dir / "results.json"
        if results_path.is_file():
            results = json.loads(results_path.read_text(encoding="utf-8"))
            for key in ("model", "data", "surface", "pooling", "real_split"):
                if results.get(key) != expected[key]:
                    errors.append(
                        f"{run_id}: results.json {key}={results.get(key)!r}, "
                        f"expected {expected[key]!r}"
                    )

        representations_path = run_dir / "hidden_representations.npz"
        if representations_path.is_file():
            with np.load(representations_path) as representations:
                for key in ("model", "surface", "pooling"):
                    actual = scalar_text(representations[key])
                    if actual != expected[key]:
                        errors.append(
                            f"{run_id}: hidden_representations.npz {key}={actual!r}, "
                            f"expected {expected[key]!r}"
                        )
            hashes[sha256(representations_path)].append(expected)

    for digest, matching_runs in hashes.items():
        model_ids = {run["model_id"] for run in matching_runs}
        if len(model_ids) > 1:
            run_ids = ", ".join(run["run_id"] for run in matching_runs)
            errors.append(
                f"identical representation archive across models ({digest[:12]}): {run_ids}"
            )

    print(f"checked: {len(runs)} expected runs")
    print(f"errors:  {len(errors)}")
    if errors:
        print()
        for error in errors:
            print(f"- {error}")
        return 1

    print("verification passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
