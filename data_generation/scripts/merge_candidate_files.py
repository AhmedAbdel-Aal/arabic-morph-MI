#!/usr/bin/env python3
"""Merge per-source candidate JSONL files before building combined views."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from common import read_jsonl, write_jsonl


DEDUP_FIELDS = [
    "source_dataset",
    "sentence_id",
    "target_token_index",
    "target_text",
    "root",
    "template",
    "base_form",
    "full_form",
    "prefix",
    "suffix",
    "surface_rule",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", required=True, nargs="+", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", type=Path)
    return parser.parse_args()


def dedup_key(row: dict[str, Any]) -> tuple[str, ...]:
    return tuple(str(row.get(field, "")) for field in DEDUP_FIELDS)


def main() -> None:
    args = parse_args()
    merged: dict[tuple[str, ...], dict[str, Any]] = {}
    input_counts: Counter[str] = Counter()
    source_counts: Counter[str] = Counter()

    for path in args.inputs:
        for row in read_jsonl(path):
            input_counts[str(path)] += 1
            source = str(row.get("source_dataset") or row.get("source") or "")
            source_counts[source] += 1
            merged.setdefault(dedup_key(row), row)

    rows = sorted(
        merged.values(),
        key=lambda row: (
            str(row.get("source_dataset", "")),
            str(row.get("sentence_id", "")),
            int(row.get("target_token_index") or 0),
            str(row.get("template", "")),
            str(row.get("full_form", "")),
        ),
    )
    write_jsonl(args.output, rows)

    report_path = args.report or args.output.with_name("merge_report.json")
    report = {
        "inputs": [str(path) for path in args.inputs],
        "output": str(args.output),
        "n_input_rows": sum(input_counts.values()),
        "n_output_rows": len(rows),
        "n_dropped_duplicates": sum(input_counts.values()) - len(rows),
        "input_counts": dict(input_counts),
        "source_counts": dict(source_counts),
        "by_template": dict(Counter(row.get("template", "") for row in rows)),
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    print(f"wrote {args.output}")
    print(f"wrote {report_path}")
    print(f"input_rows={report['n_input_rows']} output_rows={len(rows)}")


if __name__ == "__main__":
    main()
