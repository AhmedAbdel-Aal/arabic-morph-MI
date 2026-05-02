#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/AhmedAbdel-Aal/arabic-morph-MI.git}"
WORKDIR="${WORKDIR:-/content/arabic-morph-MI}"
MODEL="${MODEL:-Qwen/Qwen3-1.7B-Base}"
SURFACE="${SURFACE:-base}"
BATCH_SIZE="${BATCH_SIZE:-4}"
DATA_PATH="${DATA_PATH:-data/productivity_dataset.json}"

step() {
  printf "\n[%s] %s\n" "$(date -u +%H:%M:%S)" "$1"
}

step "Starting Colab run"
echo "repo:       $REPO_URL"
echo "workdir:    $WORKDIR"
echo "model:      $MODEL"
echo "surface:    $SURFACE"
echo "batch size: $BATCH_SIZE"
echo "data path:  $DATA_PATH"

step "Cloning or updating repository"
if [ -d "$WORKDIR/.git" ]; then
  git -C "$WORKDIR" pull --ff-only
else
  git clone "$REPO_URL" "$WORKDIR"
fi

cd "$WORKDIR"

step "Installing Python dependencies"
python -m pip install --upgrade pip
python -m pip install -e .

step "Checking dataset"
if [ ! -f "$DATA_PATH" ]; then
  echo "Missing dataset: $WORKDIR/$DATA_PATH"
  echo "Upload productivity_dataset.json to $WORKDIR/data/ or set DATA_PATH."
  exit 1
fi

step "Dataset summary"
python - <<'PY'
import json
from collections import Counter
from pathlib import Path

path = Path("data/productivity_dataset.json")
payload = json.loads(path.read_text(encoding="utf-8"))
for key in ["real_roots", "nonce_roots"]:
    rows = payload[key]
    counts = Counter(row["template"] for row in rows)
    print(f"{key}: {len(rows)} rows, {len(counts)} templates")
    print(dict(sorted(counts.items())))
PY

step "Running probes"
python scripts/run_probes.py \
  --data "$DATA_PATH" \
  --model "$MODEL" \
  --surface "$SURFACE" \
  --batch-size "$BATCH_SIZE"

step "Finished"
find results -maxdepth 2 -type f -print | sort | tail -20
