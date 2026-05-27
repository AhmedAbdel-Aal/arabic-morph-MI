#!/usr/bin/env python3
"""Extract root-template-affix candidates from sentence JSONL with CAMEL."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from common import (
    compact_camel_analysis,
    dot_root,
    infer_template_affix,
    normalize_root,
    read_jsonl,
    simple_arabic_tokenize,
    strip_diacritics,
)


KEEP_POS = {"noun", "adj", "verb"}
LEXICAL_NOUN_HEAVY_TEMPLATES = {"فعال", "فعيل", "فعول", "فعلان", "فعلاء"}
DERIVED_NOUN_TEMPLATES = {"فاعل", "مفعول", "مفتعل", "مفعال", "افتعال", "فعالة"}
VERB_TEMPLATES = {"استفعل", "انفعل"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sentences", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--camel-db", default="calima-msa-r13")
    parser.add_argument("--max-sentences", type=int, default=0)
    parser.add_argument("--log-every", type=int, default=250)
    parser.add_argument("--no-pos-tagger", action="store_true")
    parser.add_argument(
        "--filter-mode",
        choices=["broad", "derived"],
        default="broad",
        help=(
            "broad keeps any matched target template. derived drops noun uses of broad lexical "
            "noun-heavy templates such as فعال/فعيل/فعول, while keeping verbs, adjectives, "
            "participles, verbal nouns, and instrument/place-like derived templates."
        ),
    )
    return parser.parse_args()


def load_camel(camel_db: str, use_pos_tagger: bool):
    try:
        from camel_tools.disambig.mle import MLEDisambiguator
        from camel_tools.morphology.analyzer import Analyzer
        from camel_tools.morphology.database import MorphologyDB
        from camel_tools.tagger.default import DefaultTagger
    except ImportError as exc:
        raise SystemExit("Install and run this in the CAMEL environment: pip install camel-tools") from exc

    db = MorphologyDB.builtin_db(camel_db, flags="a")
    analyzer = Analyzer(db, backoff="NONE")
    pos_tagger = None
    if use_pos_tagger:
        try:
            mle = MLEDisambiguator.pretrained(camel_db)
        except TypeError:
            mle = MLEDisambiguator.pretrained()
        pos_tagger = DefaultTagger(mle, "pos")
    return analyzer, pos_tagger


def tag_pos(tokens: list[str], pos_tagger: Any | None) -> list[str | None]:
    if pos_tagger is None:
        return [None for _ in tokens]
    return pos_tagger.tag(tokens)


def pos_is_kept(selected_pos: str | None, analysis_pos: str | None) -> tuple[bool, str | None]:
    if selected_pos in KEEP_POS:
        return True, selected_pos
    if analysis_pos in KEEP_POS:
        return True, analysis_pos
    return False, selected_pos or analysis_pos


def extract_from_token(
    *,
    token: str,
    token_index: int,
    selected_pos: str | None,
    analyzer: Any,
    counters: Counter,
    filter_mode: str,
) -> list[dict[str, Any]]:
    analyses = analyzer.analyze(strip_diacritics(token))
    if not analyses:
        counters["tokens_no_camel_analysis"] += 1
        return []

    candidates: list[dict[str, Any]] = []
    saw_kept_pos = False
    saw_triliteral = False
    saw_template_match = False

    for analysis in analyses:
        keep_pos, pos = pos_is_kept(selected_pos, analysis.get("pos"))
        if not keep_pos:
            counters["analyses_pos_filtered"] += 1
            continue
        saw_kept_pos = True

        root = normalize_root(analysis.get("root"))
        if len(root) != 3:
            counters["analyses_non_triliteral_root"] += 1
            continue
        saw_triliteral = True

        template_matches = infer_template_affix(root, token)
        if not template_matches:
            counters["analyses_no_template_match"] += 1
            continue
        saw_template_match = True

        for match in template_matches:
            keep, reject_reason = keep_candidate(match["template"], pos, filter_mode)
            if not keep:
                counters[f"candidates_filtered_{reject_reason}"] += 1
                continue
            candidates.append(
                {
                    "target_text": strip_diacritics(token),
                    "target_token_index": token_index,
                    "root": dot_root(root),
                    "template": match["template"],
                    "base_form": match["canonical_base_form"],
                    "canonical_base_form": match["canonical_base_form"],
                    "surface_stem": match["surface_stem"],
                    "prefix": match["prefix"],
                    "suffix": match["suffix"],
                    "full_form": match["full_form"],
                    "surface_rule": match["surface_rule"],
                    "has_affix": bool(match["prefix"] or match["suffix"]),
                    "pos": pos,
                    "camel_ambiguity": len(analyses),
                    "camel_analysis": compact_camel_analysis(analysis),
                }
            )

    if not saw_kept_pos:
        counters["tokens_no_kept_pos"] += 1
    elif not saw_triliteral:
        counters["tokens_no_triliteral_root"] += 1
    elif not saw_template_match:
        counters["tokens_no_template_match"] += 1

    dedup = {}
    for candidate in candidates:
        key = (
            candidate["full_form"],
            candidate["root"],
            candidate["template"],
            candidate["prefix"],
            candidate["suffix"],
            candidate["surface_rule"],
        )
        dedup[key] = candidate
    return list(dedup.values())


def keep_candidate(template: str, pos: str | None, filter_mode: str) -> tuple[bool, str]:
    if filter_mode == "broad":
        return True, ""

    if pos == "verb":
        return True, ""

    if pos == "adj":
        return True, ""

    if pos == "noun":
        if template in DERIVED_NOUN_TEMPLATES:
            return True, ""
        if template in LEXICAL_NOUN_HEAVY_TEMPLATES:
            return False, "lexical_noun_heavy_template"
        if template in VERB_TEMPLATES:
            return False, "verb_template_as_noun"

    return False, "outside_derived_filter"


def main() -> None:
    args = parse_args()
    report_path = args.report or args.output.with_name("extraction_report.json")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    print("Loading CAMEL", flush=True)
    analyzer, pos_tagger = load_camel(args.camel_db, use_pos_tagger=not args.no_pos_tagger)
    print("CAMEL loaded", flush=True)

    counters: Counter = Counter()
    by_template: Counter = Counter()
    by_pos: Counter = Counter()
    by_surface_rule: Counter = Counter()

    with args.output.open("w", encoding="utf-8") as out:
        for sentence_number, sentence_row in enumerate(read_jsonl(args.sentences), 1):
            if args.max_sentences and sentence_number > args.max_sentences:
                break

            sentence = sentence_row.get("sentence", "")
            tokens = simple_arabic_tokenize(sentence)
            pos_tags = tag_pos(tokens, pos_tagger)
            counters["sentences"] += 1
            counters["tokens"] += len(tokens)

            sentence_candidates = []
            for token_index, (token, selected_pos) in enumerate(zip(tokens, pos_tags)):
                token_candidates = extract_from_token(
                    token=token,
                    token_index=token_index,
                    selected_pos=selected_pos,
                    analyzer=analyzer,
                    counters=counters,
                    filter_mode=args.filter_mode,
                )
                sentence_candidates.extend(token_candidates)

            if sentence_candidates:
                counters["sentences_with_candidates"] += 1
            for candidate in sentence_candidates:
                row = {
                    **{k: v for k, v in sentence_row.items() if k != "text"},
                    **candidate,
                    "sentence": sentence,
                }
                out.write(json.dumps(row, ensure_ascii=False, sort_keys=True))
                out.write("\n")
                counters["candidates"] += 1
                by_template[row["template"]] += 1
                by_pos[row.get("pos")] += 1
                by_surface_rule[row["surface_rule"]] += 1

            if args.log_every and sentence_number % args.log_every == 0:
                print(
                    f"sentences={sentence_number} tokens={counters['tokens']} candidates={counters['candidates']}",
                    flush=True,
                )

    report = {
        "sentences_path": str(args.sentences),
        "output_path": str(args.output),
        "camel_db": args.camel_db,
        "filter_mode": args.filter_mode,
        "filter_policy": {
            "description": (
                "derived mode keeps verbs and adjectives; keeps noun rows only for templates "
                "with clearer derivational status in the current study; drops noun rows for broad "
                "lexical noun-heavy templates that often admit frozen/concrete nouns."
            ),
            "derived_noun_templates": sorted(DERIVED_NOUN_TEMPLATES),
            "lexical_noun_heavy_templates": sorted(LEXICAL_NOUN_HEAVY_TEMPLATES),
        },
        "counters": dict(counters),
        "by_template": dict(by_template),
        "by_pos": dict(by_pos),
        "by_surface_rule": dict(by_surface_rule),
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    print(f"wrote {args.output}")
    print(f"wrote {report_path}")
    print(f"candidates={counters['candidates']}")


if __name__ == "__main__":
    main()
