#!/usr/bin/env python3
"""Build a small controlled, CAMEL-validated فعلان supplement."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from common import compact_camel_analysis, dot_root, infer_template_affix, normalize_root, strip_diacritics, write_jsonl


CONTROLLED_ITEMS = [
    {
        "root": "عطش",
        "base_form": "عطشان",
        "forms": [
            ("عطشان", "عاد الطفل عطشان بعد اللعب في الحديقة."),
            ("العطشان", "شرب الطفل العطشان الماء بعد رحلة طويلة."),
            ("وعطشان", "وصل المسافر متعبا وعطشان بعد السير في الصحراء."),
        ],
    },
    {
        "root": "غضب",
        "base_form": "غضبان",
        "forms": [
            ("غضبان", "بقي المدير غضبان بعد تأخر التقرير."),
            ("الغضبان", "حاول المعلم تهدئة الطالب الغضبان."),
            ("وغضبان", "خرج العامل محبطا وغضبان من الاجتماع."),
        ],
    },
    {
        "root": "سكر",
        "base_form": "سكران",
        "forms": [
            ("سكران", "كان السائق سكران عندما أوقفته الشرطة."),
            ("السكران", "رفض الحارس إدخال الرجل السكران إلى القاعة."),
            ("وسكران", "ظهر الرجل مرتبكا وسكران في الطريق."),
        ],
    },
    {
        "root": "نعس",
        "base_form": "نعسان",
        "forms": [
            ("نعسان", "جلس الحارس نعسان في نهاية المناوبة."),
            ("النعسان", "طلب الطبيب من المريض النعسان أن يستريح."),
            ("ونعسان", "عاد الطفل هادئا ونعسان بعد السفر."),
        ],
    },
    {
        "root": "لهف",
        "base_form": "لهفان",
        "forms": [
            ("لهفان", "وصل الأب لهفان إلى باب المستشفى."),
            ("اللهفان", "طمأن الطبيب الرجل اللهفان على ابنه."),
            ("ولهفان", "ركض الأخ قلقا ولهفان نحو البيت."),
        ],
    },
    {
        "root": "فرح",
        "base_form": "فرحان",
        "forms": [
            ("فرحان", "عاد الطالب فرحان بنجاحه في الامتحان."),
            ("الفرحان", "ابتسم الطفل الفرحان أمام عائلته."),
            ("وفرحان", "خرج اللاعب مطمئنا وفرحان بعد الفوز."),
        ],
    },
]


def load_camel(camel_db: str):
    try:
        from camel_tools.morphology.analyzer import Analyzer
        from camel_tools.morphology.database import MorphologyDB
    except ImportError as exc:
        raise SystemExit("Install and run this in the CAMEL environment: pip install camel-tools") from exc

    db = MorphologyDB.builtin_db(camel_db, flags="a")
    return Analyzer(db, backoff="NONE")


def select_analysis(analyzer: Any, form: str, expected_root: str) -> tuple[dict[str, Any], dict[str, str]]:
    analyses = analyzer.analyze(strip_diacritics(form))
    root_norm = normalize_root(expected_root)
    candidates: list[tuple[int, dict[str, Any], dict[str, str]]] = []
    for analysis in analyses:
        root = normalize_root(analysis.get("root"))
        if root != root_norm:
            continue
        if analysis.get("pos") not in {"adj", "noun"}:
            continue
        matches = [
            match
            for match in infer_template_affix(root, form)
            if match["template"] == "فعلان" and match["canonical_base_form"]
        ]
        for match in matches:
            score = 0
            if analysis.get("pos") == "adj":
                score -= 2
            if normalize_root(analysis.get("lex")) == root_norm:
                score -= 1
            candidates.append((score, analysis, match))
    if not candidates:
        raise ValueError(f"No CAMEL/root/template match for {form} root={expected_root}")
    _score, analysis, match = sorted(candidates, key=lambda item: item[0])[0]
    return analysis, match


def build_rows(camel_db: str) -> list[dict[str, Any]]:
    analyzer = load_camel(camel_db)
    rows: list[dict[str, Any]] = []
    for item in CONTROLLED_ITEMS:
        for index, (form, sentence) in enumerate(item["forms"]):
            analysis, match = select_analysis(analyzer, form, item["root"])
            rows.append(
                {
                    "audit_decision": "accept",
                    "audit_notes": (
                        "Controlled فعلان supplement: manually written MSA context; "
                        "CAMEL root and local root-template matcher agree on فعلان."
                    ),
                    "audit_reason": "controlled_context_valid_camel_validated",
                    "base_form": item["base_form"],
                    "camel_ambiguity": len(analyzer.analyze(strip_diacritics(form))),
                    "camel_analysis": compact_camel_analysis(analysis),
                    "canonical_base_form": item["base_form"],
                    "dataset_use": "main_target",
                    "example_sentence": sentence,
                    "example_source": "controlled_manual",
                    "example_source_dataset": "controlled_manual:f3lan_v1",
                    "example_url": "",
                    "full_form": match["full_form"],
                    "has_affix": bool(match["prefix"] or match["suffix"]),
                    "morph_class": "target_intensive_adjective",
                    "pos": analysis.get("pos"),
                    "prefix": match["prefix"],
                    "review_flags": ["controlled_manual_context", "camel_validated_f3lan"],
                    "review_pass": "controlled_f3lan_v1",
                    "review_status": "accept_manual_controlled",
                    "root": dot_root(item["root"]),
                    "source_datasets": ["controlled_manual:f3lan_v1"],
                    "suffix": match["suffix"],
                    "surface_rule": match["surface_rule"],
                    "surface_stem": match["surface_stem"],
                    "target_text": form,
                    "target_token_index": index,
                    "template": "فعلان",
                }
            )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("data_generation/runs/controlled_f3lan_v1"),
    )
    parser.add_argument("--camel-db", default="calima-msa-r13")
    args = parser.parse_args()

    rows = build_rows(args.camel_db)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.out_dir / "accepted_controlled_f3lan.jsonl", rows)
    report = {
        "n_rows": len(rows),
        "n_roots": len({row["root"] for row in rows}),
        "by_base": Counter(row["base_form"] for row in rows),
        "by_prefix": Counter(row["prefix"] for row in rows),
        "by_pos": Counter(row["pos"] for row in rows),
        "source_dataset": "controlled_manual:f3lan_v1",
        "template": "فعلان",
    }
    (args.out_dir / "controlled_f3lan_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8"
    )
    (args.out_dir / "README.md").write_text(
        "\n".join(
            [
                "# Controlled فعلان Supplement",
                "",
                "This is a small manual supplement for the natural-source `فعلان` gap.",
                "Rows are manually written MSA contexts and are accepted only when CAMEL and the local root-template matcher agree on the expected root and `فعلان` template.",
                "",
                "This file should stay separate from ABW-sourced rows in analysis through `source_dataset=controlled_manual:f3lan_v1`.",
                "",
                "```text",
                f"rows: {len(rows)}",
                f"roots: {len({row['root'] for row in rows})}",
                "forms per family: base + ال-prefixed + و-prefixed",
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(f"wrote {args.out_dir / 'accepted_controlled_f3lan.jsonl'}")
    print(f"rows={len(rows)} roots={report['n_roots']}")


if __name__ == "__main__":
    main()
