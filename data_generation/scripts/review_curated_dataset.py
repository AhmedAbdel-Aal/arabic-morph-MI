#!/usr/bin/env python3
"""Run a second-pass audit over a curated morphology batch.

This script does not replace linguistic review. It makes the review state explicit:
each accepted row is either kept as low-risk or placed in a review queue with
specific reasons. The strict low-risk export is useful for sanity-check probes;
the review queue is the next item-by-item audit target.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

from common import normalize_ar, read_jsonl, write_jsonl


HIGH_AMBIGUITY = 15
MEDIUM_AMBIGUITY = 10
REVIEW_TEMPLATES = {"فعال", "فاعل", "فعيل", "فعول", "فعلاء", "فعالة", "مفعال"}
SMALL_CLASS_TEMPLATES = {"مفعال", "فعلان"}
ABSTRACT_NOUN_TEMPLATES = {"فعالة", "افتعال"}
BROKEN_PLURAL_TEMPLATES = {"فعال", "فعلاء", "فعول"}


def norm_lexical(text: str) -> str:
    return normalize_ar(text).replace("ٱ", "ا")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument(
        "--root-category",
        default="audited_abw_review_pass_001_low_risk",
        help="root_category used for the strict low-risk probing JSON export.",
    )
    return parser.parse_args()


def export_probe_row(row: dict[str, Any], root_category: str) -> dict[str, Any]:
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
        "review_pass": row.get("review_pass", ""),
        "review_status": row.get("review_status", ""),
        "review_flags": row.get("review_flags", []),
    }


def build_stats(rows: list[dict[str, Any]], root_category: str) -> dict[str, Any]:
    template_counts = Counter(row.get("template", "") for row in rows)
    roots = {row.get("root", "") for row in rows}
    return {
        "total_real_roots": len(roots),
        "total_nonce_roots": 0,
        "with_affix_real": sum(1 for row in rows if row.get("has_affix")),
        "with_affix_nonce": 0,
        "root_category_counts": {"real": {root_category: len(rows)}, "nonce": {}},
        "templates_used": {
            "real": {
                template: {"type": "audited_abw_low_risk", "count": count}
                for template, count in sorted(template_counts.items())
            },
            "nonce": {},
        },
    }


def row_flags(row: dict[str, Any]) -> list[str]:
    flags: list[str] = []
    template = str(row.get("template", ""))
    morph_class = str(row.get("morph_class", ""))
    ambiguity = int(row.get("camel_ambiguity") or 0)
    analysis = row.get("camel_analysis") or {}
    source = str(analysis.get("source", ""))
    gloss = str(analysis.get("gloss", "")).lower()
    lex = str(analysis.get("lex", ""))
    sentence = str(row.get("example_sentence") or row.get("sentence") or "")
    full_form = str(row.get("full_form", ""))
    base = str(row.get("base_form", ""))

    if ambiguity > HIGH_AMBIGUITY:
        flags.append("high_camel_ambiguity")
    elif ambiguity > MEDIUM_AMBIGUITY:
        flags.append("medium_camel_ambiguity")

    if template in REVIEW_TEMPLATES:
        flags.append("template_needs_semantic_review")
    if template in SMALL_CLASS_TEMPLATES:
        flags.append("small_or_missing_template_class")
    if template in ABSTRACT_NOUN_TEMPLATES:
        flags.append("abstract_or_lexicalized_noun_needs_context_check")
    if template in BROKEN_PLURAL_TEMPLATES:
        flags.append("broken_plural_needs_singular_plural_context_check")
    if source == "spvar":
        flags.append("camel_spvar_analysis")

    if any(token in gloss for token in ["proper", "name", "nationality"]):
        flags.append("possible_name_or_nationality_gloss")
    if "country" in gloss and base != "بلاد":
        flags.append("possible_place_or_country_gloss")

    # CAMEL sometimes chooses a homographic lexeme even when the sentence supports
    # the intended surface form. Keep these rows, but force explicit review.
    if base == "دراسة" and "threshing_machine" in gloss:
        flags.append("camel_wrong_homograph_reading")
    if base == "مبتكر" and "invention" in gloss and full_form != "مبتكر":
        flags.append("camel_wrong_homograph_reading")

    if morph_class == "target_active_participle" and full_form in sentence:
        for marker in [" لصالح ", "للصالح", "صالح العام"]:
            if marker in sentence:
                flags.append("lexicalized_expression_context")

    if lex and base and norm_lexical(base) not in norm_lexical(lex) and template not in BROKEN_PLURAL_TEMPLATES:
        flags.append("camel_lex_differs_from_base")

    return sorted(set(flags))


def review_status(flags: list[str]) -> str:
    high_flags = {
        "possible_name_or_nationality_gloss",
        "possible_place_or_country_gloss",
        "lexicalized_expression_context",
        "camel_wrong_homograph_reading",
    }
    medium_flags = {
        "high_camel_ambiguity",
        "medium_camel_ambiguity",
        "small_or_missing_template_class",
        "camel_lex_differs_from_base",
    }
    if high_flags.intersection(flags):
        return "review_high"
    if medium_flags.intersection(flags):
        return "review_medium"
    return "accept_low_risk"


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "review_status",
        "review_flags",
        "template",
        "morph_class",
        "root",
        "base_form",
        "full_form",
        "prefix",
        "suffix",
        "has_affix",
        "camel_ambiguity",
        "camel_pos",
        "camel_lex",
        "camel_gloss",
        "sentence",
        "url",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
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
                    "has_affix": row.get("has_affix", ""),
                    "camel_ambiguity": row.get("camel_ambiguity", ""),
                    "camel_pos": analysis.get("pos", ""),
                    "camel_lex": analysis.get("lex", ""),
                    "camel_gloss": analysis.get("gloss", ""),
                    "sentence": row.get("example_sentence", ""),
                    "url": row.get("example_url", ""),
                }
            )


def write_probe_json(path: Path, rows: list[dict[str, Any]], root_category: str) -> None:
    probe_rows = [export_probe_row(row, root_category) for row in rows]
    payload = {
        "corpus_stats": build_stats(probe_rows, root_category),
        "real_roots": probe_rows,
        "nonce_roots": [],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def write_markdown_report(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Curated Dataset Review Pass 001",
        "",
        "This is a second-pass audit over the current accepted Almasryalyoum pilot rows.",
        "It does not declare the full dataset finished; it separates immediately usable low-risk rows from rows that need item-level review before final experiments.",
        "",
        "## Counts",
        "",
        f"- Input rows: {report['n_input']}",
        f"- Low-risk accepted rows: {report['n_low_risk']}",
        f"- Review queue rows: {report['n_review_queue']}",
        "",
        "## Review Status",
        "",
    ]
    for status, count in report["by_review_status"].items():
        lines.append(f"- {status}: {count}")
    lines.extend(["", "## Template Counts In Low-Risk Rows", ""])
    for template, count in report["low_risk_by_template"].items():
        lines.append(f"- {template}: {count}")
    lines.extend(["", "## Most Common Review Flags", ""])
    for flag, count in report["by_review_flag"].items():
        lines.append(f"- {flag}: {count}")
    lines.extend(
        [
            "",
            "## Judgment",
            "",
            "The current pilot is good enough to keep as a validated pipeline proof, but not enough to call the final dataset complete.",
            "The low-risk export can be used for smoke-test probing. The review queue should be audited item by item, especially the broken-plural, abstract-noun, intensive-adjective, and instrument-noun rows.",
            "The next data-generation step should still be multi-source expansion from ABW, not relaxing the filters.",
            "",
            "Recommended next sources: Alittihad, Alqabas, Ryiadh, Sabanews, Techreen.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    reviewed: list[dict[str, Any]] = []
    for row in read_jsonl(args.input):
        row = dict(row)
        flags = row_flags(row)
        row["review_pass"] = "review_pass_001"
        row["review_flags"] = flags
        row["review_status"] = review_status(flags)
        reviewed.append(row)

    low_risk = [row for row in reviewed if row["review_status"] == "accept_low_risk"]
    review_queue = [row for row in reviewed if row["review_status"] != "accept_low_risk"]

    write_jsonl(args.out_dir / "all_reviewed_rows.jsonl", reviewed)
    write_jsonl(args.out_dir / "low_risk_accepts.jsonl", low_risk)
    write_jsonl(args.out_dir / "review_queue.jsonl", review_queue)
    write_csv(args.out_dir / "review_queue.csv", review_queue)
    write_csv(args.out_dir / "all_reviewed_rows.csv", reviewed)
    write_probe_json(args.out_dir / "productivity_dataset_low_risk.json", low_risk, args.root_category)

    flag_counts = Counter(flag for row in reviewed for flag in row["review_flags"])
    report = {
        "input": str(args.input),
        "n_input": len(reviewed),
        "n_low_risk": len(low_risk),
        "n_review_queue": len(review_queue),
        "by_review_status": dict(Counter(row["review_status"] for row in reviewed)),
        "by_review_flag": dict(flag_counts.most_common()),
        "input_by_template": dict(Counter(row.get("template", "") for row in reviewed)),
        "low_risk_by_template": dict(Counter(row.get("template", "") for row in low_risk)),
        "review_queue_by_template": dict(Counter(row.get("template", "") for row in review_queue)),
        "outputs": {
            "all_reviewed_rows": str(args.out_dir / "all_reviewed_rows.jsonl"),
            "low_risk_accepts": str(args.out_dir / "low_risk_accepts.jsonl"),
            "review_queue": str(args.out_dir / "review_queue.jsonl"),
            "review_queue_csv": str(args.out_dir / "review_queue.csv"),
            "low_risk_probe_json": str(args.out_dir / "productivity_dataset_low_risk.json"),
        },
    }
    (args.out_dir / "review_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    write_markdown_report(args.out_dir / "review_report.md", report)

    print(f"wrote {args.out_dir / 'all_reviewed_rows.jsonl'}")
    print(f"wrote {args.out_dir / 'low_risk_accepts.jsonl'}")
    print(f"wrote {args.out_dir / 'review_queue.jsonl'}")
    print(f"wrote {args.out_dir / 'review_queue.csv'}")
    print(f"wrote {args.out_dir / 'productivity_dataset_low_risk.json'}")
    print(f"rows={len(reviewed)} low_risk={len(low_risk)} review_queue={len(review_queue)}")


if __name__ == "__main__":
    main()
