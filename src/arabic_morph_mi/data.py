from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

ARABIC_DIACRITICS = re.compile(r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]")


@dataclass(frozen=True)
class Item:
    text: str
    template: str
    root: str
    source: str
    base_form: str
    full_form: str
    has_affix: bool


def remove_diacritics(text: str) -> str:
    return ARABIC_DIACRITICS.sub("", text)


def normalize_root(root: str) -> str:
    return root.replace(".", "").replace(" ", "")


def load_productivity_dataset(path: str | Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def make_items(payload: dict, source: str, surface: str) -> list[Item]:
    if source not in {"real", "nonce"}:
        raise ValueError("source must be 'real' or 'nonce'")
    if surface not in {"base", "full"}:
        raise ValueError("surface must be 'base' or 'full'")

    key = "real_roots" if source == "real" else "nonce_roots"
    rows = payload[key]
    items: list[Item] = []
    for row in rows:
        text = row["base_form"] if surface == "base" else row["full_form"]
        items.append(
            Item(
                text=remove_diacritics(text),
                template=row["template"],
                root=normalize_root(row["root"]),
                source=source,
                base_form=remove_diacritics(row["base_form"]),
                full_form=remove_diacritics(row["full_form"]),
                has_affix=bool(row["has_affix"]),
            )
        )

    if source == "real" and surface == "base":
        items = [item for item in items if not item.has_affix]

    return items


def with_labels(items: list[Item], target: str) -> tuple[list[str], list[int]]:
    if target not in {"template", "root"}:
        raise ValueError("target must be 'template' or 'root'")
    labels = sorted({getattr(item, target) for item in items})
    label_to_id = {label: idx for idx, label in enumerate(labels)}
    y = [label_to_id[getattr(item, target)] for item in items]
    return labels, y


def overlap_by_label(train_items: list[Item], test_items: list[Item]) -> tuple[list[Item], list[Item]]:
    labels = {item.template for item in train_items} & {item.template for item in test_items}
    return (
        [item for item in train_items if item.template in labels],
        [item for item in test_items if item.template in labels],
    )


def keep_labels_with_min_count(items: list[Item], target: str, min_count: int) -> list[Item]:
    counts: dict[str, int] = {}
    for item in items:
        label = getattr(item, target)
        counts[label] = counts.get(label, 0) + 1
    return [item for item in items if counts[getattr(item, target)] >= min_count]
