#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/AhmedAbdel-Aal/arabic-morph-MI.git}"
WORKDIR="${WORKDIR:-/workspace/arabic-morph-MI}"
DATA_PATH="${DATA_PATH:-data/productivity_dataset.json}"
OUT_DIR="${OUT_DIR:-results}"
RUN_PREFIX="${RUN_PREFIX:-REP_$(date -u +%Y%m%dT%H%M%SZ)}"
BATCH_SIZE="${BATCH_SIZE:-1}"
REP_DTYPE="${REP_DTYPE:-float16}"
INSTALL="${INSTALL:-1}"

step() {
  printf "\n[%s] %s\n" "$(date -u +%H:%M:%S)" "$1"
}

run_exp() {
  local id="$1"
  local model="$2"
  local surface="$3"
  local real_split="$4"
  local run_id="${RUN_PREFIX}_${id}"

  step "Running ${run_id}"
  echo "model:      ${model}"
  echo "surface:    ${surface}"
  echo "real split: ${real_split}"
  echo "batch size: ${BATCH_SIZE}"
  echo "rep dtype:  ${REP_DTYPE}"

  python scripts/run_probes.py \
    --data "$DATA_PATH" \
    --model "$model" \
    --surface "$surface" \
    --pooling last \
    --real-split "$real_split" \
    --batch-size "$BATCH_SIZE" \
    --output-dir "$OUT_DIR" \
    --run-id "$run_id" \
    --save-representations \
    --representation-dtype "$REP_DTYPE"
}

step "Preparing repository"
echo "repo:       $REPO_URL"
echo "workdir:    $WORKDIR"
echo "run prefix: $RUN_PREFIX"

if [ -d "$WORKDIR/.git" ]; then
  git -C "$WORKDIR" pull --ff-only
else
  git clone "$REPO_URL" "$WORKDIR"
fi

cd "$WORKDIR"

if [ "$INSTALL" = "1" ]; then
  step "Installing dependencies"
  python -m pip install --upgrade pip
  python -m pip install -e .
  python -m pip install protobuf sentencepiece tiktoken
fi

step "Checking dataset"
if [ ! -f "$DATA_PATH" ]; then
  echo "Missing dataset: $WORKDIR/$DATA_PATH"
  exit 1
fi

step "Starting representation-saving runs"
run_exp "E03"  "Qwen/Qwen3-1.7B-Base"              "base" "item"
run_exp "E05b" "Qwen/Qwen3-1.7B-Base"              "full" "family"
run_exp "E06"  "Qwen/Qwen3-8B"                     "base" "item"
run_exp "E06b" "Qwen/Qwen3-8B"                     "full" "family"
run_exp "E07"  "QCRI/Fanar-1-9B"                   "base" "item"
run_exp "E07b" "QCRI/Fanar-1-9B"                   "full" "family"
run_exp "E08"  "humain-ai/ALLaM-7B-Instruct-preview" "base" "item"
run_exp "E08b" "humain-ai/ALLaM-7B-Instruct-preview" "full" "family"

step "Saved representation files"
find "$OUT_DIR" -path "*/hidden_representations.npz" -name "hidden_representations.npz" -print | sort | grep "$RUN_PREFIX" || true

step "Disk usage"
du -h "$OUT_DIR"/"${RUN_PREFIX}"_* 2>/dev/null || true

cat > "$OUT_DIR/${RUN_PREFIX}_DOWNLOAD.txt" <<EOF
Representation runs are saved under:
  $WORKDIR/$OUT_DIR/${RUN_PREFIX}_*

From your local machine, download them with:
  rsync -avz root@<RUNPOD_HOST>:$WORKDIR/$OUT_DIR/${RUN_PREFIX}_* ./results/

Or:
  scp -r root@<RUNPOD_HOST>:$WORKDIR/$OUT_DIR/${RUN_PREFIX}_* ./results/

These folders contain hidden_representations.npz files. They are intentionally gitignored.
EOF

step "Finished"
cat "$OUT_DIR/${RUN_PREFIX}_DOWNLOAD.txt"
