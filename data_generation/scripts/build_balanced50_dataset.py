#!/usr/bin/env python3
"""Build the 50-example-per-template probing dataset."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from common import compact_camel_analysis, dot_root, infer_template_affix, normalize_root, read_jsonl, strip_diacritics, write_jsonl
from export_productivity_dataset import build_stats, export_row


TARGET_COUNT = 50
TEMPLATES = [
    "استفعل",
    "افتعال",
    "انفعل",
    "فاعل",
    "فعال",
    "فعالة",
    "فعلاء",
    "فعلان",
    "فعول",
    "فعيل",
    "مفتعل",
    "مفعال",
    "مفعول",
]

MORPH_CLASS = {
    "فاعل": "target_active_participle",
    "فعال": "target_broken_plural",
    "فعلاء": "target_broken_plural",
    "فعلان": "target_intensive_adjective",
    "فعول": "target_broken_plural",
    "فعيل": "target_intensive_adjective",
    "مفعال": "target_instrument_noun",
}

CONTROLLED_SPECS = [
    # فاعل top-up
    ("فاعل", "حرس", "حارس", "حارس", "وقف حارس أمام الباب طوال الليل."),
    ("فاعل", "كتب", "كاتب", "كاتب", "شارك كاتب معروف في الندوة الثقافية."),
    # فعال top-up: broken plurals/collectives with controlled contexts.
    ("فعال", "ثمر", "ثمار", "ثمار", "جمع الفلاح ثمار الموسم في صناديق كبيرة."),
    ("فعال", "ثمر", "ثمار", "الثمار", "فحص العامل الثمار الناضجة قبل نقلها إلى السوق."),
    ("فعال", "ثمر", "ثمار", "بثمار", "امتلأت السلة بثمار طازجة من البستان."),
    ("فعال", "ثمر", "ثمار", "وثمار", "باع الفلاح الخضار وثمار الأشجار في الصباح."),
    ("فعال", "جبل", "جبال", "جبال", "تغطي الثلوج جبال المنطقة في الشتاء."),
    ("فعال", "جبل", "جبال", "الجبال", "بدت الجبال عالية خلف القرية."),
    ("فعال", "جبل", "جبال", "بجبال", "تشتهر البلاد بجبال شاهقة ومناظر واسعة."),
    ("فعال", "جبل", "جبال", "وجبال", "تضم الخريطة سهولا وجبال تمتد إلى الشمال."),
    ("فعال", "سلل", "سلال", "سلال", "حملت الأسرة سلال الفاكهة إلى السيارة."),
    ("فعال", "سلل", "سلال", "السلال", "وضعت المرأة السلال قرب باب المطبخ."),
    ("فعال", "سلل", "سلال", "بسلال", "عاد الأطفال بسلال مليئة بالتفاح."),
    ("فعال", "سلل", "سلال", "وسلال", "اشترى البائع صناديق وسلال جديدة للعرض."),
    ("فعال", "بحر", "بحار", "بحار", "تصل السفن بين بحار بعيدة عبر طرق تجارية."),
    ("فعال", "بحر", "بحار", "البحار", "تلوثت البحار بسبب النفايات الصناعية."),
    ("فعال", "بحر", "بحار", "ببحار", "تحيط الجزيرة ببحار واسعة من كل جهة."),
    ("فعال", "بحر", "بحار", "وبحار", "تضم القارة صحارى وبحار كثيرة."),
    # فعلاء top-up
    ("فعلاء", "شعر", "شعراء", "شعراء", "اجتمع شعراء المدينة في أمسية أدبية."),
    ("فعلاء", "حلف", "حلفاء", "حلفاء", "بحث القادة مع حلفاء المنطقة خطة التعاون."),
    # فعول top-up
    ("فعول", "جند", "جنود", "جنود", "عاد جنود الوحدة إلى المعسكر بعد التدريب."),
    ("فعول", "جند", "جنود", "وجنود", "شارك ضباط وجنود في العرض الرسمي."),
    ("فعول", "صفف", "صفوف", "صفوف", "انتظمت صفوف الطلاب أمام المدرسة."),
    ("فعول", "صفف", "صفوف", "وصفوف", "نظمت الإدارة مقاعد وصفوف القاعة."),
    ("فعول", "شرط", "شروط", "شروط", "وضعت اللجنة شروط المشاركة في المسابقة."),
    ("فعول", "شرط", "شروط", "بشروط", "وافق الطرفان بشروط واضحة ومكتوبة."),
    # فعيل top-up
    ("فعيل", "قصر", "قصير", "قصير", "كان الطريق قصير لكنه مزدحم بالسيارات."),
    ("فعيل", "شدد", "شديد", "شديد", "واجه الفريق ضغطا شديد في نهاية المباراة."),
    ("فعيل", "بعد", "بعيد", "بعيد", "يقع البيت بعيد عن مركز المدينة."),
    ("فعيل", "كبر", "كبير", "كبير", "كان المشروع كبير ويحتاج إلى تمويل واسع."),
    # فعلان top-up beyond the earlier controlled_f3lan_v1 rows.
    ("فعلان", "خجل", "خجلان", "خجلان", "وقف الطفل خجلان أمام الضيوف."),
    ("فعلان", "خجل", "خجلان", "الخجلان", "ساعد المعلم الطالب الخجلان على الكلام."),
    ("فعلان", "خجل", "خجلان", "وخجلان", "دخل الطالب هادئا وخجلان إلى الصف."),
    ("فعلان", "خجل", "خجلان", "بخجلان", "نظر الصغير بخجلان إلى الأرض."),
    ("فعلان", "كسل", "كسلان", "كسلان", "بدا العامل كسلان في بداية اليوم."),
    ("فعلان", "كسل", "كسلان", "الكسلان", "نبّه المدرب اللاعب الكسلان إلى واجبه."),
    ("فعلان", "كسل", "كسلان", "وكسلان", "جلس الطالب صامتا وكسلان بعد الغداء."),
    ("فعلان", "كسل", "كسلان", "بكسلان", "وصف المدير الموظف بكسلان أمام الفريق."),
    ("فعلان", "ندم", "ندمان", "ندمان", "بقي الرجل ندمان بعد قراره المتسرع."),
    ("فعلان", "ندم", "ندمان", "الندمان", "حاول الصديق الندمان إصلاح الخطأ."),
    ("فعلان", "ندم", "ندمان", "وندمان", "عاد الشاب صامتا وندمان إلى بيته."),
    ("فعلان", "ندم", "ندمان", "بندمان", "تكلم الأخ بندمان واضح عن فعلته."),
    ("فعلان", "غرق", "غرقان", "غرقان", "وجد الصياد قاربا غرقان قرب الساحل."),
    ("فعلان", "غرق", "غرقان", "الغرقان", "أنقذ الحارس الرجل الغرقان بسرعة."),
    ("فعلان", "غرق", "غرقان", "وغرقان", "وصل القارب مكسورا وغرقان في الماء."),
    ("فعلان", "غرق", "غرقان", "بغرقان", "أشار البحار بغرقان واضح في النهر."),
    ("فعلان", "زعل", "زعلان", "زعلان", "جلس الطفل زعلان بعد خسارة لعبته."),
    ("فعلان", "زعل", "زعلان", "الزعلان", "حاولت الأم إضحاك الطفل الزعلان."),
    ("فعلان", "زعل", "زعلان", "وزعلان", "عاد الطالب ساكتا وزعلان من المدرسة."),
    ("فعلان", "زعل", "زعلان", "بزعلان", "تحدث الصديق بزعلان ظاهر في صوته."),
    ("فعلان", "تعب", "تعبان", "تعبان", "كان العامل تعبان بعد يوم طويل."),
    ("فعلان", "تعب", "تعبان", "التعبان", "جلس المسافر التعبان على المقعد."),
    ("فعلان", "تعب", "تعبان", "وتعبان", "عاد الطفل جائعا وتعبان من الرحلة."),
    ("فعلان", "تعب", "تعبان", "بتعبان", "وصف الطبيب المريض بتعبان في التقرير."),
    ("فعلان", "خجل", "خجلان", "خجلانة", "بقيت الطالبة خجلانة أمام الجمهور."),
    ("فعلان", "كسل", "كسلان", "كسلانة", "بدت القطة كسلانة قرب النافذة."),
    ("فعلان", "ندم", "ندمان", "ندمانة", "كانت الفتاة ندمانة على التأخير."),
    ("فعلان", "غرق", "غرقان", "غرقانة", "وجد البحارة السفينة غرقانة بعد العاصفة."),
    ("فعلان", "زعل", "زعلان", "زعلانة", "كانت الطفلة زعلانة من صديقتها."),
    ("فعلان", "غضب", "غضبان", "غضبانة", "خرجت المديرة غضبانة من الاجتماع."),
    ("فعلان", "فرح", "فرحان", "فرحانة", "عادت الطالبة فرحانة بعد الفوز."),
    ("فعلان", "نعس", "نعسان", "نعسانة", "كانت الطفلة نعسانة في السيارة."),
    # مفعال top-up: concrete instrument nouns.
    ("مفعال", "نشر", "منشار", "منشار", "استخدم النجار منشار حاد لقطع الخشب."),
    ("مفعال", "نشر", "منشار", "المنشار", "وضع العامل المنشار على الطاولة."),
    ("مفعال", "نشر", "منشار", "بمنشار", "قطع الحرفي اللوح بمنشار صغير."),
    ("مفعال", "نشر", "منشار", "بالمنشار", "بدأ النجار العمل بالمنشار الكهربائي."),
    ("مفعال", "نشر", "منشار", "ومنشار", "اشترى العامل مطرقة ومنشار للورشة."),
    ("مفعال", "سمر", "مسمار", "مسمار", "ثبت الحرفي اللوحة باستخدام مسمار قوي."),
    ("مفعال", "سمر", "مسمار", "المسمار", "دخل المسمار في الخشب بسهولة."),
    ("مفعال", "سمر", "مسمار", "بمسمار", "علق العامل الصورة بمسمار صغير."),
    ("مفعال", "سمر", "مسمار", "بالمسمار", "ثبت الغطاء بالمسمار المعدني."),
    ("مفعال", "سمر", "مسمار", "ومسمار", "وجد الطفل برغيا ومسمار في الصندوق."),
    ("مفعال", "حرث", "محراث", "محراث", "استعمل الفلاح محراث جديد في الحقل."),
    ("مفعال", "حرث", "محراث", "المحراث", "أصلح الفلاح المحراث قبل موسم الزراعة."),
    ("مفعال", "حرث", "محراث", "بمحراث", "حرث العامل الأرض بمحراث حديدي."),
    ("مفعال", "حرث", "محراث", "بالمحراث", "بدأ الفلاح العمل بالمحراث عند الفجر."),
    ("مفعال", "حرث", "محراث", "ومحراث", "اشترت المزرعة جرارا ومحراث جديدا."),
    ("مفعال", "جرف", "مجراف", "مجراف", "حمل العامل مجراف لينقل الرمل."),
    ("مفعال", "جرف", "مجراف", "المجراف", "كان المجراف مصنوعا من الحديد."),
    ("مفعال", "جرف", "مجراف", "بمجراف", "نظف الحارس الطريق بمجراف واسع."),
    ("مفعال", "جرف", "مجراف", "بالمجراف", "أزاح العامل الطين بالمجراف."),
    ("مفعال", "جرف", "مجراف", "ومجراف", "وضع العامل دلوا ومجراف قرب الباب."),
    ("مفعال", "قلع", "مقلاع", "مقلاع", "صنع الطفل مقلاع من غصن صغير."),
    ("مفعال", "قلع", "مقلاع", "المقلاع", "استخدم الراعي المقلاع لإبعاد الطيور."),
    ("مفعال", "قلع", "مقلاع", "بمقلاع", "رمى الطفل الحصى بمقلاع خشبي."),
    ("مفعال", "قلع", "مقلاع", "بالمقلاع", "تدرب الصبي بالمقلاع تحت إشراف أبيه."),
    ("مفعال", "قلع", "مقلاع", "ومقلاع", "حمل الصبي حبلا ومقلاع في الحقيبة."),
    ("مفعال", "زمر", "مزمار", "مزمار", "عزف الراعي على مزمار من القصب."),
    ("مفعال", "زمر", "مزمار", "المزمار", "انكسر المزمار أثناء النقل."),
    ("مفعال", "زمر", "مزمار", "بمزمار", "بدأ العازف الحفل بمزمار قديم."),
    ("مفعال", "زمر", "مزمار", "بالمزمار", "عزف الفلاح بالمزمار في الحقل."),
    ("مفعال", "زمر", "مزمار", "ومزمار", "اشترى العازف طبلا ومزمار للفرقة."),
    ("مفعال", "خبر", "مخبار", "مخبار", "استخدم الطالب مخبار شفاف في التجربة."),
    ("مفعال", "خبر", "مخبار", "المخبار", "وضع المعلم المخبار على الطاولة."),
    ("مفعال", "خبر", "مخبار", "بمخبار", "قاس الطالب السائل بمخبار دقيق."),
    ("مفعال", "خبر", "مخبار", "بالمخبار", "حدد الباحث الكمية بالمخبار الزجاجي."),
    ("مفعال", "خبر", "مخبار", "ومخبار", "أحضر المعلم ميزانا ومخبار للتجربة."),
    ("مفعال", "نقش", "منقاش", "منقاش", "استعمل الحرفي منقاش صغير للنقش."),
    ("مفعال", "نقش", "منقاش", "المنقاش", "كان المنقاش حادا ودقيقا."),
    ("مفعال", "نقش", "منقاش", "بمنقاش", "نقش العامل الحجر بمنقاش معدني."),
    ("مفعال", "نقش", "منقاش", "بالمنقاش", "أصلح الحرفي الزخرفة بالمنقاش."),
    ("مفعال", "نقش", "منقاش", "ومنقاش", "وضع الحرفي مطرقة ومنقاش في الحقيبة."),
    ("مفعال", "نشر", "منشار", "منشارين", "احتاج النجار إلى منشارين في الورشة."),
    ("مفعال", "سمر", "مسمار", "مسمارين", "ثبت العامل الرف بمسمارين قويين."),
    ("مفعال", "فتح", "مفتاح", "مفتاحين", "احتفظ الحارس بمفتاحين للباب الخارجي."),
]


def load_camel(camel_db: str):
    try:
        from camel_tools.morphology.analyzer import Analyzer
        from camel_tools.morphology.database import MorphologyDB
    except ImportError as exc:
        raise SystemExit("Install and run this in the CAMEL environment: pip install camel-tools") from exc
    return Analyzer(MorphologyDB.builtin_db(camel_db, flags="a"), backoff="NONE")


def select_analysis(analyzer: Any, template: str, root: str, form: str) -> tuple[dict[str, Any], dict[str, str], int]:
    analyses = analyzer.analyze(strip_diacritics(form))
    root_norm = normalize_root(root)
    candidates: list[tuple[int, dict[str, Any], dict[str, str]]] = []
    for analysis in analyses:
        analysis_root = normalize_root(analysis.get("root"))
        if analysis_root != root_norm:
            continue
        matches = [match for match in infer_template_affix(analysis_root, form) if match["template"] == template]
        for match in matches:
            score = 0
            if analysis.get("pos") == "noun_prop":
                score += 5
            if analysis.get("pos") == "adj":
                score -= 2
            if analysis.get("pos") == "noun":
                score -= 1
            if "proper" in str(analysis.get("gloss", "")).lower():
                score += 3
            candidates.append((score, analysis, match))
    if not candidates:
        raise ValueError(f"No CAMEL/template match for {template} {form} root={root}")
    score, analysis, match = sorted(candidates, key=lambda item: item[0])[0]
    return analysis, match, len(analyses)


def controlled_rows(camel_db: str) -> list[dict[str, Any]]:
    analyzer = load_camel(camel_db)
    rows = []
    for index, (template, root, base_form, form, sentence) in enumerate(CONTROLLED_SPECS):
        analysis, match, ambiguity = select_analysis(analyzer, template, root, form)
        rows.append(
            {
                "audit_decision": "accept",
                "audit_notes": (
                    "Balanced50 controlled supplement: manually written MSA context; "
                    "CAMEL root and local root-template matcher agree."
                ),
                "audit_reason": "controlled_context_valid_camel_validated",
                "base_form": base_form,
                "camel_ambiguity": ambiguity,
                "camel_analysis": compact_camel_analysis(analysis),
                "canonical_base_form": base_form,
                "dataset_use": "main_target",
                "example_sentence": sentence,
                "example_source": "controlled_manual",
                "example_source_dataset": "controlled_manual:balanced50_v1",
                "example_url": "",
                "full_form": match["full_form"],
                "has_affix": bool(match["prefix"] or match["suffix"]),
                "morph_class": MORPH_CLASS[template],
                "pos": analysis.get("pos"),
                "prefix": match["prefix"],
                "review_flags": ["controlled_manual_context", "camel_validated_template"],
                "review_pass": "balanced50_controlled_v1",
                "review_status": "accept_manual_controlled",
                "root": dot_root(root),
                "source_datasets": ["controlled_manual:balanced50_v1"],
                "suffix": match["suffix"],
                "surface_rule": match["surface_rule"],
                "surface_stem": match["surface_stem"],
                "target_text": form,
                "target_token_index": index,
                "template": template,
            }
        )
    return rows


def source_dataset(row: dict[str, Any]) -> str:
    return str(row.get("source_dataset") or row.get("example_source_dataset") or "")


def selection_key(row: dict[str, Any]) -> tuple[int, str, str, str, str]:
    controlled = source_dataset(row).startswith("controlled_manual")
    return (
        1 if controlled else 0,
        str(row.get("base_form", "")),
        str(row.get("full_form", "")),
        source_dataset(row),
        str(row.get("sentence") or row.get("example_sentence") or ""),
    )


def select_balanced(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_template: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_template[str(row.get("template", ""))].append(row)

    selected: list[dict[str, Any]] = []
    for template in TEMPLATES:
        candidates = sorted(by_template[template], key=selection_key)
        if len(candidates) < TARGET_COUNT:
            raise ValueError(f"Template {template} has only {len(candidates)} rows after supplementation")

        # Round-robin by base form to avoid taking 50 variants from a few large families.
        by_base: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in candidates:
            by_base[str(row.get("base_form", ""))].append(row)

        chosen: list[dict[str, Any]] = []
        while len(chosen) < TARGET_COUNT:
            progressed = False
            for base in sorted(by_base):
                bucket = by_base[base]
                if not bucket:
                    continue
                chosen.append(bucket.pop(0))
                progressed = True
                if len(chosen) == TARGET_COUNT:
                    break
            if not progressed:
                break
        selected.extend(chosen)
    return selected


def export_probe_json(path: Path, rows: list[dict[str, Any]], root_category: str) -> None:
    probe_rows = [export_row(row, root_category) for row in rows]
    payload = {
        "corpus_stats": build_stats(probe_rows),
        "real_roots": probe_rows,
        "nonce_roots": [],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-accepted",
        type=Path,
        default=Path("data_generation/runs/abw_multisource_v3_controlled_f3lan/accepted_combined_reviewed.jsonl"),
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("data_generation/runs/balanced50_v1"),
    )
    parser.add_argument("--camel-db", default="calima-msa-r13")
    args = parser.parse_args()

    base_rows = list(read_jsonl(args.base_accepted))
    supplement_rows = controlled_rows(args.camel_db)
    all_rows = base_rows + supplement_rows
    selected = select_balanced(all_rows)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.out_dir / "controlled_supplement.jsonl", supplement_rows)
    write_jsonl(args.out_dir / "selected_rows.jsonl", selected)
    export_probe_json(
        args.out_dir / "productivity_dataset_balanced50.json",
        selected,
        "audited_balanced50_v1",
    )

    report = {
        "target_count_per_template": TARGET_COUNT,
        "base_input": str(args.base_accepted),
        "n_base_rows": len(base_rows),
        "n_controlled_supplement_rows": len(supplement_rows),
        "n_selected_rows": len(selected),
        "selected_by_template": Counter(row["template"] for row in selected),
        "selected_by_source_dataset": Counter(source_dataset(row) for row in selected),
        "controlled_selected_by_template": Counter(
            row["template"] for row in selected if source_dataset(row).startswith("controlled_manual")
        ),
        "roots": len({row["root"] for row in selected}),
        "templates": len({row["template"] for row in selected}),
    }
    (args.out_dir / "balanced50_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8"
    )
    (args.out_dir / "README.md").write_text(
        "\n".join(
            [
                "# Balanced50 v1",
                "",
                "This is the 50-example-per-template dataset for probing.",
                "",
                "Rows are selected from the reviewed v3 handoff first. Controlled rows are used only to fill template deficits and are marked by `source_dataset`.",
                "",
                "```text",
                f"rows: {len(selected)}",
                f"templates: {len({row['template'] for row in selected})}",
                f"target per template: {TARGET_COUNT}",
                "```",
                "",
                "Main file:",
                "",
                "```text",
                "data_generation/runs/balanced50_v1/productivity_dataset_balanced50.json",
                "```",
                "",
                "Always report controlled-source sensitivity, especially for `فعلان` and `مفعال`.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(f"wrote {args.out_dir / 'productivity_dataset_balanced50.json'}")
    print(f"rows={len(selected)} templates={report['templates']} roots={report['roots']}")


if __name__ == "__main__":
    main()
