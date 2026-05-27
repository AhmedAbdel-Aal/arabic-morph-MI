#!/usr/bin/env python3
"""Apply explicit reviewer decisions to a reviewed morphology batch."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

from common import read_jsonl, write_jsonl
from review_curated_dataset import export_probe_row, build_stats


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reviewed-rows", required=True, type=Path)
    parser.add_argument("--decisions", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--root-category", default="audited_abw_reviewed_v1")
    return parser.parse_args()


def decision_key(row: dict[str, Any]) -> tuple[str, str, str, str, str, str]:
    return (
        str(row.get("template", "")),
        str(row.get("base_form", "")),
        str(row.get("full_form", "")),
        str(row.get("prefix", "")),
        str(row.get("suffix", "")),
        str(row.get("surface_rule", "")),
    )


def write_probe_json(path: Path, rows: list[dict[str, Any]], root_category: str) -> None:
    probe_rows = [export_probe_row(row, root_category) for row in rows]
    payload = {
        "corpus_stats": build_stats(probe_rows, root_category),
        "real_roots": probe_rows,
        "nonce_roots": [],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def write_remaining_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "review_status",
        "review_flags",
        "template",
        "morph_class",
        "root",
        "base_form",
        "full_form",
        "prefix",
        "suffix",
        "camel_ambiguity",
        "camel_lex",
        "camel_gloss",
        "sentence",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            analysis = row.get("camel_analysis") or {}
            writer.writerow(
                {
                    "review_status": row.get("review_status", ""),
                    "review_flags": ";".join(row.get("review_flags", [])),
                    "template": row.get("template", ""),
                    "morph_class": row.get("morph_class", ""),
                    "root": row.get("root", ""),
                    "base_form": row.get("base_form", ""),
                    "full_form": row.get("full_form", ""),
                    "prefix": row.get("prefix", ""),
                    "suffix": row.get("suffix", ""),
                    "camel_ambiguity": row.get("camel_ambiguity", ""),
                    "camel_lex": analysis.get("lex", ""),
                    "camel_gloss": analysis.get("gloss", ""),
                    "sentence": row.get("example_sentence", ""),
                }
            )


def main() -> None:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    decisions = {decision_key(row): row for row in read_jsonl(args.decisions)}
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    remaining: list[dict[str, Any]] = []
    applied = 0

    for row in read_jsonl(args.reviewed_rows):
        row = dict(row)
        decision = decisions.get(decision_key(row))
        if decision:
            applied += 1
            row["reviewer_decision"] = decision.get("decision", "")
            row["reviewer_reason"] = decision.get("reason", "")
            row["reviewer_notes"] = decision.get("notes", "")
            if decision.get("decision") == "accept":
                accepted.append(row)
            elif decision.get("decision") == "reject":
                rejected.append(row)
            else:
                remaining.append(row)
        elif row.get("review_status") == "accept_low_risk":
            row["reviewer_decision"] = "accept"
            row["reviewer_reason"] = "low_risk_automatic_second_pass"
            accepted.append(row)
        else:
            remaining.append(row)

    write_jsonl(args.out_dir / "accepted_after_review.jsonl", accepted)
    write_jsonl(args.out_dir / "rejected_after_review.jsonl", rejected)
    write_jsonl(args.out_dir / "remaining_review_queue.jsonl", remaining)
    write_remaining_csv(args.out_dir / "remaining_review_queue.csv", remaining)
    write_probe_json(args.out_dir / "productivity_dataset_reviewed.json", accepted, args.root_category)

    report = {
        "reviewed_rows": str(args.reviewed_rows),
        "decisions": str(args.decisions),
        "n_decisions": len(decisions),
        "n_decisions_applied": applied,
        "n_accepted": len(accepted),
        "n_rejected": len(rejected),
        "n_remaining_review": len(remaining),
        "accepted_by_template": dict(Counter(row.get("template", "") for row in accepted)),
        "remaining_by_template": dict(Counter(row.get("template", "") for row in remaining)),
        "rejected_by_template": dict(Counter(row.get("template", "") for row in rejected)),
        "outputs": {
            "accepted": str(args.out_dir / "accepted_after_review.jsonl"),
            "rejected": str(args.out_dir / "rejected_after_review.jsonl"),
            "remaining_review_queue": str(args.out_dir / "remaining_review_queue.jsonl"),
            "remaining_review_queue_csv": str(args.out_dir / "remaining_review_queue.csv"),
            "productivity_dataset_reviewed": str(args.out_dir / "productivity_dataset_reviewed.json"),
        },
    }
    (args.out_dir / "review_decision_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(f"wrote {args.out_dir / 'accepted_after_review.jsonl'}")
    print(f"wrote {args.out_dir / 'remaining_review_queue.jsonl'}")
    print(f"wrote {args.out_dir / 'productivity_dataset_reviewed.json'}")
    print(f"accepted={len(accepted)} rejected={len(rejected)} remaining_review={len(remaining)} decisions_applied={applied}")


if __name__ == "__main__":
    main()
