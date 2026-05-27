#!/usr/bin/env python3
"""Build a small conservative seed dataset from prepared audit rows."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from common import read_jsonl, write_jsonl


DERIVED_VERB_TEMPLATES = {"استفعل", "انفعل"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    return parser.parse_args()


def int_value(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def is_conservative_main_accept(row: dict[str, Any]) -> bool:
    analysis = row.get("camel_analysis") or {}
    return (
        row.get("audit_bucket") == "low_review"
        and row.get("pos") == "verb"
        and analysis.get("pos") == "verb"
        and row.get("template") in DERIVED_VERB_TEMPLATES
        and int_value(row.get("camel_ambiguity")) < 10
        and "name_or_place_signal" not in set(row.get("audit_flags") or [])
    )


def mark_accept(row: dict[str, Any]) -> dict[str, Any]:
    row = dict(row)
    row["audit_decision"] = "accept"
    row["audit_reason"] = "valid_clean"
    row["morph_class"] = "target_form_x_verb" if row.get("template") == "استفعل" else "target_form_vii_verb"
    row["dataset_use"] = "main_target"
    row["audit_notes"] = (
        "Conservative rule seed: CAMEL and tagger agree on verb, template is derived verb, "
        "ambiguity is below 10, and no name/place signal was found. Still suitable for spot-checking."
    )
    return row


def mark_review(row: dict[str, Any]) -> dict[str, Any]:
    row = dict(row)
    row["audit_decision"] = ""
    row["audit_reason"] = ""
    row["morph_class"] = row.get("suggested_morph_class", "")
    row["dataset_use"] = row.get("suggested_dataset_use", "needs_review")
    row["audit_notes"] = ""
    return row


def main() -> None:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    rows = list(read_jsonl(args.input))
    accepted = [mark_accept(row) for row in rows if is_conservative_main_accept(row)]
    review = [mark_review(row) for row in rows if not is_conservative_main_accept(row)]

    write_jsonl(args.out_dir / "main_target_seed.jsonl", accepted)
    write_jsonl(args.out_dir / "review_queue.jsonl", review)
    report = {
        "input": str(args.input),
        "accepted_main_seed": str(args.out_dir / "main_target_seed.jsonl"),
        "review_queue": str(args.out_dir / "review_queue.jsonl"),
        "n_input": len(rows),
        "n_main_target_seed": len(accepted),
        "n_review_queue": len(review),
        "accepted_by_template": dict(Counter(row.get("template", "") for row in accepted)),
        "review_by_audit_bucket": dict(Counter(row.get("audit_bucket", "") for row in review)),
        "review_by_suggested_morph_class": dict(Counter(row.get("suggested_morph_class", "") for row in review)),
    }
    (args.out_dir / "seed_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(f"wrote {args.out_dir / 'main_target_seed.jsonl'}")
    print(f"wrote {args.out_dir / 'review_queue.jsonl'}")
    print(f"wrote {args.out_dir / 'seed_report.json'}")
    print(f"accepted={len(accepted)} review={len(review)}")


if __name__ == "__main__":
    main()
