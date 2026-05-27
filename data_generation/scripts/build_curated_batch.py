#!/usr/bin/env python3
"""Build a curated reviewed batch from explicit target-pattern allowlists."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from common import normalize_ar, read_jsonl, strip_diacritics, write_jsonl


ALLOWLIST: dict[str, dict[str, set[str]]] = {
    "فعال": {
        "target_broken_plural": {
            "رجال",
            "شباب",
            "كتاب",
            "بنات",
            "حكام",
            "عمال",
            "تجار",
            "طلاب",
            "كبار",
            "بلاد",
        }
    },
    "فعلاء": {
        "target_broken_plural": {
            "زملاء",
            "فقراء",
            "عملاء",
            "نشطاء",
            "بدلاء",
            "خبراء",
            "زعماء",
            "علماء",
            "سجناء",
            "سفراء",
            "شركاء",
            "شهداء",
            "غرباء",
            "شرفاء",
            "سعداء",
        }
    },
    "فعول": {
        "target_broken_plural": {
            "حقوق",
            "جهود",
            "شروط",
            "ظروف",
            "دروس",
            "بنوك",
            "نجوم",
            "حدود",
            "شعوب",
            "جنود",
            "حلول",
            "صفوف",
        }
    },
    "فاعل": {
        "target_active_participle": {
            "طالب",
            "عامل",
            "لاعب",
            "سابق",
            "عالم",
            "شاهد",
            "كاتب",
            "باحث",
            "قادر",
            "خادم",
            "حامل",
            "قاتل",
            "بارز",
            "عادل",
        }
    },
    "فعيل": {
        "target_intensive_adjective": {
            "شقيق",
            "عديد",
            "قليل",
            "كبير",
            "بعيد",
            "جديد",
            "كريم",
            "ضعيف",
            "صغير",
            "طويل",
            "قصير",
            "شديد",
            "جميل",
            "سليم",
            "غريب",
        }
    },
    "مفعول": {
        "target_passive_participle": {
            "محدود",
            "معروف",
            "محظور",
            "منشور",
            "مشغول",
            "معقول",
            "ممنوع",
            "منسوب",
            "محظوظ",
            "محكوم",
            "مظلوم",
            "مفتوح",
            "مقبول",
            "مكتوب",
            "محروس",
            "محروم",
            "مفقود",
            "مطلوب",
            "مبذول",
            "مجروح",
        }
    },
    "افتعال": {
        "target_verbal_noun": {
            "اجتماع",
            "انتخاب",
            "اهتمام",
            "التزام",
            "اعتماد",
            "اختلاف",
            "اعتقال",
            "احترام",
            "اعتراف",
            "انتقال",
            "احتفال",
            "احتمال",
            "ارتباط",
            "ارتفاع",
            "اعتذار",
            "اعتراض",
            "انتشار",
            "احتجاز",
            "احتلال",
            "اشتراك",
            "اعتصام",
            "اقتراح",
            "اقتصاد",
            "اكتشاف",
            "امتحان",
            "اختبار",
            "ابتعاد",
            "ابتكار",
            "انتصار",
            "امتلاك",
        }
    },
    "فعالة": {
        "target_verbal_noun": {
            "ثقافة",
            "دراسة",
            "علاقة",
            "كتابة",
            "تجارة",
            "حراسة",
            "صناعة",
            "خسارة",
            "سلامة",
            "شهادة",
            "صحافة",
            "نزاهة",
            "بطالة",
            "جدارة",
            "حضارة",
            "رقابة",
            "شجاعة",
            "عمالة",
            "كثافة",
            "براعة",
            "بساطة",
            "جراحة",
            "حرارة",
            "خلاصة",
        }
    },
    "فعلان": {
        "target_intensive_adjective": {
            "فرحان",
            "زعلان",
            "عطشان",
            "سكران",
        }
    },
    "مفتعل": {
        "target_form_viii_participle": {
            "مختلف",
            "معتدل",
            "مشترك",
            "مقترح",
            "ملتزم",
            "مرتبط",
            "معترف",
            "مفترض",
            "مشتبه",
            "مشتعل",
            "مقتنع",
            "مكتمل",
            "منتسب",
            "مختلط",
            "مرتقب",
            "معترض",
            "محتجز",
            "محترف",
            "مبتكر",
            "مخترع",
        }
    },
    "مفعال": {
        "target_instrument_noun": {
            "مفتاح",
            "منظار",
            "مرصاد",
            "مصباح",
        }
    },
}

EXCLUDED_BASES = {
    "تراب": "primitive_lexical",
    "مجتمع": "primitive_lexical",
    "باخرة": "primitive_lexical",
    "بارحة": "primitive_lexical",
    "تجاري": "non_target_nisba",
    "ثقافي": "non_target_nisba",
    "حكومي": "non_target_nisba",
    "سعودي": "proper_name_or_place",
    "لبناني": "proper_name_or_place",
    "صالح": "lexicalized_fixed_expression",
}
DERIVED_VERB_TEMPLATES = {"استفعل", "انفعل"}
ALLOWED_POS_BY_CLASS = {
    "target_broken_plural": {"noun"},
    "target_form_x_verb": {"verb"},
    "target_form_vii_verb": {"verb"},
    "target_active_participle": {"noun", "adj"},
    "target_passive_participle": {"noun", "adj"},
    "target_form_viii_participle": {"noun", "adj"},
    "target_verbal_noun": {"noun"},
    "target_intensive_adjective": {"noun", "adj"},
    "target_instrument_noun": {"noun"},
}
PATTERN_COMPATIBLE = {
    "فعال": {"فعال"},
    "فعلاء": {"فعلاء"},
    "فعول": {"فعول"},
    "فاعل": {"فاعل"},
    "فعيل": {"فعيل"},
    "مفعول": {"مفعول"},
    "افتعال": {"افتعال"},
    "فعالة": {"فعالة", "فعالت"},
    "فعلان": {"فعلان"},
    "مفتعل": {"مفتعل"},
    "مفعال": {"مفعال"},
}
RAW_PATTERN_SIGNATURES = {
    # Distinguish فاعِل active participles from فاعَل verbs and فاعَل nouns
    # such as عالَم "world". The unvocalized pattern alone is not enough.
    "فاعل": {"1ا2ِ3"},
}
CONTEXT_EXCLUDED_ROWS = [
    {
        "full_form": "مصباح",
        "base_form": "مصباح",
        "sentence_contains": "مصباح قطب",
        "reason": "proper_name_in_context",
    },
    {
        "full_form": "وسليمان",
        "base_form": "سليم",
        "sentence_contains": "وسليمان سعد",
        "reason": "proper_name_in_context",
    },
    {
        "full_form": "الغريب",
        "base_form": "غريب",
        "sentence_contains": "محيي الدين الغريب",
        "reason": "proper_name_in_context",
    },
    {
        "full_form": "انتصار",
        "base_form": "انتصار",
        "sentence_contains": "انتصار حسين",
        "reason": "proper_name_in_context",
    },
    {
        "full_form": "بكتابه",
        "base_form": "كتاب",
        "sentence_contains": "بكتابه ضخم الأهمية",
        "reason": "wrong_lexical_reading_in_context",
    },
    {
        "full_form": "بالكتاب",
        "base_form": "كتاب",
        "sentence_contains": "بالكتاب والسنة",
        "reason": "wrong_lexical_reading_in_context",
    },
    {
        "full_form": "كتاب",
        "base_form": "كتاب",
        "sentence_contains": "من كتاب يحمل",
        "reason": "wrong_lexical_reading_in_context",
    },
    {
        "full_form": "كتابا",
        "base_form": "كتاب",
        "sentence_contains": "يبيع كتابا",
        "reason": "wrong_lexical_reading_in_context",
    },
    {
        "full_form": "ببلاده",
        "base_form": "بلاد",
        "sentence_contains": "ووصل ببلاده",
        "reason": "wrong_camel_reading_in_context",
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--max-per-base", type=int, default=4)
    return parser.parse_args()


def row_key(row: dict[str, Any]) -> tuple[str, str, str, str, str]:
    return (
        str(row.get("template", "")),
        str(row.get("base_form", "")),
        str(row.get("full_form", "")),
        str(row.get("prefix", "")),
        str(row.get("suffix", "")),
    )


def row_sort_key(row: dict[str, Any]) -> tuple[str, str, int, int, str]:
    prefix = str(row.get("prefix", ""))
    suffix = str(row.get("suffix", ""))
    return (
        str(row.get("template", "")),
        str(row.get("base_form", "")),
        1 if row.get("has_affix") else 0,
        len(prefix) + len(suffix),
        str(row.get("full_form", "")),
    )


def accepted_class(row: dict[str, Any]) -> str:
    template = row.get("template", "")
    base = row.get("base_form", "")
    if is_conservative_derived_verb(row):
        return "target_form_x_verb" if template == "استفعل" else "target_form_vii_verb"
    for morph_class, bases in ALLOWLIST.get(template, {}).items():
        if base in bases:
            return morph_class
    return ""


def is_conservative_derived_verb(row: dict[str, Any]) -> bool:
    analysis = row.get("camel_analysis") or {}
    return (
        row.get("template") in DERIVED_VERB_TEMPLATES
        and row.get("pos") == "verb"
        and analysis.get("pos") == "verb"
        and int(row.get("camel_ambiguity") or 0) < 10
    )


def should_skip(row: dict[str, Any], morph_class: str) -> bool:
    analysis = row.get("camel_analysis") or {}
    full = str(row.get("full_form", ""))
    lex = str(analysis.get("lex", ""))
    analysis_pos = analysis.get("pos")
    if context_exclusion_reason(row):
        return True
    if not pos_is_compatible(row, morph_class):
        return True
    if row.get("base_form") in EXCLUDED_BASES:
        return True
    if analysis_pos and row.get("pos") and analysis_pos != row.get("pos"):
        return True
    if analysis_pos in {"noun_prop", "latin", "foreign"}:
        return True
    if "ِيّ" in lex or full.endswith("ي") and row.get("template") in {"فعال", "فعول", "فعلان", "مفتعل"}:
        return True
    if int(row.get("camel_ambiguity") or 0) > 20:
        return True
    if row.get("template") not in DERIVED_VERB_TEMPLATES and not camel_pattern_matches(row):
        return True
    return False


def pos_is_compatible(row: dict[str, Any], morph_class: str) -> bool:
    allowed = ALLOWED_POS_BY_CLASS.get(morph_class)
    if not allowed:
        return False
    pos_values = {str(value) for value in [row.get("pos"), (row.get("camel_analysis") or {}).get("pos")] if value}
    return bool(pos_values) and pos_values <= allowed


def context_exclusion_reason(row: dict[str, Any]) -> str:
    sentence = str(row.get("example_sentence") or row.get("sentence") or "")
    for exclusion in CONTEXT_EXCLUDED_ROWS:
        if row.get("full_form") != exclusion["full_form"]:
            continue
        if row.get("base_form") != exclusion["base_form"]:
            continue
        if exclusion["sentence_contains"] in sentence:
            return exclusion["reason"]
    return ""


def camel_pattern_matches(row: dict[str, Any]) -> bool:
    analysis = row.get("camel_analysis") or {}
    raw_pattern = str(analysis.get("pattern", ""))
    raw_signatures = RAW_PATTERN_SIGNATURES.get(str(row.get("template", "")))
    if raw_signatures and not any(signature in raw_pattern for signature in raw_signatures):
        return False
    pattern = normalize_camel_pattern(analysis.get("pattern", ""))
    if not pattern:
        return False
    expected = PATTERN_COMPATIBLE.get(row.get("template", ""), {row.get("template", "")})
    return any(value in pattern for value in expected)


def normalize_camel_pattern(pattern: str) -> str:
    text = normalize_ar(strip_diacritics(pattern))
    text = text.replace("1", "ف").replace("2", "ع").replace("3", "ل")
    text = text.replace("ٱ", "ا")
    # Remove common clitics/case material without trying to fully parse Arabic morphology.
    for prefix in ["وال", "فال", "بال", "كال", "لل", "ال", "و", "ف", "ب", "ل"]:
        if text.startswith(prefix):
            text = text[len(prefix) :]
            break
    for suffix in ["اته", "اتها", "اتهم", "اتهم", "ات", "هما", "هم", "هن", "ها", "ه", "ك", "ي", "نا", "ون", "ين", "ان", "وا", "ا"]:
        if text.endswith(suffix) and len(text) > len(suffix) + 2:
            text = text[: -len(suffix)]
            break
    return text


def mark_accept(row: dict[str, Any], morph_class: str) -> dict[str, Any]:
    row = dict(row)
    row["audit_decision"] = "accept"
    row["audit_reason"] = "valid_clean"
    row["morph_class"] = morph_class
    row["dataset_use"] = "main_target"
    row["audit_notes"] = (
        "Curated batch 001: accepted by explicit base-form allowlist for this target template. "
        "Rows with obvious nisba/name/primitive lexical problems were excluded before export."
    )
    return row


def mark_exclude(row: dict[str, Any], reason: str) -> dict[str, Any]:
    row = dict(row)
    row["audit_decision"] = "reject"
    row["audit_reason"] = reason
    row["morph_class"] = EXCLUDED_BASES.get(row.get("base_form", ""), "non_target")
    row["dataset_use"] = "exclude"
    row["audit_notes"] = "Curated batch 001 explicit exclusion."
    return row


def main() -> None:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    rows = sorted(read_jsonl(args.input), key=row_sort_key)

    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    per_base: Counter[tuple[str, str]] = Counter()
    seen: set[tuple[str, str, str, str, str]] = set()

    for row in rows:
        key = row_key(row)
        if key in seen:
            continue
        seen.add(key)

        base = row.get("base_form", "")
        if base in EXCLUDED_BASES:
            rejected.append(mark_exclude(row, EXCLUDED_BASES[base]))
            continue
        context_reason = context_exclusion_reason(row)
        if context_reason:
            rejected.append(mark_exclude(row, context_reason))
            continue

        morph_class = accepted_class(row)
        if not morph_class or should_skip(row, morph_class):
            continue

        base_key = (row.get("template", ""), base)
        if per_base[base_key] >= args.max_per_base:
            continue
        per_base[base_key] += 1
        accepted.append(mark_accept(row, morph_class))

    write_jsonl(args.out_dir / "accepted_batch_001.jsonl", accepted)
    write_jsonl(args.out_dir / "rejected_batch_001.jsonl", rejected)
    report = {
        "input": str(args.input),
        "accepted": str(args.out_dir / "accepted_batch_001.jsonl"),
        "rejected": str(args.out_dir / "rejected_batch_001.jsonl"),
        "n_accepted": len(accepted),
        "n_rejected": len(rejected),
        "accepted_by_template": dict(Counter(row.get("template", "") for row in accepted)),
        "accepted_by_morph_class": dict(Counter(row.get("morph_class", "") for row in accepted)),
        "accepted_roots": len({row.get("root", "") for row in accepted}),
        "accepted_bases": len({(row.get("template", ""), row.get("base_form", "")) for row in accepted}),
        "rejected_by_reason": dict(Counter(row.get("audit_reason", "") for row in rejected)),
    }
    (args.out_dir / "batch_001_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(f"wrote {args.out_dir / 'accepted_batch_001.jsonl'}")
    print(f"wrote {args.out_dir / 'rejected_batch_001.jsonl'}")
    print(f"wrote {args.out_dir / 'batch_001_report.json'}")
    print(f"accepted={len(accepted)} rejected={len(rejected)}")


if __name__ == "__main__":
    main()
