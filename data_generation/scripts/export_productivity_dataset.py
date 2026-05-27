#!/usr/bin/env python3
"""Export audited rows to the probing dataset JSON shape."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from common import read_jsonl


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--root-category", default="audited_abw")
    return parser.parse_args()


def export_row(row: dict[str, Any], root_category: str) -> dict[str, Any]:
    return {
        "root": row.get("root", ""),
        "template": row.get("template", ""),
        "base_form": row.get("base_form") or row.get("canonical_base_form", ""),
        "prefix": row.get("prefix", ""),
        "suffix": row.get("suffix", ""),
        "full_form": row.get("full_form", ""),
        "has_affix": bool(row.get("has_affix")),
        "root_category": root_category,
        "morph_class": row.get("morph_class", ""),
        "dataset_use": row.get("dataset_use", ""),
        "source_dataset": row.get("example_source_dataset", ""),
        "source_datasets": row.get("source_datasets", []),
        "source": row.get("example_source", ""),
        "url": row.get("example_url", ""),
        "sentence": row.get("example_sentence", ""),
        "camel_ambiguity": row.get("camel_ambiguity", ""),
        "camel_analysis": row.get("camel_analysis", {}),
        "audit_decision": row.get("audit_decision", ""),
        "audit_reason": row.get("audit_reason", ""),
        "audit_notes": row.get("audit_notes", ""),
    }


def build_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    template_counts = Counter(row.get("template", "") for row in rows)
    roots = {row.get("root", "") for row in rows}
    return {
        "total_real_roots": len(roots),
        "total_nonce_roots": 0,
        "with_affix_real": sum(1 for row in rows if row.get("has_affix")),
        "with_affix_nonce": 0,
        "root_category_counts": {
            "real": dict(Counter(row.get("root_category", "") for row in rows)),
            "nonce": {},
        },
        "templates_used": {
            "real": {
                template: {"type": "audited_abw", "count": count}
                for template, count in sorted(template_counts.items())
            },
            "nonce": {},
        },
    }


def main() -> None:
    args = parse_args()
    rows = [export_row(row, args.root_category) for row in read_jsonl(args.input)]
    payload = {
        "corpus_stats": build_stats(rows),
        "real_roots": rows,
        "nonce_roots": [],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    print(f"wrote {args.output}")
    print(f"rows={len(rows)} roots={payload['corpus_stats']['total_real_roots']}")


if __name__ == "__main__":
    main()
