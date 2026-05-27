#!/usr/bin/env python3
"""Combine accepted JSONL row files without changing row contents."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import read_jsonl, write_jsonl


def row_key(row: dict) -> tuple[str, str, str, str, str, str, str]:
    return (
        str(row.get("source_dataset") or row.get("example_source_dataset", "")),
        str(row.get("template", "")),
        str(row.get("root", "")),
        str(row.get("base_form", "")),
        str(row.get("full_form", "")),
        str(row.get("prefix", "")),
        str(row.get("suffix", "")),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", nargs="+", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    rows: list[dict] = []
    seen: set[tuple[str, str, str, str, str, str, str]] = set()
    input_counts: dict[str, int] = {}
    dropped_duplicates = 0
    for path in args.inputs:
        count = 0
        for row in read_jsonl(path):
            count += 1
            key = row_key(row)
            if key in seen:
                dropped_duplicates += 1
                continue
            seen.add(key)
            rows.append(row)
        input_counts[str(path)] = count

    write_jsonl(args.output, rows)
    report = {
        "inputs": [str(path) for path in args.inputs],
        "input_counts": input_counts,
        "output": str(args.output),
        "n_output_rows": len(rows),
        "n_dropped_duplicates": dropped_duplicates,
    }
    report_path = args.report or args.output.with_name("combine_report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    print(f"wrote {args.output}")
    print(f"wrote {report_path}")
    print(f"rows={len(rows)} dropped_duplicates={dropped_duplicates}")


if __name__ == "__main__":
    main()
