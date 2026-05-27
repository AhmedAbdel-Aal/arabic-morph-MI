#!/usr/bin/env python3
"""Prepare morphology candidates for item-level audit."""

from __future__ import annotations

import argparse
import json
import random
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from common import read_jsonl, write_jsonl


DERIVED_VERB_TEMPLATES = {"استفعل", "انفعل"}
PARTICIPLE_TEMPLATES = {"فاعل", "مفعول", "مفتعل"}
MASDAR_TEMPLATES = {"افتعال", "فعالة"}
BROKEN_PLURAL_TEMPLATES = {"فعال", "فعول", "فعلاء"}
INTENSIVE_ADJECTIVE_TEMPLATES = {"فعيل", "فعلان"}
INSTRUMENT_TEMPLATES = {"مفعال"}
AMBIGUOUS_NOUN_TEMPLATES = BROKEN_PLURAL_TEMPLATES | INTENSIVE_ADJECTIVE_TEMPLATES | INSTRUMENT_TEMPLATES


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--annotated-output", required=True, type=Path)
    parser.add_argument("--sample-output", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--sample-size", type=int, default=500)
    parser.add_argument("--seed", type=int, default=17)
    return parser.parse_args()


def int_value(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def has_name_or_place_signal(row: dict[str, Any]) -> bool:
    analysis = row.get("camel_analysis") or {}
    english_text = " ".join(
        str(value or "")
        for value in [analysis.get("gloss"), analysis.get("pos")]
    ).lower()
    english_tokens = set(re.findall(r"[a-z_]+", english_text))
    english_signals = {
        "proper",
        "name",
        "nationality",
        "person",
        "proper_name",
    }
    return analysis.get("pos") == "noun_prop" or bool(english_tokens & english_signals)


def add_audit_hints(row: dict[str, Any]) -> dict[str, Any]:
    row = dict(row)
    template = row.get("template", "")
    pos = row.get("pos", "")
    ambiguity = int_value(row.get("camel_ambiguity"))
    analysis = row.get("camel_analysis") or {}

    flags: list[str] = []
    notes: list[str] = []

    if ambiguity >= 10:
        flags.append("high_camel_ambiguity")
        notes.append(f"CAMEL ambiguity is {ambiguity}.")
    elif ambiguity:
        flags.append("camel_analyzed")

    if not analysis:
        flags.append("missing_camel_analysis_in_view")
        notes.append("Type view lacks CAMEL analysis; regenerate views with the updated make_views.py.")

    analysis_pos = analysis.get("pos")
    if analysis_pos and pos and analysis_pos != pos:
        flags.append("camel_pos_mismatch")
        notes.append(f"Pipeline POS is {pos}, but CAMEL selected analysis POS is {analysis_pos}.")

    source = analysis.get("source")
    if source and source not in {"lex", "spvar"}:
        flags.append(f"camel_source_{source}")

    if has_name_or_place_signal(row):
        flags.append("name_or_place_signal")

    suggested_class = "unsure"
    suggested_use = "needs_review"
    bucket = "medium_review"

    if pos == "verb" and template in DERIVED_VERB_TEMPLATES:
        suggested_class = "target_form_x_verb" if template == "استفعل" else "target_form_vii_verb"
        suggested_use = "main_target"
        bucket = "low_review"
        notes.append("Verb in a target derived-verb template; likely main-study item if context agrees.")
    elif pos in {"noun", "adj"} and template == "فاعل":
        suggested_class = "target_active_participle"
        suggested_use = "main_target"
        bucket = "medium_review"
        notes.append("Active-participle template; audit context and root/template correctness.")
    elif pos in {"noun", "adj"} and template == "مفعول":
        suggested_class = "target_passive_participle"
        suggested_use = "main_target"
        bucket = "medium_review"
        notes.append("Passive-participle template; audit context and root/template correctness.")
    elif pos in {"noun", "adj"} and template == "مفتعل":
        suggested_class = "target_form_viii_participle"
        suggested_use = "main_target"
        bucket = "medium_review"
        notes.append("Form VIII participle-like template; audit context and root/template correctness.")
    elif pos == "noun" and template in MASDAR_TEMPLATES:
        suggested_class = "target_verbal_noun"
        suggested_use = "main_target"
        bucket = "medium_review"
        notes.append("Target verbal-noun/masdar template; audit whether it is valid in context.")
    elif pos == "noun" and template in BROKEN_PLURAL_TEMPLATES:
        flags.append("primitive_or_derived_noun_template")
        suggested_class = "unsure"
        suggested_use = "needs_review"
        bucket = "high_review"
        notes.append("Noun in a possible broken-plural template; audit against primitive singular nouns.")
    elif pos == "adj" and template in INTENSIVE_ADJECTIVE_TEMPLATES:
        flags.append("intensive_adjective_template")
        suggested_class = "target_intensive_adjective"
        suggested_use = "main_target"
        bucket = "medium_review"
        notes.append("Target intensive-adjective template; audit context and root/template correctness.")
    elif pos == "noun" and template in INSTRUMENT_TEMPLATES:
        flags.append("instrument_noun_template")
        suggested_class = "target_instrument_noun"
        suggested_use = "main_target"
        bucket = "medium_review"
        notes.append("Target instrument-noun template; audit context and root/template correctness.")
    elif pos == "adj" and template in BROKEN_PLURAL_TEMPLATES:
        flags.append("adjective_in_ambiguous_template")
        suggested_class = "target_intensive_adjective"
        suggested_use = "main_target"
        bucket = "medium_review"
        notes.append("Adjective in a template that can also be broken plural; audit as possible target adjective.")

    if "name_or_place_signal" in flags:
        suggested_class = "proper_name_or_place"
        suggested_use = "exclude"
        bucket = "high_review"
        notes.append("Name/place signal should be checked before inclusion.")

    if "camel_pos_mismatch" in flags:
        suggested_class = "unsure"
        suggested_use = "needs_review"
        bucket = "high_review"

    if "high_camel_ambiguity" in flags and bucket == "low_review":
        bucket = "medium_review"

    row["audit_flags"] = flags
    row["audit_bucket"] = bucket
    row["audit_hint"] = " ".join(notes)
    row["suggested_morph_class"] = suggested_class
    row["suggested_dataset_use"] = suggested_use
    return row


def sample_by_bucket_and_template(rows: list[dict[str, Any]], sample_size: int, seed: int) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[(row.get("audit_bucket", ""), row.get("template", ""))].append(row)

    sampled: list[dict[str, Any]] = []
    seen_keys: set[tuple[str, str, str, str, str, str, str, str, str]] = set()
    for key in sorted(groups):
        group = groups[key]
        take = min(4, len(group))
        for row in rng.sample(group, take):
            sampled.append(dict(row))
            seen_keys.add(row_identity(row))

    targets = allocate_bucket_targets(rows, sample_size)
    for bucket in ["high_review", "medium_review", "low_review"]:
        bucket_rows = [row for row in rows if row.get("audit_bucket") == bucket and row_identity(row) not in seen_keys]
        bucket_rows.sort(
            key=lambda row: (
                -int_value(row.get("camel_ambiguity")),
                row.get("template", ""),
                row.get("full_form", ""),
            )
        )
        current = sum(1 for row in sampled if row.get("audit_bucket") == bucket)
        needed = max(0, targets.get(bucket, 0) - current)
        for row in bucket_rows[:needed]:
            sampled.append(dict(row))
            seen_keys.add(row_identity(row))

    if len(sampled) < sample_size:
        remaining = [row for row in rows if row_identity(row) not in seen_keys]
        rng.shuffle(remaining)
        sampled.extend(dict(row) for row in remaining[: sample_size - len(sampled)])

    if len(sampled) > sample_size:
        sampled = sampled[:sample_size]

    rng.shuffle(sampled)
    for index, row in enumerate(sampled, 1):
        row["audit_id"] = f"audit_{index:04d}"
        row["audit_sample_seed"] = seed
        row["audit_sample_strategy"] = "bucket_template_stratified"
    return sampled


def row_identity(row: dict[str, Any]) -> tuple[str, str, str, str, str, str, str, str, str]:
    return (
        str(row.get("root", "")),
        str(row.get("template", "")),
        str(row.get("base_form", "")),
        str(row.get("canonical_base_form", "")),
        str(row.get("surface_stem", "")),
        str(row.get("prefix", "")),
        str(row.get("suffix", "")),
        str(row.get("full_form", "")),
        str(row.get("surface_rule", "")),
    )


def allocate_bucket_targets(rows: list[dict[str, Any]], sample_size: int) -> dict[str, int]:
    desired = {
        "high_review": round(sample_size * 0.4),
        "medium_review": round(sample_size * 0.4),
        "low_review": sample_size - round(sample_size * 0.4) - round(sample_size * 0.4),
    }
    available = Counter(row.get("audit_bucket", "") for row in rows)
    targets = {bucket: min(count, desired.get(bucket, 0)) for bucket, count in available.items()}
    remaining = sample_size - sum(targets.values())
    while remaining > 0:
        changed = False
        for bucket, count in available.most_common():
            if targets.get(bucket, 0) < count:
                targets[bucket] = targets.get(bucket, 0) + 1
                remaining -= 1
                changed = True
                if remaining == 0:
                    break
        if not changed:
            break
    return targets


def write_report(path: Path, rows: list[dict[str, Any]], sample: list[dict[str, Any]], args: argparse.Namespace) -> None:
    report = {
        "input": str(args.input),
        "annotated_output": str(args.annotated_output),
        "sample_output": str(args.sample_output),
        "n_rows": len(rows),
        "n_sample": len(sample),
        "by_template": dict(Counter(row.get("template", "") for row in rows)),
        "by_pos": dict(Counter(row.get("pos", "") for row in rows)),
        "by_audit_bucket": dict(Counter(row.get("audit_bucket", "") for row in rows)),
        "by_suggested_morph_class": dict(Counter(row.get("suggested_morph_class", "") for row in rows)),
        "by_suggested_dataset_use": dict(Counter(row.get("suggested_dataset_use", "") for row in rows)),
        "sample_by_template": dict(Counter(row.get("template", "") for row in sample)),
        "sample_by_audit_bucket": dict(Counter(row.get("audit_bucket", "") for row in sample)),
        "sample_by_suggested_morph_class": dict(Counter(row.get("suggested_morph_class", "") for row in sample)),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def main() -> None:
    args = parse_args()
    rows = [add_audit_hints(row) for row in read_jsonl(args.input)]
    sample = sample_by_bucket_and_template(rows, args.sample_size, args.seed)
    write_jsonl(args.annotated_output, rows)
    write_jsonl(args.sample_output, sample)
    write_report(args.report, rows, sample, args)
    print(f"wrote {args.annotated_output}")
    print(f"wrote {args.sample_output}")
    print(f"wrote {args.report}")
    print(f"rows={len(rows)} sample={len(sample)}")


if __name__ == "__main__":
    main()
