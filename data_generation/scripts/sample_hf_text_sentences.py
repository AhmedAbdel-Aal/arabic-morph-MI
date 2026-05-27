#!/usr/bin/env python3
"""Sample Arabic sentence JSONL from a generic Hugging Face text dataset."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


SENTENCE_BOUNDARY_RE = re.compile(r"(?<=[.!؟?؛…])\s+|\n+")
ARABIC_LETTER_RE = re.compile(r"[\u0621-\u064A]")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--config", default="")
    parser.add_argument("--split", default="train")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--text-field", required=True)
    parser.add_argument("--title-field", default="")
    parser.add_argument("--source-name", default="")
    parser.add_argument("--max-records", type=int, default=2000)
    parser.add_argument("--max-sentences", type=int, default=10000)
    parser.add_argument("--min-chars", type=int, default=25)
    parser.add_argument("--max-chars", type=int, default=350)
    parser.add_argument("--streaming", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--log-every", type=int, default=500)
    return parser.parse_args()


def sentence_split(text: str) -> list[str]:
    return [part.strip() for part in SENTENCE_BOUNDARY_RE.split(text) if part.strip()]


def is_good_sentence(text: str, min_chars: int, max_chars: int) -> bool:
    if len(text) < min_chars or len(text) > max_chars:
        return False
    arabic_chars = len(ARABIC_LETTER_RE.findall(text))
    if arabic_chars < min_chars // 2:
        return False
    return arabic_chars / max(1, len(text)) >= 0.45


def get_text(row: dict[str, Any], text_field: str, title_field: str) -> str:
    parts = []
    if title_field and row.get(title_field):
        parts.append(str(row.get(title_field)))
    if row.get(text_field):
        parts.append(str(row.get(text_field)))
    return "\n".join(parts)


def load_records(dataset: str, config: str, split: str, streaming: bool):
    try:
        from datasets import load_dataset
    except ImportError as exc:
        raise SystemExit("Install datasets first: pip install datasets") from exc

    if config:
        return load_dataset(dataset, config, split=split, streaming=streaming)
    return load_dataset(dataset, split=split, streaming=streaming)


def main() -> None:
    args = parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)

    records = load_records(args.dataset, args.config, args.split, args.streaming)
    source_dataset = args.dataset if not args.config else f"{args.dataset}:{args.config}"
    source_name = args.source_name or source_dataset

    n_records = 0
    n_sentences = 0
    with args.output.open("w", encoding="utf-8") as out:
        for record_index, row in enumerate(records):
            if args.max_records and n_records >= args.max_records:
                break
            n_records += 1
            text = get_text(row, args.text_field, args.title_field)
            for sentence in sentence_split(text):
                if not is_good_sentence(sentence, args.min_chars, args.max_chars):
                    continue
                n_sentences += 1
                payload = {
                    "sentence_id": f"hf_{n_sentences:08d}",
                    "record_index": record_index,
                    "sentence": sentence,
                    "source_dataset": source_dataset,
                    "source": source_name,
                }
                for key in ["Article_Class", "Published Date", "Write_By", "Title"]:
                    if key in row:
                        payload[key] = row.get(key)
                out.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
                if args.max_sentences and n_sentences >= args.max_sentences:
                    break
            if args.log_every and n_records % args.log_every == 0:
                print(f"records={n_records} sentences={n_sentences}", flush=True)
            if args.max_sentences and n_sentences >= args.max_sentences:
                break

    print(f"wrote {args.output}")
    print(f"records={n_records} sentences={n_sentences}")


if __name__ == "__main__":
    main()
