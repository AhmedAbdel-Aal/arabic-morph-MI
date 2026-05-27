#!/usr/bin/env python3
"""Build the natural-only almost-100-example probing dataset."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


TARGET_PER_TEMPLATE = 100
TEMPLATES = [
    "استفعل",
    "افتعال",
    "انفعل",
    "فاعل",
    "فعال",
    "فعالة",
    "فعلاء",
    "فعول",
    "فعيل",
    "مفتعل",
    "مفعول",
]

DEFAULT_V2 = Path(
    "data_generation/runs/abw_multisource_v2/audit_v1/review_pass_001/"
    "decision_applied_001/productivity_dataset_reviewed.json"
)
DEFAULT_AMINA = Path("data_generation/runs/amina_v1/audit_v1/review_pass_001/low_risk_accepts.jsonl")
DEFAULT_SANAD = Path("data_generation/runs/sanad_v1/audit_v1/review_pass_001/low_risk_accepts.jsonl")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def read_probe_json(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    return list(payload.get("real_roots", []))


def source_dataset(row: dict[str, Any]) -> str:
    return str(row.get("source_dataset") or row.get("example_source_dataset") or "")


def source(row: dict[str, Any]) -> str:
    return str(row.get("source") or row.get("example_source") or "")


def sentence(row: dict[str, Any]) -> str:
    return str(row.get("sentence") or row.get("example_sentence") or "")


def url(row: dict[str, Any]) -> str:
    return str(row.get("url") or row.get("example_url") or "")


def normalize_row(row: dict[str, Any], root_category: str) -> dict[str, Any]:
    src = source_dataset(row)
    if src.startswith("controlled_manual"):
        raise ValueError(f"Controlled row leaked into natural builder: {row}")
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
        "source_dataset": src,
        "source_datasets": row.get("source_datasets", [src] if src else []),
        "source": source(row),
        "url": url(row),
        "sentence": sentence(row),
        "camel_ambiguity": row.get("camel_ambiguity", ""),
        "camel_analysis": row.get("camel_analysis", {}),
        "audit_decision": row.get("audit_decision", ""),
        "audit_reason": row.get("audit_reason", ""),
        "audit_notes": row.get("audit_notes", ""),
        "review_status": row.get("review_status", ""),
        "review_pass": row.get("review_pass", ""),
        "review_flags": row.get("review_flags", []),
    }


def dedupe_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: dict[tuple[str, str, str, str, str, str, str], dict[str, Any]] = {}
    for row in rows:
        key = (
            str(row.get("template", "")),
            str(row.get("root", "")),
            str(row.get("base_form", "")),
            str(row.get("full_form", "")),
            str(row.get("prefix", "")),
            str(row.get("suffix", "")),
            str(row.get("source_dataset", "")),
        )
        if key not in deduped:
            deduped[key] = row
    return list(deduped.values())


def row_sort_key(row: dict[str, Any]) -> tuple[int, str, str, str, str]:
    # Prefer rows that have an explicit sentence and lower CAMEL ambiguity.
    ambiguity = row.get("camel_ambiguity")
    try:
        ambiguity_int = int(ambiguity)
    except (TypeError, ValueError):
        ambiguity_int = 999
    return (
        0 if row.get("sentence") else 1,
        ambiguity_int,
        str(row.get("source_dataset", "")),
        str(row.get("base_form", "")),
        str(row.get("full_form", "")),
    )


def round_robin_select(rows: list[dict[str, Any]], target: int) -> list[dict[str, Any]]:
    if len(rows) <= target:
        return sorted(rows, key=row_sort_key)

    # First pass: maximize unique full forms.
    full_form_buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in sorted(rows, key=row_sort_key):
        full_form_buckets[str(row.get("full_form", ""))].append(row)

    selected: list[dict[str, Any]] = []
    used_ids: set[int] = set()
    for full_form in sorted(full_form_buckets):
        row = full_form_buckets[full_form][0]
        selected.append(row)
        used_ids.add(id(row))
        if len(selected) == target:
            return selected

    # Second pass: fill with extra contexts, balanced across source datasets.
    source_buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in sorted(rows, key=row_sort_key):
        if id(row) not in used_ids:
            source_buckets[str(row.get("source_dataset", ""))].append(row)

    while len(selected) < target:
        progressed = False
        for src in sorted(source_buckets):
            bucket = source_buckets[src]
            if not bucket:
                continue
            row = bucket.pop(0)
            selected.append(row)
            progressed = True
            if len(selected) == target:
                break
        if not progressed:
            break
    return selected


def build_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    template_counts = Counter(row.get("template", "") for row in rows)
    root_category_counts = Counter(row.get("root_category", "") for row in rows)
    return {
        "total_real_roots": len({row.get("root", "") for row in rows}),
        "total_nonce_roots": 0,
        "with_affix_real": sum(1 for row in rows if row.get("has_affix")),
        "with_affix_nonce": 0,
        "root_category_counts": {"real": dict(root_category_counts), "nonce": {}},
        "templates_used": {
            "real": {
                template: {"type": "natural_corpus_reviewed", "count": count}
                for template, count in sorted(template_counts.items())
            },
            "nonce": {},
        },
    }


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--v2-json", type=Path, default=DEFAULT_V2)
    parser.add_argument("--amina-low-risk", type=Path, default=DEFAULT_AMINA)
    parser.add_argument("--sanad-low-risk", type=Path, default=DEFAULT_SANAD)
    parser.add_argument("--out-dir", type=Path, default=Path("data_generation/runs/natural_almost100_v1"))
    parser.add_argument("--target-per-template", type=int, default=TARGET_PER_TEMPLATE)
    parser.add_argument("--root-category", default="natural_hf_news_almost100_v1")
    args = parser.parse_args()

    raw_rows = []
    raw_rows.extend(read_probe_json(args.v2_json))
    raw_rows.extend(read_jsonl(args.amina_low_risk))
    raw_rows.extend(read_jsonl(args.sanad_low_risk))

    rows = [
        normalize_row(row, args.root_category)
        for row in raw_rows
        if row.get("template") in set(TEMPLATES) and not source_dataset(row).startswith("controlled_manual")
    ]
    rows = dedupe_rows(rows)

    by_template: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_template[str(row.get("template", ""))].append(row)

    selected: list[dict[str, Any]] = []
    for template in TEMPLATES:
        selected.extend(round_robin_select(by_template[template], args.target_per_template))

    payload = {
        "corpus_stats": build_stats(selected),
        "real_roots": selected,
        "nonce_roots": [],
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    output = args.out_dir / "productivity_dataset_natural_almost100.json"
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    write_jsonl(args.out_dir / "selected_rows.jsonl", selected)

    report = {
        "target_per_template": args.target_per_template,
        "inputs": {
            "v2_json": str(args.v2_json),
            "amina_low_risk": str(args.amina_low_risk),
            "sanad_low_risk": str(args.sanad_low_risk),
        },
        "n_raw_input_rows": len(raw_rows),
        "n_candidate_rows_after_template_filter": len(rows),
        "n_selected_rows": len(selected),
        "selected_by_template": Counter(row["template"] for row in selected),
        "selected_by_source_dataset": Counter(row["source_dataset"] for row in selected),
        "unique_full_forms_by_template": {
            template: len({row["full_form"] for row in selected if row["template"] == template})
            for template in TEMPLATES
        },
        "unique_base_forms_by_template": {
            template: len({row["base_form"] for row in selected if row["template"] == template})
            for template in TEMPLATES
        },
        "with_affix_by_template": {
            template: sum(1 for row in selected if row["template"] == template and row["has_affix"])
            for template in TEMPLATES
        },
        "roots": len({row["root"] for row in selected}),
        "templates": len({row["template"] for row in selected}),
        "nonce_rows": 0,
    }
    (args.out_dir / "natural_almost100_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (args.out_dir / "README.md").write_text(
        "\n".join(
            [
                "# Natural Almost100 v1",
                "",
                "Natural-only corpus dataset for representation probing.",
                "",
                "Main file:",
                "",
                "```text",
                str(output),
                "```",
                "",
                "Composition:",
                "",
                "```text",
                f"rows: {len(selected)}",
                f"templates: {len({row['template'] for row in selected})}",
                f"target cap per template: {args.target_per_template}",
                "nonce rows: 0",
                "synthetic rows: 0",
                "```",
                "",
                "The file combines reviewed ABW/HF v2 rows with AMINA and SANAD low-risk rows. Templates with more than 100 available rows are capped at 100; templates below 100 keep all available low-risk rows.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    print(f"wrote {output}")
    print(f"rows={len(selected)} templates={report['templates']} roots={report['roots']}")
    print("by_template")
    for template, count in sorted(report["selected_by_template"].items()):
        print(f"{template}\t{count}")


if __name__ == "__main__":
    main()
