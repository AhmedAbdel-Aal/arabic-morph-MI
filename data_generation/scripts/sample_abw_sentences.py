#!/usr/bin/env python3
"""Sample sentence JSONL from Arabic Billion Words style article records."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import urllib.request
from pathlib import Path
from urllib.parse import urlparse


SENTENCE_BOUNDARY_RE = re.compile(r"(?<=[.!؟?؛…])\s+|\n+")
ARABIC_LETTER_RE = re.compile(r"[\u0621-\u064A]")
ABW_ORIGINAL_URL = "http://abuelkhair.net/corpus/{config}_XML_utf_8.rar"
TAG_LABELS = {
    "Dateline": ["Dateline", "dateline"],
    "Headline": ["Headline", "Healine"],
    "Text": ["Text"],
    "URL": ["URL"],
}
TAG_PATTERNS = {
    tag: [re.compile(rf".*?<{label}>(.*?)</{label}>.*?", re.MULTILINE | re.DOTALL) for label in labels]
    for tag, labels in TAG_LABELS.items()
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--input-jsonl", type=Path, help="Optional local article JSONL instead of Hugging Face.")
    parser.add_argument("--dataset", default="oserikov/arabic_billion_words")
    parser.add_argument(
        "--config",
        default="Almasryalyoum",
        help="Arabic Billion Words newspaper subset, e.g. Almasryalyoum, Youm7, Alittihad.",
    )
    parser.add_argument("--split", default="train")
    parser.add_argument("--max-records", type=int, default=1000)
    parser.add_argument("--max-sentences", type=int, default=5000)
    parser.add_argument("--min-chars", type=int, default=25)
    parser.add_argument("--max-chars", type=int, default=350)
    parser.add_argument("--text-field", default="text")
    parser.add_argument(
        "--abw-cache-dir",
        type=Path,
        default=Path("data_generation/runs/abw_source_cache"),
        help="Cache directory for direct original Abu El-Khair archive fallback.",
    )
    parser.add_argument(
        "--no-original-url-fallback",
        action="store_true",
        help="Disable fallback to the original Abu El-Khair archive if the HF mirror URL is missing.",
    )
    parser.add_argument(
        "--prefer-original-url",
        action="store_true",
        help="For Arabic Billion Words, bypass Hugging Face loading and read the original archive XML directly.",
    )
    parser.add_argument(
        "--streaming",
        action="store_true",
        help="Use Hugging Face streaming. Do not use this for Arabic Billion Words because its source files are RAR archives.",
    )
    parser.add_argument("--log-every", type=int, default=500)
    return parser.parse_args()


def iter_local_jsonl(path: Path):
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def iter_hf_dataset(name: str, config: str, split: str, streaming: bool):
    try:
        import datasets
        from datasets import load_dataset
    except ImportError as exc:
        raise SystemExit("Install datasets first: pip install datasets") from exc
    try:
        return load_dataset(name, config, split=split, streaming=streaming, trust_remote_code=True)
    except TypeError:
        return load_dataset(name, config, split=split, streaming=streaming)
    except NotImplementedError as exc:
        if "rar" in str(exc).lower():
            raise SystemExit(
                "\n".join(
                    [
                        "Arabic Billion Words is distributed as .rar archives.",
                        "Hugging Face streaming cannot extract RAR files.",
                        "",
                        "Rerun without --streaming. If extraction then complains about rarfile, install:",
                        "  uv pip install rarfile",
                        "",
                        "On macOS, rarfile also needs an extraction backend. If needed:",
                        "  brew install unar",
                    ]
                )
            ) from exc
        raise
    except ImportError as exc:
        if "rarfile" in str(exc).lower():
            raise SystemExit(
                "\n".join(
                    [
                        "Arabic Billion Words is distributed as .rar archives.",
                        "Install the Python RAR helper:",
                        "  uv pip install rarfile",
                        "",
                        "On macOS, rarfile also needs an extraction backend. If needed:",
                        "  brew install unar",
                    ]
                )
            ) from exc
        raise
    except Exception as exc:
        if exc.__class__.__name__ in {"BadRarFile", "RarCannotExec", "RarExecError"}:
            backend_hint = "unar is available" if shutil.which("unar") else "unar is not installed"
            raise SystemExit(
                "\n".join(
                    [
                        "RAR extraction failed while loading Arabic Billion Words.",
                        f"Detected RAR backend status: {backend_hint}.",
                        "",
                        "On macOS, install a real RAR extraction backend:",
                        "  brew install unar",
                        "",
                        "Then remove the partial empty extraction cache and rerun:",
                        "  rm -rf ~/.cache/huggingface/datasets/downloads/extracted/*",
                        "",
                        "The partial cache cleanup is needed because the failed run created a 0-byte XML file.",
                    ]
                )
            ) from exc
        raise
    except RuntimeError as exc:
        message = str(exc)
        if "Dataset scripts are no longer supported" in message:
            raise SystemExit(
                "\n".join(
                    [
                        f"{name} still uses an old Hugging Face dataset loading script.",
                        f"Your installed datasets version is {datasets.__version__}, which no longer runs dataset scripts.",
                        "",
                        "Use an older datasets version for this sampling step:",
                        '  uv pip install "datasets<4"',
                        "",
                        "Then rerun, for example:",
                        "  python data_generation/scripts/sample_abw_sentences.py \\",
                        "    --config Almasryalyoum \\",
                        "    --output data_generation/runs/abw_10k/sentences.jsonl \\",
                        "    --max-records 2000 \\",
                        "    --max-sentences 10000",
                        "",
                        "Alternative: prepare article records yourself as JSONL and pass --input-jsonl.",
                    ]
                )
            ) from exc
        raise


def download_file(url: str, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists() and output.stat().st_size > 0 and is_rar_archive(output):
        return
    if output.exists() and output.stat().st_size > 0:
        output.unlink()
    tmp = output.with_suffix(output.suffix + ".partial")
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 arabic-morph-mi-data-generation",
            "Accept": "*/*",
        },
    )
    with urllib.request.urlopen(request) as response, tmp.open("wb") as out:
        shutil.copyfileobj(response, out)
    tmp.replace(output)
    if not is_rar_archive(output):
        raise SystemExit(
            "\n".join(
                [
                    f"Downloaded {url}, but it is not a RAR archive.",
                    f"Cached file: {output}",
                    "The source may be unavailable or returning an HTML error page.",
                ]
            )
        )


def is_rar_archive(path: Path) -> bool:
    with path.open("rb") as f:
        return f.read(7).startswith(b"Rar!\x1a\x07")


def ensure_original_abw_xml(config: str, cache_dir: Path) -> Path:
    try:
        import rarfile
    except ImportError as exc:
        raise SystemExit(
            "\n".join(
                [
                    "Direct Arabic Billion Words fallback needs rarfile.",
                    "Install it with:",
                    "  uv pip install rarfile",
                    "",
                    "On macOS, rarfile also needs an extraction backend:",
                    "  brew install unar",
                ]
            )
        ) from exc

    cache_dir.mkdir(parents=True, exist_ok=True)
    rar_path = cache_dir / f"{config}_XML_utf_8.rar"
    extract_dir = cache_dir / config
    xml_path = extract_dir / f"{config}_utf_8.xml"
    if xml_path.exists() and xml_path.stat().st_size > 0:
        return xml_path

    url = ABW_ORIGINAL_URL.format(config=config)
    print(f"HF mirror missing; downloading original archive {url}", flush=True)
    download_file(url, rar_path)

    extract_dir.mkdir(parents=True, exist_ok=True)
    try:
        with rarfile.RarFile(rar_path) as archive:
            archive.extractall(extract_dir)
    except Exception as exc:
        backend_hint = "unar is available" if shutil.which("unar") else "unar is not installed"
        raise SystemExit(
            "\n".join(
                [
                    f"Failed to extract {rar_path}.",
                    f"Detected RAR backend status: {backend_hint}.",
                    "",
                    "On macOS, install a real RAR extraction backend:",
                    "  brew install unar",
                ]
            )
        ) from exc

    if not xml_path.exists():
        candidates = sorted(extract_dir.glob("*.xml"))
        if len(candidates) == 1:
            return candidates[0]
        raise SystemExit(f"Could not find expected XML file after extraction: {xml_path}")
    return xml_path


def clean_text(text: str) -> str:
    return str(text or "").replace("?", "")


def extract_tag(tag: str, text: str) -> str:
    for pattern in TAG_PATTERNS[tag]:
        match = pattern.match(text)
        if match:
            return match.group(1)
    return ""


def iter_original_abw_records(config: str, cache_dir: Path):
    xml_path = ensure_original_abw_xml(config, cache_dir)
    data_tag = config
    pattern = re.compile(rf".*?<{data_tag}(.*?)</{data_tag}.*?", re.MULTILINE | re.DOTALL)
    buffer = ""
    with xml_path.open(encoding="utf-8") as f:
        for line in f:
            buffer += line
            if f"</{data_tag}" not in line:
                continue
            match = pattern.match(buffer)
            buffer = ""
            if not match:
                continue
            record = match.group(1)
            yield {
                "url": extract_tag("URL", record),
                "head_line": clean_text(extract_tag("Headline", record)),
                "date": extract_tag("Dateline", record),
                "text": clean_text(extract_tag("Text", record)),
            }


def split_sentences(text: str) -> list[str]:
    sentences = []
    for part in SENTENCE_BOUNDARY_RE.split(str(text or "")):
        sentence = " ".join(part.split())
        if sentence:
            sentences.append(sentence)
    return sentences


def source_from_url(url: str | None) -> str:
    if not url:
        return ""
    host = urlparse(url).netloc
    return host.removeprefix("www.")


def has_arabic(text: str) -> bool:
    return bool(ARABIC_LETTER_RE.search(text))


def main() -> None:
    args = parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)

    if args.input_jsonl:
        records = iter_local_jsonl(args.input_jsonl)
        source_dataset = str(args.input_jsonl)
    elif args.prefer_original_url:
        if args.no_original_url_fallback or args.dataset != "oserikov/arabic_billion_words":
            raise SystemExit("--prefer-original-url is only supported for Arabic Billion Words with fallback enabled.")
        records = iter_original_abw_records(args.config, args.abw_cache_dir)
        source_dataset = f"{args.dataset}:{args.config}"
    else:
        try:
            records = iter_hf_dataset(args.dataset, args.config, args.split, streaming=args.streaming)
        except FileNotFoundError:
            if args.no_original_url_fallback or args.dataset != "oserikov/arabic_billion_words":
                raise
            records = iter_original_abw_records(args.config, args.abw_cache_dir)
        source_dataset = f"{args.dataset}:{args.config}"

    seen_sentences: set[str] = set()
    n_records = 0
    n_sentences = 0

    with args.output.open("w", encoding="utf-8") as out:
        for record in records:
            if args.max_records and n_records >= args.max_records:
                break
            n_records += 1
            text = record.get(args.text_field, "")
            for sentence in split_sentences(text):
                if len(sentence) < args.min_chars or len(sentence) > args.max_chars:
                    continue
                if not has_arabic(sentence):
                    continue
                if sentence in seen_sentences:
                    continue
                seen_sentences.add(sentence)
                row = {
                    "sentence_id": f"abw_{n_sentences:08d}",
                    "source_dataset": source_dataset,
                    "record_index": n_records - 1,
                    "source": source_from_url(record.get("url")),
                    "url": record.get("url", ""),
                    "date": record.get("date", ""),
                    "headline": record.get("head_line", ""),
                    "sentence": sentence,
                }
                out.write(json.dumps(row, ensure_ascii=False, sort_keys=True))
                out.write("\n")
                n_sentences += 1
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
