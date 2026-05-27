#!/usr/bin/env python3
"""Summarize and gate Arabic Billion Words source-expansion runs.

The purpose is not to certify final linguistic quality. It answers the earlier
question: after sampling more HF/ABW subsets, which sources are worth merging
and what coverage problem do they solve?
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from common import read_jsonl


WEAK_TEMPLATES = {"فعلان", "مفعال"}
DEFAULT_SOURCE_DIR = "sources"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, help="Multi-source run dir, e.g. data_generation/runs/abw_multisource_v1")
    parser.add_argument(
        "--source-run",
        action="append",
        default=[],
        metavar="NAME=PATH",
        help="Add a source run manually. Useful for the pilot: Almasryalyoum=data_generation/runs/abw_10k_broad",
    )
    parser.add_argument("--current-reviewed-json", type=Path, help="Current reviewed probing JSON used as baseline coverage.")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--markdown", type=Path)
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def parse_source_run(value: str) -> tuple[str, Path]:
    if "=" not in value:
        raise ValueError(f"--source-run must be NAME=PATH, got {value!r}")
    name, path = value.split("=", 1)
    if not name:
        raise ValueError(f"Missing source name in --source-run {value!r}")
    return name, Path(path)


def discover_sources(args: argparse.Namespace) -> dict[str, Path]:
    sources: dict[str, Path] = {}
    if args.run_dir:
        source_dir = args.run_dir / DEFAULT_SOURCE_DIR
        if source_dir.exists():
            for path in sorted(source_dir.iterdir()):
                if path.is_dir():
                    sources[path.name] = path
    for value in args.source_run:
        name, path = parse_source_run(value)
        sources[name] = path
    return sources


def summarize_type_rows(type_path: Path) -> dict[str, Any]:
    if not type_path.exists():
        return {
            "n_type_rows_from_file": 0,
            "roots_by_template": {},
            "unique_roots": 0,
            "family_ready_count": 0,
            "family_ready_by_template": {},
        }

    rows = list(read_jsonl(type_path))
    roots_by_template: dict[str, set[str]] = defaultdict(set)
    family_rows: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        template = str(row.get("template", ""))
        root = str(row.get("root", ""))
        base = str(row.get("base_form") or row.get("canonical_base_form") or "")
        roots_by_template[template].add(root)
        family_rows[(template, root, base)].append(row)

    family_ready_by_template: Counter[str] = Counter()
    for (template, _root, _base), family in family_rows.items():
        has_base = any(not row.get("has_affix") for row in family)
        affixed_forms = {
            (
                str(row.get("full_form", "")),
                str(row.get("prefix", "")),
                str(row.get("suffix", "")),
            )
            for row in family
            if row.get("has_affix")
        }
        if has_base and len(affixed_forms) >= 2:
            family_ready_by_template[template] += 1

    return {
        "n_type_rows_from_file": len(rows),
        "roots_by_template": {template: len(roots) for template, roots in sorted(roots_by_template.items())},
        "unique_roots": len({row.get("root", "") for row in rows}),
        "family_ready_count": sum(family_ready_by_template.values()),
        "family_ready_by_template": dict(sorted(family_ready_by_template.items())),
    }


def summarize_source(name: str, path: Path) -> dict[str, Any]:
    extraction = load_json(path / "extraction_report.json")
    view = load_json(path / "views" / "view_report.json")
    type_summary = summarize_type_rows(path / "views" / "type_level.jsonl")

    by_template_type = view.get("by_template_type", {})
    weak_counts = {template: int(by_template_type.get(template, 0)) for template in sorted(WEAK_TEMPLATES)}
    n_type_rows = int(view.get("n_type_rows") or type_summary["n_type_rows_from_file"] or 0)
    n_token_rows = int(view.get("n_token_rows") or extraction.get("counters", {}).get("candidates", 0) or 0)
    n_sentences = int(extraction.get("counters", {}).get("sentences", 0) or 0)
    n_templates = len([template for template, count in by_template_type.items() if count])

    gates: list[str] = []
    if n_type_rows == 0:
        gates.append("missing_or_empty_type_view")
    if n_templates < 8 and n_type_rows:
        gates.append("low_template_diversity")
    if sum(weak_counts.values()) == 0:
        gates.append("adds_no_weak_template_types")
    if type_summary["family_ready_count"] == 0:
        gates.append("adds_no_family_ready_groups")
    if n_sentences and n_token_rows / max(n_sentences, 1) > 8:
        gates.append("very_dense_candidate_extraction_check_noise")

    if n_type_rows == 0:
        recommendation = "not_ready"
    elif sum(weak_counts.values()) > 0 or type_summary["family_ready_count"] > 0:
        recommendation = "merge_candidate_pool_after_audit"
    else:
        recommendation = "low_priority_source"

    return {
        "source": name,
        "path": str(path),
        "recommendation": recommendation,
        "gates": gates,
        "sentences": n_sentences,
        "token_rows": n_token_rows,
        "type_rows": n_type_rows,
        "templates_with_types": n_templates,
        "by_template_type": by_template_type,
        "weak_template_type_rows": weak_counts,
        **type_summary,
    }


def summarize_current_reviewed(path: Path | None) -> dict[str, Any]:
    if not path or not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("real_roots", [])
    by_template = Counter(row.get("template", "") for row in rows)
    roots_by_template: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        roots_by_template[str(row.get("template", ""))].add(str(row.get("root", "")))
    return {
        "path": str(path),
        "rows": len(rows),
        "roots": len({row.get("root", "") for row in rows}),
        "templates": len(by_template),
        "by_template": dict(sorted(by_template.items())),
        "roots_by_template": {template: len(roots) for template, roots in sorted(roots_by_template.items())},
        "missing_templates": sorted(template for template in WEAK_TEMPLATES if by_template.get(template, 0) == 0),
    }


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Source Expansion Summary",
        "",
        "This report checks whether sampled ABW/HF sources are useful for the final morphology dataset.",
        "It is a coverage and audit-prioritization report, not a final linguistic acceptance decision.",
        "",
    ]
    baseline = report.get("current_reviewed_baseline") or {}
    if baseline:
        lines.extend(
            [
                "## Current Reviewed Baseline",
                "",
                f"- Path: `{baseline['path']}`",
                f"- Rows: {baseline['rows']}",
                f"- Roots: {baseline['roots']}",
                f"- Templates: {baseline['templates']}",
                f"- Missing weak templates: {', '.join(baseline['missing_templates']) or 'none'}",
                "",
            ]
        )

    lines.extend(["## Sources", ""])
    for source in report["sources"]:
        weak = source["weak_template_type_rows"]
        lines.extend(
            [
                f"### {source['source']}",
                "",
                f"- Recommendation: `{source['recommendation']}`",
                f"- Type rows: {source['type_rows']}",
                f"- Token rows: {source['token_rows']}",
                f"- Unique roots: {source['unique_roots']}",
                f"- Templates with types: {source['templates_with_types']}",
                f"- Family-ready groups: {source['family_ready_count']}",
                f"- Weak-template type rows: فعلان={weak.get('فعلان', 0)}, مفعال={weak.get('مفعال', 0)}",
                f"- Gates: {', '.join(source['gates']) or 'none'}",
                "",
            ]
        )

    lines.extend(
        [
            "## Decision Rule",
            "",
            "Prioritize sources that add weak templates, add family-ready groups, or substantially increase clean root/template coverage.",
            "Do not relax the linguistic audit just to increase counts; merge candidates first, then rerun audit preparation, curated selection, second-pass review, and explicit decisions.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    sources = discover_sources(args)
    report = {
        "run_dir": str(args.run_dir) if args.run_dir else "",
        "current_reviewed_baseline": summarize_current_reviewed(args.current_reviewed_json),
        "sources": [summarize_source(name, path) for name, path in sorted(sources.items())],
    }
    report["summary"] = {
        "n_sources": len(report["sources"]),
        "sources_ready_for_merge": [
            source["source"]
            for source in report["sources"]
            if source["recommendation"] == "merge_candidate_pool_after_audit"
        ],
        "sources_not_ready": [
            source["source"]
            for source in report["sources"]
            if source["recommendation"] == "not_ready"
        ],
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    if args.markdown:
        write_markdown(args.markdown, report)

    print(f"wrote {args.output}")
    if args.markdown:
        print(f"wrote {args.markdown}")
    print(
        "sources="
        f"{len(report['sources'])} ready_for_merge={len(report['summary']['sources_ready_for_merge'])} "
        f"not_ready={len(report['summary']['sources_not_ready'])}"
    )


if __name__ == "__main__":
    main()
