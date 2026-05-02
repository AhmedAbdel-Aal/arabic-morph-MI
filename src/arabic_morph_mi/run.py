from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from arabic_morph_mi.data import Item, load_productivity_dataset, make_items, overlap_by_label, with_labels
from arabic_morph_mi.io import timestamp, write_json
from arabic_morph_mi.model import encode_last_token, load_model
from arabic_morph_mi.plot import plot_curves
from arabic_morph_mi.probe import layer_probe
from arabic_morph_mi.splits import heldout_root_split, random_split


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/productivity_dataset.json")
    parser.add_argument("--model", default="Qwen/Qwen3-1.7B-Base")
    parser.add_argument("--surface", choices=["base", "full"], default="base")
    parser.add_argument("--output-dir", default="results")
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dtype", default="auto", choices=["auto", "float16", "fp16", "bfloat16", "bf16", "float32"])
    return parser.parse_args()


def explicit_split(train_items: list[Item], test_items: list[Item]) -> tuple[list[Item], list[str], list[int], np.ndarray, np.ndarray]:
    items = train_items + test_items
    labels, y = with_labels(items)
    train = np.arange(len(train_items))
    test = np.arange(len(train_items), len(items))
    return items, labels, y, train, test


def run_one(name: str, items: list[Item], labels: list[str], y: list[int], train, test, hidden_by_text: dict[str, np.ndarray]) -> dict:
    texts = [item.text for item in items]
    X = np.stack([hidden_by_text[text] for text in texts])
    print(f"\n{name}: {len(items)} items, {len(labels)} labels")
    result = layer_probe(X, y, labels, texts, train, test)
    result["labels"] = labels
    result["n_items"] = len(items)
    result["train_size"] = int(len(train))
    result["test_size"] = int(len(test))
    return result


def main() -> None:
    args = parse_args()
    payload = load_productivity_dataset(args.data)

    real = make_items(payload, "real", args.surface)
    nonce = make_items(payload, "nonce", "base")
    real_overlap, nonce_overlap = overlap_by_label(real, nonce)

    experiments = {}

    labels, y = with_labels(real)
    train, test = random_split(y, args.test_size, args.seed)
    experiments["real_templates_random"] = (real, labels, y, train, test)

    labels, y = with_labels(nonce)
    train, test = random_split(y, args.test_size, args.seed + 1)
    experiments["nonce_templates_random"] = (nonce, labels, y, train, test)

    train, test = heldout_root_split(nonce, y, args.test_size, args.seed + 2)
    experiments["nonce_templates_heldout_roots"] = (nonce, labels, y, train, test)

    experiments["train_real_test_nonce_overlap"] = explicit_split(real_overlap, nonce_overlap)
    experiments["train_nonce_test_real_overlap"] = explicit_split(nonce_overlap, real_overlap)

    texts = sorted({item.text for exp in experiments.values() for item in exp[0]})
    tokenizer, model, input_device = load_model(args.model, args.dtype)
    hidden_by_text = encode_last_token(texts, tokenizer, model, input_device, args.batch_size)

    run_dir = Path(args.output_dir) / f"{timestamp()}_{args.model.split('/')[-1]}_{args.surface}"
    results = {
        name: run_one(name, items, labels, y, train, test, hidden_by_text)
        for name, (items, labels, y, train, test) in experiments.items()
    }

    write_json(
        run_dir / "results.json",
        {
            "model": args.model,
            "surface": args.surface,
            "data": str(args.data),
            "results": results,
        },
    )
    plot_curves(results, run_dir / "curves.png")
    print(f"\nwrote {run_dir / 'results.json'}")
    print(f"wrote {run_dir / 'curves.png'}")


if __name__ == "__main__":
    main()
