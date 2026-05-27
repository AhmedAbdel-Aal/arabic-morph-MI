#!/usr/bin/env python3
"""Select Akeel-style families: base form plus two affixed variants."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from common import read_jsonl, write_jsonl


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--affixed-per-family", type=int, default=2)
    return parser.parse_args()


def family_key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (row.get("root", ""), row.get("template", ""), row.get("base_form", ""))


def sort_variant(row: dict[str, Any]) -> tuple[int, int, str]:
    prefix = row.get("prefix", "")
    suffix = row.get("suffix", "")
    # Prefer simpler affixes, then deterministic surface order.
    return (len(prefix) + len(suffix), 0 if prefix else 1, row.get("full_form", ""))


def select_family_rows(rows: list[dict[str, Any]], affixed_per_family: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    families: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        families[family_key(row)].append(row)

    selected: list[dict[str, Any]] = []
    incomplete: list[dict[str, Any]] = []
    for key, family_rows in sorted(families.items(), key=lambda item: item[0]):
        base_rows = sorted([row for row in family_rows if not row.get("has_affix")], key=sort_variant)
        affixed_rows = sorted([row for row in family_rows if row.get("has_affix")], key=sort_variant)
        if not base_rows or len(affixed_rows) < affixed_per_family:
            example = dict(family_rows[0])
            example["family_status"] = "incomplete"
            example["family_n_base_rows"] = len(base_rows)
            example["family_n_affixed_rows"] = len(affixed_rows)
            incomplete.append(example)
            continue

        family_selection = [base_rows[0], *affixed_rows[:affixed_per_family]]
        for index, row in enumerate(family_selection):
            row = dict(row)
            row["family_id"] = "|".join(key)
            row["family_variant_role"] = "base" if index == 0 else f"affixed_{index}"
            row["family_status"] = "complete_base_plus_affixes"
            selected.append(row)

    return selected, incomplete


def write_report(path: Path, selected: list[dict[str, Any]], incomplete: list[dict[str, Any]], args: argparse.Namespace) -> None:
    families = {row.get("family_id", "") for row in selected}
    report = {
        "input": str(args.input),
        "selected_path": str(args.out_dir / "family_balanced_rows.jsonl"),
        "incomplete_path": str(args.out_dir / "incomplete_families.jsonl"),
        "affixed_per_family": args.affixed_per_family,
        "n_selected_rows": len(selected),
        "n_selected_families": len(families),
        "n_incomplete_families": len(incomplete),
        "selected_by_template": dict(Counter(row.get("template", "") for row in selected)),
        "selected_families_by_template": dict(Counter(row.get("template", "") for row in selected if row.get("family_variant_role") == "base")),
        "incomplete_by_template": dict(Counter(row.get("template", "") for row in incomplete)),
        "variant_roles": dict(Counter(row.get("family_variant_role", "") for row in selected)),
    }
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def main() -> None:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    rows = list(read_jsonl(args.input))
    selected, incomplete = select_family_rows(rows, args.affixed_per_family)
    write_jsonl(args.out_dir / "family_balanced_rows.jsonl", selected)
    write_jsonl(args.out_dir / "incomplete_families.jsonl", incomplete)
    write_report(args.out_dir / "family_balanced_report.json", selected, incomplete, args)
    print(f"wrote {args.out_dir / 'family_balanced_rows.jsonl'}")
    print(f"wrote {args.out_dir / 'incomplete_families.jsonl'}")
    print(f"wrote {args.out_dir / 'family_balanced_report.json'}")
    print(f"selected_rows={len(selected)} selected_families={len(selected) // (1 + args.affixed_per_family)}")


if __name__ == "__main__":
    main()
