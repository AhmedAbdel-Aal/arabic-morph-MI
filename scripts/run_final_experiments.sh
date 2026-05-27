#!/usr/bin/env bash
set -euo pipefail

OUTPUT_DIR="${OUTPUT_DIR:-results/final}"
BATCH_SIZE="${BATCH_SIZE:-1}"
DTYPE="${DTYPE:-auto}"
SAVE_REPRESENTATIONS="${SAVE_REPRESENTATIONS:-1}"
MODEL_SET="${MODEL_SET:-core}"
RUN_BASE_DIAGNOSTICS="${RUN_BASE_DIAGNOSTICS:-0}"

CORE_MODELS=(
  "Qwen/Qwen3-1.7B-Base"
  "Qwen/Qwen3-8B"
  "QCRI/Fanar-1-9B"
  "humain-ai/ALLaM-7B-Instruct-preview"
)

CORE_MODEL_IDS=(
  "qwen17b"
  "qwen8b"
  "fanar9b"
  "allam7b"
)

EXTENDED_MODELS=(
  "meta-llama/Meta-Llama-3-8B"
  "FreedomIntelligence/AceGPT-7B"
  "inceptionai/jais-13b"
)

EXTENDED_MODEL_IDS=(
  "llama3_8b"
  "acegpt7b"
  "jais13b"
)

step() {
  printf "\n[%s] %s\n" "$(date -u +%H:%M:%S)" "$1"
}

run_probe() {
  local dataset_id="$1"
  local data_path="$2"
  local model="$3"
  local model_id="$4"
  local surface="$5"
  local real_split="$6"
  local run_id="${dataset_id}_${model_id}_${surface}_last_${real_split}"

  step "Running ${run_id}"
  cmd=(
    python scripts/run_probes.py
    --data "$data_path"
    --model "$model"
    --surface "$surface"
    --pooling last
    --real-split "$real_split"
    --batch-size "$BATCH_SIZE"
    --dtype "$DTYPE"
    --output-dir "$OUTPUT_DIR"
    --run-id "$run_id"
  )
  if [ "$SAVE_REPRESENTATIONS" = "1" ]; then
    cmd+=(--save-representations)
  fi
  "${cmd[@]}"
}

if [ "$MODEL_SET" = "core" ]; then
  MODELS=("${CORE_MODELS[@]}")
  MODEL_IDS=("${CORE_MODEL_IDS[@]}")
elif [ "$MODEL_SET" = "extended" ]; then
  MODELS=("${EXTENDED_MODELS[@]}")
  MODEL_IDS=("${EXTENDED_MODEL_IDS[@]}")
elif [ "$MODEL_SET" = "all" ]; then
  MODELS=("${CORE_MODELS[@]}" "${EXTENDED_MODELS[@]}")
  MODEL_IDS=("${CORE_MODEL_IDS[@]}" "${EXTENDED_MODEL_IDS[@]}")
else
  echo "MODEL_SET must be 'core', 'extended', or 'all', got: $MODEL_SET" >&2
  exit 1
fi

for i in "${!MODELS[@]}"; do
  model="${MODELS[$i]}"
  model_id="${MODEL_IDS[$i]}"

  run_probe "AKEEL30" "data/productivity_dataset.json" "$model" "$model_id" "full" "family"
  run_probe "NATURAL100" "data/productivity_dataset_natural_almost100.json" "$model" "$model_id" "full" "family"

  if [ "$RUN_BASE_DIAGNOSTICS" = "1" ]; then
    run_probe "AKEEL30" "data/productivity_dataset.json" "$model" "$model_id" "base" "item"
    run_probe "NATURAL100" "data/productivity_dataset_natural_almost100.json" "$model" "$model_id" "base" "item"
  fi
done

step "Finished final experiment matrix"
find "$OUTPUT_DIR" -maxdepth 2 -type f -print | sort
