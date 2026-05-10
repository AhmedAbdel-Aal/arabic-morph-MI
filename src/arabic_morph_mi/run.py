from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from arabic_morph_mi.data import (
    Item,
    keep_labels_with_min_count,
    load_productivity_dataset,
    make_items,
    overlap_by_label,
    with_labels,
)
from arabic_morph_mi.diagnostics import representation_diagnostics
from arabic_morph_mi.io import timestamp, write_json
from arabic_morph_mi.model import encode_texts, load_model, tokenization_diagnostics
from arabic_morph_mi.plot import plot_curves
from arabic_morph_mi.probe import layer_probe
from arabic_morph_mi.splits import (
    group_split_summary,
    grouped_one_per_label_test_split,
    grouped_random_split,
    heldout_root_split,
    heldout_template_split,
    one_per_label_test_split,
    random_split,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/productivity_dataset.json")
    parser.add_argument("--model", default="Qwen/Qwen3-1.7B-Base")
    parser.add_argument("--surface", choices=["base", "full"], default="base")
    parser.add_argument("--pooling", choices=["last", "first", "mean"], default="last")
    parser.add_argument(
        "--real-split",
        choices=["item", "family"],
        default="item",
        help="Use item-level real splits, or group real variants by root/template/base_form.",
    )
    parser.add_argument("--run-id", help="Optional output folder name under --output-dir, e.g. E03.")
    parser.add_argument("--output-dir", default="results")
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dtype", default="auto", choices=["auto", "float16", "fp16", "bfloat16", "bf16", "float32"])
    parser.add_argument(
        "--save-representations",
        action="store_true",
        help="Save pooled hidden representations as compressed NPZ in the run folder.",
    )
    parser.add_argument(
        "--representation-dtype",
        choices=["float16", "float32"],
        default="float16",
        help="Storage dtype for saved representations. float16 is smaller and enough for exploration.",
    )
    return parser.parse_args()


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


def run_one(
    name: str,
    items: list[Item],
    labels: list[str],
    y: list[int],
    train,
    test,
    hidden_by_text: dict[str, np.ndarray],
    control_seed: int,
    token_count_by_text: dict[str, int],
    split_kind: str,
) -> dict:
    texts = [item.text for item in items]
    X = np.stack([hidden_by_text[text] for text in texts])
    token_counts = [token_count_by_text[text] for text in texts]
    print(f"\n{name}: {len(items)} items, {len(labels)} labels")
    result = layer_probe(
        X,
        y,
        labels,
        texts,
        train,
        test,
        control_seed=control_seed,
        token_counts=token_counts,
    )
    result["labels"] = labels
    result["n_items"] = len(items)
    result["train_size"] = int(len(train))
    result["test_size"] = int(len(test))
    result["split_kind"] = split_kind
    if split_kind == "family":
        result["group_split"] = group_split_summary(items, train, test)
    return result


def real_random_split(items: list[Item], y: list[int], args: argparse.Namespace) -> tuple[np.ndarray, np.ndarray, str]:
    if args.real_split == "family":
        train, test = grouped_random_split(items, y, args.test_size, args.seed)
        return train, test, "family"
    train, test = random_split(y, args.test_size, args.seed)
    return train, test, "item"


def real_root_split(items: list[Item], y: list[int], args: argparse.Namespace) -> tuple[np.ndarray, np.ndarray, str]:
    if args.real_split == "family":
        train, test = grouped_one_per_label_test_split(items, y, args.seed + 3)
        return train, test, "family"
    train, test = one_per_label_test_split(y, args.seed + 3)
    return train, test, "item"


def save_representations(
    path: Path,
    hidden_by_text: dict[str, np.ndarray],
    model_name: str,
    surface: str,
    pooling: str,
    dtype: str,
) -> None:
    texts = sorted(hidden_by_text)
    hidden = np.stack([hidden_by_text[text] for text in texts])
    if dtype == "float16":
        hidden = hidden.astype(np.float16)
    elif dtype == "float32":
        hidden = hidden.astype(np.float32)
    else:
        raise ValueError(f"Unsupported representation dtype: {dtype}")

    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        path,
        hidden=hidden,
        texts=np.asarray(texts),
        model=np.asarray(model_name),
        surface=np.asarray(surface),
        pooling=np.asarray(pooling),
        dtype=np.asarray(str(hidden.dtype)),
    )


def main() -> None:
    args = parse_args()
    payload = load_productivity_dataset(args.data)

    real = make_items(payload, "real", args.surface)
    nonce = make_items(payload, "nonce", "base")
    real_overlap, nonce_overlap = overlap_by_label(real, nonce)

    experiments = {}
    skipped_experiments = {}

    labels, y = with_labels(real, "template")
    train, test, split_kind = real_random_split(real, y, args)
    experiments["real_templates_random"] = (real, labels, y, train, test, split_kind)

    labels, y = with_labels(nonce, "template")
    train, test = random_split(y, args.test_size, args.seed + 1)
    experiments["nonce_templates_random"] = (nonce, labels, y, train, test, "item")

    train, test = heldout_root_split(nonce, y, args.test_size, args.seed + 2)
    experiments["nonce_templates_heldout_roots"] = (nonce, labels, y, train, test, "heldout_root")

    experiments["train_real_test_nonce_overlap"] = (*explicit_split(real_overlap, nonce_overlap, "template"), "explicit")
    experiments["train_nonce_test_real_overlap"] = (*explicit_split(nonce_overlap, real_overlap, "template"), "explicit")

    real_roots = keep_labels_with_min_count(real, "root", min_count=2)
    labels, y = with_labels(real_roots, "root")
    try:
        train, test, split_kind = real_root_split(real_roots, y, args)
    except ValueError as exc:
        skipped_experiments["real_roots_random"] = str(exc)
    else:
        experiments["real_roots_random"] = (real_roots, labels, y, train, test, split_kind)

    labels, y = with_labels(nonce, "root")
    train, test = random_split(y, args.test_size, args.seed + 4)
    experiments["nonce_roots_random"] = (nonce, labels, y, train, test, "item")

    train, test = heldout_template_split(nonce, y, args.test_size, args.seed + 5)
    experiments["nonce_roots_heldout_templates"] = (nonce, labels, y, train, test, "heldout_template")

    texts = sorted({item.text for exp in experiments.values() for item in exp[0]})
    tokenizer, model, input_device = load_model(args.model, args.dtype)
    tokenization = tokenization_diagnostics(texts, tokenizer)
    token_count_by_text = {item["text"]: item["n_tokens"] for item in tokenization["items"]}
    print(
        "tokenization:",
        f"n={tokenization['n_texts']}",
        f"min={tokenization['min_tokens']}",
        f"max={tokenization['max_tokens']}",
        f"mean={tokenization['mean_tokens']:.2f}",
    )
    hidden_by_text = encode_texts(texts, tokenizer, model, input_device, args.batch_size, args.pooling)
    representation = representation_diagnostics(hidden_by_text)

    run_name = args.run_id or f"{timestamp()}_{args.model.split('/')[-1]}_{args.surface}_{args.pooling}"
    run_dir = Path(args.output_dir) / run_name
    if run_dir.exists():
        raise SystemExit(f"Output folder already exists: {run_dir}")
    results = {
        name: run_one(
            name,
            items,
            labels,
            y,
            train,
            test,
            hidden_by_text,
            control_seed=args.seed + i,
            token_count_by_text=token_count_by_text,
            split_kind=split_kind,
        )
        for i, (name, (items, labels, y, train, test, split_kind)) in enumerate(experiments.items())
    }

    write_json(run_dir / "tokenization_diagnostics.json", tokenization)
    write_json(run_dir / "representation_diagnostics.json", representation)
    write_json(
        run_dir / "results.json",
        {
            "model": args.model,
            "surface": args.surface,
            "pooling": args.pooling,
            "real_split": args.real_split,
            "data": str(args.data),
            "skipped_experiments": skipped_experiments,
            "tokenization_summary": {k: v for k, v in tokenization.items() if k != "items"},
            "representation_summary": {
                "n_texts": representation["n_texts"],
                "n_layers": representation["n_layers"],
                "hidden_size": representation["hidden_size"],
            },
            "results": results,
        },
    )
    plot_curves(results, run_dir / "curves.png")
    if args.save_representations:
        representation_path = run_dir / "hidden_representations.npz"
        save_representations(
            representation_path,
            hidden_by_text,
            model_name=args.model,
            surface=args.surface,
            pooling=args.pooling,
            dtype=args.representation_dtype,
        )
        print(f"wrote {representation_path}")
    print(f"\nwrote {run_dir / 'results.json'}")
    print(f"wrote {run_dir / 'curves.png'}")


if __name__ == "__main__":
    main()
