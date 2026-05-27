#!/usr/bin/env python3
"""Print reproducible commands for the Arabic Billion Words multi-source pass."""

from __future__ import annotations

import argparse
from pathlib import Path


DEFAULT_SOURCES = ["Alittihad", "Alqabas", "Ryiadh", "Sabanews", "Techreen"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", default="data_generation/runs/abw_multisource_v1", type=Path)
    parser.add_argument("--sources", nargs="+", default=DEFAULT_SOURCES)
    parser.add_argument("--max-records", type=int, default=2000)
    parser.add_argument("--max-sentences", type=int, default=10000)
    parser.add_argument("--sample-python", default="python")
    parser.add_argument("--camel-python", default="python")
    parser.add_argument(
        "--current-reviewed-json",
        default="data_generation/runs/abw_10k_audit_v1/review_pass_001/decision_applied_002/productivity_dataset_reviewed.json",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_dir = args.run_dir

    print("# 1. Sample sentences. Run in the environment with datasets<4 and RAR support.")
    for source in args.sources:
        source_dir = run_dir / "sources" / source
        print(
            " ".join(
                [
                    args.sample_python,
                    "data_generation/scripts/sample_abw_sentences.py",
                    "--config",
                    source,
                    "--output",
                    str(source_dir / "sentences.jsonl"),
                    "--max-records",
                    str(args.max_records),
                    "--max-sentences",
                    str(args.max_sentences),
                ]
            )
        )

    print("\n# 2. Extract candidates. Run in the CAMEL environment.")
    for source in args.sources:
        source_dir = run_dir / "sources" / source
        print(
            " ".join(
                [
                    args.camel_python,
                    "data_generation/scripts/extract_candidates.py",
                    "--sentences",
                    str(source_dir / "sentences.jsonl"),
                    "--output",
                    str(source_dir / "candidates.jsonl"),
                    "--report",
                    str(source_dir / "extraction_report.json"),
                    "--filter-mode",
                    "broad",
                ]
            )
        )

    print("\n# 3. Build per-source views.")
    for source in args.sources:
        source_dir = run_dir / "sources" / source
        print(
            " ".join(
                [
                    args.camel_python,
                    "data_generation/scripts/make_views.py",
                    "--candidates",
                    str(source_dir / "candidates.jsonl"),
                    "--out-dir",
                    str(source_dir / "views"),
                ]
            )
        )

    print("\n# 3b. Summarize per-source coverage before merging.")
    print(
        " ".join(
            [
                args.camel_python,
                "data_generation/scripts/summarize_source_expansion.py",
                "--run-dir",
                str(run_dir),
                "--current-reviewed-json",
                str(args.current_reviewed_json),
                "--output",
                str(run_dir / "source_expansion_summary.json"),
                "--markdown",
                str(run_dir / "source_expansion_summary.md"),
            ]
        )
    )

    candidate_inputs = " ".join(str(run_dir / "sources" / source / "candidates.jsonl") for source in args.sources)
    print("\n# 4. Merge candidates and rebuild combined views.")
    print(
        " ".join(
            [
                args.camel_python,
                "data_generation/scripts/merge_candidate_files.py",
                "--inputs",
                candidate_inputs,
                "--output",
                str(run_dir / "combined" / "candidates.jsonl"),
                "--report",
                str(run_dir / "combined" / "merge_report.json"),
            ]
        )
    )
    print(
        " ".join(
            [
                args.camel_python,
                "data_generation/scripts/make_views.py",
                "--candidates",
                str(run_dir / "combined" / "candidates.jsonl"),
                "--out-dir",
                str(run_dir / "combined" / "views"),
            ]
        )
    )

    audit_dir = run_dir / "audit_v1"
    print("\n# 5. Prepare audit, build curated data, and export probing JSON.")
    print(
        " ".join(
            [
                args.camel_python,
                "data_generation/scripts/prepare_morph_audit.py",
                "--input",
                str(run_dir / "combined" / "views" / "type_level.jsonl"),
                "--annotated-output",
                str(audit_dir / "type_level_audit_prep.jsonl"),
                "--sample-output",
                str(audit_dir / "audit_sample_500.jsonl"),
                "--report",
                str(audit_dir / "audit_prep_report.json"),
                "--sample-size",
                "500",
                "--seed",
                "17",
            ]
        )
    )
    print(
        " ".join(
            [
                args.camel_python,
                "data_generation/scripts/build_curated_batch.py",
                "--input",
                str(audit_dir / "type_level_audit_prep.jsonl"),
                "--out-dir",
                str(audit_dir / "curated_batch_001"),
                "--max-per-base",
                "4",
            ]
        )
    )
    print(
        " ".join(
            [
                args.camel_python,
                "data_generation/scripts/export_productivity_dataset.py",
                "--input",
                str(audit_dir / "curated_batch_001" / "accepted_batch_001.jsonl"),
                "--output",
                str(audit_dir / "curated_batch_001" / "productivity_dataset_multisource.json"),
                "--root-category",
                "audited_abw_multisource_v1",
            ]
        )
    )
    print(
        " ".join(
            [
                args.camel_python,
                "data_generation/scripts/build_family_balanced_dataset.py",
                "--input",
                str(audit_dir / "curated_batch_001" / "accepted_batch_001.jsonl"),
                "--out-dir",
                str(audit_dir / "family_balanced_001"),
                "--affixed-per-family",
                "2",
            ]
        )
    )
    print(
        " ".join(
            [
                args.camel_python,
                "data_generation/scripts/export_productivity_dataset.py",
                "--input",
                str(audit_dir / "family_balanced_001" / "family_balanced_rows.jsonl"),
                "--output",
                str(audit_dir / "family_balanced_001" / "productivity_dataset_multisource_family_balanced.json"),
                "--root-category",
                "audited_abw_multisource_v1_family_balanced",
            ]
        )
    )


if __name__ == "__main__":
    main()
