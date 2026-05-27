#!/usr/bin/env python3
"""Write explicit reviewer decisions for the v2 Echoroukonline review queue."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


REJECT_OVERRIDES: dict[tuple[str, str, str, str, str, str], tuple[str, str]] = {
    (
        "فاعل",
        "خادم",
        "وخادم",
        "و",
        "",
        "plain",
    ): (
        "lexicalized_honorific_title",
        "Context is `خادم الحرمين`, an official royal title; not a clean ordinary active-participle item.",
    ),
    (
        "فاعل",
        "سابق",
        "فسابقي",
        "ف",
        "ي",
        "plain",
    ): (
        "false_surface_or_analysis",
        "The sentence context does not support a clean `سابق` target item; likely token/analysis artifact.",
    ),
    (
        "فعال",
        "كتاب",
        "لكتاب",
        "ل",
        "",
        "plain",
    ): (
        "singular_book_not_writers",
        "Context is `لكتاب وثقافة الطفل`, i.e. book/culture, not the broken plural `writers`.",
    ),
    (
        "فعال",
        "كتاب",
        "الكتاب",
        "ال",
        "",
        "plain",
    ): (
        "singular_book_not_writers",
        "Context is `صدر كتاب جديد`; not the broken plural `writers`.",
    ),
    (
        "فعيل",
        "شقيق",
        "لشقيقتها",
        "ل",
        "تها",
        "plain",
    ): (
        "kinship_noun_not_target_adjective",
        "Context means `to her sister`; this is a lexical kinship noun use, not the target adjective reading.",
    ),
    (
        "فعيل",
        "صغير",
        "وصغير",
        "و",
        "",
        "plain",
    ): (
        "proper_name_in_context",
        "Context lists person names and includes `وصغير مراد`; not the adjective `small/young`.",
    ),
    (
        "فعيل",
        "كريم",
        "لكريم",
        "ل",
        "",
        "plain",
    ): (
        "proper_name_in_context",
        "Context says the federation will sit with Karim; this is a person name, not an adjective.",
    ),
    (
        "مفعال",
        "مرصاد",
        "بالمرصاد",
        "بال",
        "",
        "plain",
    ): (
        "lexicalized_fixed_expression",
        "Context is the fixed sports expression `كان لها بالمرصاد`; not a clean instrument-noun item.",
    ),
    (
        "مفعال",
        "مفتاح",
        "ومفتاح",
        "و",
        "",
        "plain",
    ): (
        "proper_name_in_context",
        "Context lists absent/suspended players `عبد السلام ومفتاح`; this is a person name.",
    ),
    (
        "مفعول",
        "مجروح",
        "مجروحة",
        "",
        "ة",
        "plain",
    ): (
        "lexicalized_fixed_expression",
        "Context is the idiom `شهادتي فيها مجروحة`; not a clean literal passive-participle item.",
    ),
}


NOTES_BY_TEMPLATE = {
    "استفعل": "Context supports the intended Form X verb reading.",
    "انفعل": "Context supports the intended Form VII verb reading.",
    "افتعال": "Context supports a verbal-noun/masdar reading; ambiguity is from clitics or lexical alternatives.",
    "فاعل": "Context supports an active participle or active-participle-derived noun/adjective reading.",
    "فعال": "Context supports the intended broken-plural/collective nominal reading.",
    "فعالة": "Context supports the intended abstract/verbal-noun reading.",
    "فعلاء": "Context supports the intended broken-plural reading.",
    "فعول": "Context supports the intended broken-plural or collective nominal reading.",
    "فعيل": "Context supports the intended adjective/intensive-adjective reading.",
    "مفتعل": "Context supports the intended Form VIII participial/adjectival reading.",
    "مفعال": "Context supports the intended instrument-noun reading.",
    "مفعول": "Context supports the intended passive-participle/adjectival reading.",
}


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def decision_key(row: dict) -> tuple[str, str, str, str, str, str]:
    return (
        str(row.get("template", "")),
        str(row.get("base_form", "")),
        str(row.get("full_form", "")),
        str(row.get("prefix", "")),
        str(row.get("suffix", "")),
        str(row.get("surface_rule", "")),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--review-queue",
        type=Path,
        default=Path("data_generation/runs/abw_multisource_v2/audit_v1/review_pass_001/review_queue.jsonl"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "data_generation/runs/abw_multisource_v2/audit_v1/review_pass_001/manual_review_decisions_001.jsonl"
        ),
    )
    args = parser.parse_args()

    rows = read_jsonl(args.review_queue)
    if len(rows) != 137:
        raise SystemExit(f"Expected 137 v2 review rows, got {len(rows)}")

    keys = [decision_key(row) for row in rows]
    if len(set(keys)) != len(keys):
        raise SystemExit("Review queue contains duplicate decision keys; source-aware decisions are needed.")

    decisions: list[dict[str, str]] = []
    for row in rows:
        key = decision_key(row)
        if key in REJECT_OVERRIDES:
            reason, notes = REJECT_OVERRIDES[key]
            decision = "reject"
        else:
            reason = "context_valid_after_v2_second_pass"
            notes = NOTES_BY_TEMPLATE.get(str(row.get("template", "")), "Context supports the intended target reading.")
            decision = "accept"

        decisions.append(
            {
                "template": key[0],
                "base_form": key[1],
                "full_form": key[2],
                "prefix": key[3],
                "suffix": key[4],
                "surface_rule": key[5],
                "decision": decision,
                "reason": reason,
                "notes": notes,
            }
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for decision in decisions:
            handle.write(json.dumps(decision, ensure_ascii=False, sort_keys=True) + "\n")

    n_accept = sum(row["decision"] == "accept" for row in decisions)
    n_reject = sum(row["decision"] == "reject" for row in decisions)
    print(f"wrote {args.output}")
    print(f"decisions={len(decisions)} accept={n_accept} reject={n_reject}")


if __name__ == "__main__":
    main()
