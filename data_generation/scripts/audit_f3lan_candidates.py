#!/usr/bin/env python3
"""Focused audit for the unresolved `فعلان` coverage gap."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


MANUAL_ADJ_DECISIONS = {
    "البركاني": (
        "reject",
        "proper_name_or_nisba",
        "Context is Sultan al-Barkani; surface is nisba/proper-name use, not a clean `فعلان` adjective.",
    ),
    "البستاني": (
        "reject",
        "proper_name_or_nisba",
        "Context is the Boustani family/name; nisba/surname use, not target `فعلان` morphology.",
    ),
    "بستاني": (
        "reject",
        "proper_name_or_nisba",
        "Context is a surname/name mention; not a clean target adjective.",
    ),
    "لبستاني": (
        "reject",
        "proper_name_or_nisba",
        "Context is a Boustani name/family mention; not a clean target adjective.",
    ),
    "زعلانين": (
        "reject",
        "dialect_or_register",
        "Valid colloquial adjective form, but context is Egyptian colloquial; exclude from MSA target set.",
    ),
    "السرطاني": (
        "reject",
        "nisba_not_f3lan",
        "Surface is nisba `سرطاني` from `سرطان`, not the target `فعلان` adjective itself.",
    ),
    "الرحمان": (
        "reject",
        "proper_name_or_lexicalized_epithet",
        "Observed context is the proper name `عبد الرحمان`; not a clean target adjective use.",
    ),
    "الشرهان": (
        "reject",
        "proper_name",
        "Context is a person name; CAMEL reading as adjective/dual is not the intended token.",
    ),
    "الشعراني": (
        "reject",
        "proper_name_or_nisba",
        "Context is a person name; not a target adjective use.",
    ),
    "شعراني": (
        "reject",
        "proper_name_or_nisba",
        "Context is a person name; not a target adjective use.",
    ),
    "عجلان": (
        "reject",
        "proper_name",
        "Context is the person name Muhammad Ajlan; not a target adjective use.",
    ),
    "العقلاني": (
        "reject",
        "nisba_not_f3lan",
        "Surface is nisba/adjectival `عقلاني`; useful maybe for another class, but not `فعلان`.",
    ),
    "عقلاني": (
        "reject",
        "nisba_not_f3lan",
        "Surface is nisba/adjectival `عقلاني`; useful maybe for another class, but not `فعلان`.",
    ),
    "العلماني": (
        "reject",
        "nisba_not_f3lan",
        "Surface is nisba/adjectival `علماني`; useful maybe for another class, but not `فعلان`.",
    ),
    "علماني": (
        "reject",
        "nisba_not_f3lan",
        "Surface is nisba/adjectival `علماني`; useful maybe for another class, but not `فعلان`.",
    ),
    "العمراني": (
        "reject",
        "nisba_not_f3lan",
        "Surface is nisba/adjectival `عمراني`; useful maybe for another class, but not `فعلان`.",
    ),
    "عمراني": (
        "reject",
        "nisba_not_f3lan",
        "Surface is nisba/adjectival `عمراني`; useful maybe for another class, but not `فعلان`.",
    ),
    "فرحان": (
        "reject",
        "proper_name",
        "Context is an Iraqi player's given/family name; not target adjective use.",
    ),
    "لفرحان": (
        "reject",
        "proper_name",
        "Context is a player/person name with prefixed preposition; not target adjective use.",
    ),
    "وفرحان": (
        "reject",
        "dialect_or_register",
        "Adjectival use is plausible, but sentence is colloquial Egyptian; exclude from MSA target set.",
    ),
    "الفردان": (
        "reject",
        "proper_name_or_place",
        "Observed contexts are person/place names; not clean target adjective use.",
    ),
    "فردان": (
        "reject",
        "proper_name_or_place",
        "Observed context is Beirut neighborhood/place name; not clean target adjective use.",
    ),
    "المرجاني": (
        "reject",
        "nisba_not_f3lan",
        "Surface is nisba/adjectival `مرجاني`, not target `فعلان`.",
    ),
    "نبهان": (
        "reject",
        "proper_name",
        "Context is a person name; CAMEL dual/adjective reading is not the intended token.",
    ),
    "النعسان": (
        "reject",
        "proper_name_or_place",
        "Context is `دار النعسان`, likely name/place; not a clean adjective use.",
    ),
    "البحراني": (
        "reject",
        "proper_name_or_nisba",
        "Context is artist Ahmad al-Bahrani; nisba/proper-name use.",
    ),
    "جدعان": (
        "reject",
        "proper_name",
        "Context is a person name; not a target adjective use.",
    ),
    "خسران": (
        "reject",
        "lexical_nominal",
        "Context means loss/damage as a nominal/verbal-noun reading, not target adjective use.",
    ),
    "العثماني": (
        "reject",
        "nisba_not_f3lan",
        "Historical nisba adjective `Ottoman`; not target `فعلان`.",
    ),
    "عثماني": (
        "reject",
        "proper_name_or_nisba",
        "Observed contexts are either nisba `Ottoman` or person-name use; not target `فعلان`.",
    ),
    "لعثماني": (
        "reject",
        "proper_name_or_nisba",
        "Person-name/nisba use with prefixed preposition; not target `فعلان`.",
    ),
    "وعثماني": (
        "reject",
        "proper_name_or_nisba",
        "Person-name/nisba use with prefixed conjunction; not target `فعلان`.",
    ),
    "الفلتان": (
        "reject",
        "lexical_nominal",
        "Context is lexical noun `chaos/recklessness`; not target adjective use.",
    ),
    "فلتان": (
        "reject",
        "lexical_nominal",
        "Context is lexical noun `chaos/recklessness`; not target adjective use.",
    ),
    "والفلتان": (
        "reject",
        "lexical_nominal",
        "Context is lexical noun `chaos/recklessness`; not target adjective use.",
    ),
    "لبناني": (
        "reject",
        "nisba_not_f3lan",
        "Lebanese nisba adjective; not target `فعلان`, and CAMEL selected a false verb analysis.",
    ),
    "لثماني": (
        "reject",
        "false_analysis",
        "Surface is numeral/prepositional phrase `لثماني`; not a `فعلان` item.",
    ),
}


def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def classify(row: dict) -> tuple[str, str, str]:
    full_form = row.get("full_form", "")
    if full_form in MANUAL_ADJ_DECISIONS:
        return MANUAL_ADJ_DECISIONS[full_form]

    pos = row.get("pos")
    if pos == "noun":
        return (
            "reject",
            "not_target_pos_noun",
            "Systematic exclusion: noun row, not a clean `فعلان` adjective target.",
        )
    if pos == "verb":
        return (
            "reject",
            "not_target_pos_verb",
            "Systematic exclusion: verb row, not a clean `فعلان` adjective target.",
        )
    return (
        "needs_manual_review",
        "unclassified",
        "No focused `فعلان` decision was available for this row.",
    )


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(path: Path, rows: list[dict]) -> None:
    fieldnames = [
        "decision",
        "decision_category",
        "reason",
        "base_form",
        "full_form",
        "root",
        "pos",
        "suggested_dataset_use",
        "suggested_morph_class",
        "camel_ambiguity",
        "camel_lex",
        "camel_gloss",
        "camel_pattern",
        "example_source_dataset",
        "example_sentence",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in fieldnames})


def build_report(rows: list[dict], audited_rows: list[dict]) -> str:
    counts = Counter(row["decision"] for row in audited_rows)
    categories = Counter(row["decision_category"] for row in audited_rows)
    pos_counts = Counter(row.get("pos") for row in rows)
    use_counts = Counter(row.get("suggested_dataset_use") for row in rows)
    morph_counts = Counter(row.get("suggested_morph_class") for row in rows)
    sources = Counter(row.get("example_source_dataset") for row in rows)
    top_bases = Counter(row.get("base_form") for row in rows).most_common(30)

    lines = [
        "# Focused فعلان Audit",
        "",
        "This audit checks whether the combined multi-source candidate pool contains clean `فعلان` items suitable for the main MSA morphology probing dataset.",
        "",
        "## Input",
        "",
        "```text",
        f"فعلان type rows: {len(rows)}",
        f"pos distribution: {dict(pos_counts)}",
        f"suggested use: {dict(use_counts)}",
        f"suggested morph class: {dict(morph_counts)}",
        f"sources: {dict(sources)}",
        "```",
        "",
        "Top base forms:",
        "",
        "```text",
    ]
    lines.extend(f"{base}: {count}" for base, count in top_bases)
    lines.extend(
        [
            "```",
            "",
            "## Decision",
            "",
            "```text",
            f"decision counts: {dict(counts)}",
            f"rejection categories: {dict(categories)}",
            "```",
            "",
            "No `فعلان` row is accepted into the main target dataset in this pass.",
            "",
            "The apparent candidates are dominated by:",
            "",
            "- nisba/adjectival forms ending in `-ي`, such as `عقلاني`, `عمراني`, `علماني`, and `مرجاني`; these are not the target `فعلان` form.",
            "- proper names and places, such as `عجلان`, `فرحان`, `الفردان`, `نبهان`, and `دار النعسان`.",
            "- lexical nouns or nominal readings, such as `فلتان` and `خسران`.",
            "- colloquial-register rows such as `زعلانين` and `وفرحان`, which are not appropriate for a strict MSA target set.",
            "- plural/dual or analysis artifacts such as `بلدان`, `جدران`, `جدعان`, and `لثماني`.",
            "",
            "## Scientific Judgment",
            "",
            "Do not force `فعلان` into the reviewed dataset from this source pool. The raw pool contains many strings that match the surface shape, but the context-level audit shows they are not clean MSA target examples for our current probe design.",
            "",
            "The right next step is either targeted source expansion or a separate controlled construction pass for `فعلان`, with explicit manual validation. The current reviewed dataset remains usable as a clean 12-template interim set, but it should not be described as covering all planned templates.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data_generation/runs/abw_multisource_v1/audit_v1/type_level_audit_prep.jsonl"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data_generation/runs/abw_multisource_v1/audit_v1/f3lan_audit"),
    )
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    rows = [row for row in load_jsonl(args.input) if row.get("template") == "فعلان"]
    audited_rows = []
    for row in rows:
        decision, category, reason = classify(row)
        camel = row.get("camel_analysis") or {}
        audited_rows.append(
            {
                **row,
                "decision": decision,
                "decision_category": category,
                "reason": reason,
                "camel_lex": camel.get("lex"),
                "camel_gloss": camel.get("gloss"),
                "camel_pattern": camel.get("pattern"),
            }
        )

    unclassified = [row for row in audited_rows if row["decision"] == "needs_manual_review"]
    if unclassified:
        forms = ", ".join(sorted({row.get("full_form", "") for row in unclassified}))
        raise SystemExit(f"Unclassified فعلان rows remain: {forms}")

    write_jsonl(args.output_dir / "f3lan_audit_decisions.jsonl", audited_rows)
    write_csv(args.output_dir / "f3lan_audit_decisions.csv", audited_rows)
    (args.output_dir / "f3lan_audit_report.md").write_text(
        build_report(rows, audited_rows), encoding="utf-8"
    )

    summary = {
        "input_rows": len(rows),
        "accepted_rows": sum(row["decision"] == "accept" for row in audited_rows),
        "rejected_rows": sum(row["decision"] == "reject" for row in audited_rows),
        "decision_categories": Counter(row["decision_category"] for row in audited_rows),
        "pos_distribution": Counter(row.get("pos") for row in rows),
        "suggested_use_distribution": Counter(row.get("suggested_dataset_use") for row in rows),
        "source_distribution": Counter(row.get("example_source_dataset") for row in rows),
    }
    (args.output_dir / "f3lan_audit_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(f"wrote {args.output_dir}")


if __name__ == "__main__":
    main()
