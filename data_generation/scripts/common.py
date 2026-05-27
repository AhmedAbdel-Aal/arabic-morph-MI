"""Shared helpers for Arabic root-template candidate extraction."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable


TARGET_TEMPLATES = [
    "فعال",
    "فعلاء",
    "فعول",
    "استفعل",
    "فاعل",
    "فعالة",
    "فعيل",
    "مفعول",
    "افتعال",
    "انفعل",
    "فعلان",
    "مفتعل",
    "مفعال",
]

PREFIXES = ["", "ال", "و", "ف", "ب", "ل", "وال", "فال", "بال", "لل"]
SUFFIXES = [
    "",
    "ه",
    "ها",
    "هم",
    "هن",
    "نا",
    "ك",
    "كم",
    "ي",
    "ة",
    "ا",
    "ان",
    "ين",
    "ون",
    "ات",
    "وا",
    "ت",
    "تها",
    "وه",
    "يه",
    "اتها",
]
POSSESSIVE_SUFFIXES = {"ه", "ها", "هم", "هن", "نا", "ك", "كم", "ي", "يه"}

ARABIC_DIACRITICS_RE = re.compile(r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]")
ARABIC_TOKEN_RE = re.compile(r"[\u0621-\u064A]+")


def read_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open(encoding="utf-8") as f:
        for line_number, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {path}:{line_number}") from exc


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True))
            f.write("\n")
            count += 1
    return count


def strip_diacritics(text: str | None) -> str:
    return ARABIC_DIACRITICS_RE.sub("", str(text or ""))


def normalize_ar(text: str | None) -> str:
    text = strip_diacritics(text)
    text = text.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    text = text.replace("ى", "ي")
    return text


def normalize_root(root: str | None) -> str:
    root = str(root or "")
    return root.replace(".", "").replace("-", "").replace("_", "").replace(" ", "")


def dot_root(root: str | None) -> str:
    root = normalize_root(root)
    return ".".join(root) if len(root) == 3 else root


def simple_arabic_tokenize(sentence: str) -> list[str]:
    return [m.group(0) for m in ARABIC_TOKEN_RE.finditer(strip_diacritics(sentence))]


def apply_template(root: str, template: str) -> str | None:
    root = normalize_root(root)
    if len(root) != 3:
        return None
    r1, r2, r3 = root
    slot = {"ف": r1, "ع": r2, "ل": r3}
    return "".join(slot.get(ch, ch) for ch in template)


def generate_surface_variants(
    prefix: str,
    canonical_base: str,
    suffix: str,
) -> list[dict[str, str]]:
    variants = [
        {
            "surface_stem": canonical_base,
            "canonical_base_form": canonical_base,
            "full_form": f"{prefix}{canonical_base}{suffix}",
            "surface_rule": "plain",
        }
    ]
    if suffix in POSSESSIVE_SUFFIXES and canonical_base.endswith("ة"):
        surface_stem = f"{canonical_base[:-1]}ت"
        variants.append(
            {
                "surface_stem": surface_stem,
                "canonical_base_form": canonical_base,
                "full_form": f"{prefix}{surface_stem}{suffix}",
                "surface_rule": "ta_marbuta_to_t_before_possessive_suffix",
            }
        )
    return variants


def match_rank(match: dict[str, str]) -> tuple[int, int, bool, int]:
    """Prefer parsimonious analyses, then stable template order."""
    return (
        len(match["suffix"]),
        len(match["prefix"]),
        match["surface_rule"] != "plain",
        TARGET_TEMPLATES.index(match["template"]),
    )


def keep_best_matches(matches: list[dict[str, str]]) -> list[dict[str, str]]:
    if not matches:
        return []
    best_rank = min(match_rank(match) for match in matches)
    return [match for match in matches if match_rank(match) == best_rank]


def infer_template_affix(root: str, token: str) -> list[dict[str, str]]:
    token_norm = normalize_ar(token)
    matches: list[dict[str, str]] = []
    for template in TARGET_TEMPLATES:
        base = apply_template(root, template)
        if not base:
            continue
        base_norm = normalize_ar(base)
        for prefix in PREFIXES:
            for suffix in SUFFIXES:
                for variant in generate_surface_variants(prefix, base_norm, suffix):
                    if token_norm == normalize_ar(variant["full_form"]):
                        matches.append(
                            {
                                "template": template,
                                "surface_stem": variant["surface_stem"],
                                "canonical_base_form": variant["canonical_base_form"],
                                "prefix": prefix,
                                "suffix": suffix,
                                "full_form": variant["full_form"],
                                "surface_rule": variant["surface_rule"],
                            }
                        )
    return keep_best_matches(matches)


def compact_camel_analysis(analysis: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "diac",
        "lex",
        "root",
        "pattern",
        "pos",
        "source",
        "gloss",
        "prc0",
        "prc1",
        "prc2",
        "prc3",
        "enc0",
    ]
    return {k: analysis.get(k) for k in keys if analysis.get(k) not in [None, "", "0", "na"]}
