#!/usr/bin/env python3
"""Create token-level and type-level views from candidate JSONL."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from common import read_jsonl, write_jsonl


TYPE_KEY_FIELDS = [
    "root",
    "template",
    "base_form",
    "canonical_base_form",
    "surface_stem",
    "prefix",
    "suffix",
    "full_form",
    "surface_rule",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    return parser.parse_args()


def type_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return tuple(row.get(field, "") for field in TYPE_KEY_FIELDS)


def main() -> None:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    rows = list(read_jsonl(args.candidates))

    token_path = args.out_dir / "token_level.jsonl"
    type_path = args.out_dir / "type_level.jsonl"
    report_path = args.out_dir / "view_report.json"

    write_jsonl(token_path, rows)

    types: dict[tuple[Any, ...], dict[str, Any]] = {}
    for row in rows:
        key = type_key(row)
        if key not in types:
            types[key] = {
                field: row.get(field, "") for field in TYPE_KEY_FIELDS
            }
            types[key].update(
                {
                    "pos": row.get("pos", ""),
                    "camel_ambiguity": row.get("camel_ambiguity", ""),
                    "camel_analysis": row.get("camel_analysis", {}),
                    "has_affix": row.get("has_affix", False),
                    "n_token_occurrences": 0,
                    "sentence_ids": [],
                    "sentence_refs": [],
                    "source_datasets": [],
                    "example_sentence": row.get("sentence", ""),
                    "example_source_dataset": row.get("source_dataset", ""),
                    "example_source": row.get("source", ""),
                    "example_url": row.get("url", ""),
                }
            )
        types[key]["n_token_occurrences"] += 1
        sentence_id = row.get("sentence_id")
        if sentence_id and sentence_id not in types[key]["sentence_ids"]:
            types[key]["sentence_ids"].append(sentence_id)
        source_dataset = row.get("source_dataset")
        if source_dataset and source_dataset not in types[key]["source_datasets"]:
            types[key]["source_datasets"].append(source_dataset)
        if sentence_id:
            sentence_ref = f"{source_dataset or row.get('source', '')}:{sentence_id}"
            if sentence_ref not in types[key]["sentence_refs"]:
                types[key]["sentence_refs"].append(sentence_ref)

    type_rows = sorted(types.values(), key=lambda r: (r["template"], r["root"], r["full_form"]))
    write_jsonl(type_path, type_rows)

    report = {
        "candidates_path": str(args.candidates),
        "token_level_path": str(token_path),
        "type_level_path": str(type_path),
        "n_token_rows": len(rows),
        "n_type_rows": len(type_rows),
        "by_template_token": dict(Counter(row.get("template") for row in rows)),
        "by_template_type": dict(Counter(row.get("template") for row in type_rows)),
        "by_surface_rule_token": dict(Counter(row.get("surface_rule") for row in rows)),
        "by_surface_rule_type": dict(Counter(row.get("surface_rule") for row in type_rows)),
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    print(f"wrote {token_path}")
    print(f"wrote {type_path}")
    print(f"wrote {report_path}")
    print(f"token_rows={len(rows)} type_rows={len(type_rows)}")


if __name__ == "__main__":
    main()
