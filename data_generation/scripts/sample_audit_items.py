#!/usr/bin/env python3
"""Create a stratified manual-audit sample from type-level candidates."""

from __future__ import annotations

import argparse
import random
from collections import defaultdict
from pathlib import Path
from typing import Any

from common import read_jsonl, write_jsonl


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--n", type=int, default=500)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--min-per-template", type=int, default=20)
    return parser.parse_args()


def allocate_counts(groups: dict[str, list[dict[str, Any]]], n: int, min_per_template: int) -> dict[str, int]:
    allocations = {key: min(len(rows), min_per_template) for key, rows in groups.items()}
    allocated = sum(allocations.values())

    if allocated > n:
        allocations = {key: 0 for key in groups}
        order = sorted(groups, key=lambda key: len(groups[key]))
        while sum(allocations.values()) < n:
            changed = False
            for key in order:
                if allocations[key] < len(groups[key]):
                    allocations[key] += 1
                    changed = True
                    if sum(allocations.values()) == n:
                        break
            if not changed:
                break
        return allocations

    remaining = n - allocated
    capacities = {key: len(rows) - allocations[key] for key, rows in groups.items()}
    while remaining > 0 and any(capacity > 0 for capacity in capacities.values()):
        total_capacity = sum(cap for cap in capacities.values() if cap > 0)
        additions: dict[str, int] = {}
        for key, capacity in capacities.items():
            if capacity <= 0:
                additions[key] = 0
                continue
            proportional = max(1, round(remaining * capacity / total_capacity))
            additions[key] = min(capacity, proportional)

        for key in sorted(additions, key=lambda k: len(groups[k]), reverse=True):
            if remaining <= 0:
                break
            add = min(additions[key], remaining)
            allocations[key] += add
            capacities[key] -= add
            remaining -= add

    return allocations


def main() -> None:
    args = parse_args()
    rows = list(read_jsonl(args.input))
    if args.n > len(rows):
        raise SystemExit(f"Requested {args.n} rows, but input only has {len(rows)} rows.")

    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for index, row in enumerate(rows):
        row = dict(row)
        row["_source_index"] = index
        groups[row.get("template", "")].append(row)

    rng = random.Random(args.seed)
    allocations = allocate_counts(groups, args.n, args.min_per_template)
    sampled: list[dict[str, Any]] = []
    for template, group_rows in sorted(groups.items()):
        selected = rng.sample(group_rows, allocations[template])
        sampled.extend(selected)

    rng.shuffle(sampled)
    for audit_index, row in enumerate(sampled, 1):
        row["audit_id"] = f"audit_{audit_index:04d}"
        row["audit_sample_seed"] = args.seed
        row["audit_sample_strategy"] = "template_stratified"

    write_jsonl(args.output, sampled)

    print(f"wrote {args.output}")
    print(f"sampled={len(sampled)} from input={len(rows)}")
    for template in sorted(allocations):
        print(f"{template}: {allocations[template]}")


if __name__ == "__main__":
    main()
