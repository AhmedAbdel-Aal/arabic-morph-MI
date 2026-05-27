#!/usr/bin/env bash
set -euo pipefail

OUTPUT_DIR="${OUTPUT_DIR:-results/final}"
BATCH_SIZE="${BATCH_SIZE:-1}"
DTYPE="${DTYPE:-auto}"
SAVE_REPRESENTATIONS="${SAVE_REPRESENTATIONS:-1}"
MODEL_SET="${MODEL_SET:-core}"
RUN_BASE_DIAGNOSTICS="${RUN_BASE_DIAGNOSTICS:-0}"
RUN_EVERYTHING="${RUN_EVERYTHING:-0}"
STATUS_FILE="${STATUS_FILE:-$OUTPUT_DIR/RUN_STATUS.md}"
LOG_DIR="${LOG_DIR:-$OUTPUT_DIR/logs}"
STATE_DIR="${STATE_DIR:-$OUTPUT_DIR/.run_state}"

if [ "$RUN_EVERYTHING" = "1" ]; then
  MODEL_SET="all"
  RUN_BASE_DIAGNOSTICS="1"
fi

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
)

EXTENDED_MODEL_IDS=(
  "llama3_8b"
  "acegpt7b"
)

step() {
  printf "\n[%s] %s\n" "$(date -u +%H:%M:%S)" "$1"
}

now_utc() {
  date -u +"%Y-%m-%d %H:%M:%S UTC"
}

safe_name() {
  printf "%s" "$1" | tr -c '[:alnum:]_.-' '_'
}

PLANNED_RUNS=()

add_plan() {
  local dataset_id="$1"
  local data_path="$2"
  local model="$3"
  local model_id="$4"
  local surface="$5"
  local real_split="$6"
  local run_id="${dataset_id}_${model_id}_${surface}_last_${real_split}"
  PLANNED_RUNS+=("${run_id}|${dataset_id}|${data_path}|${model}|${model_id}|${surface}|${real_split}")
}

run_state() {
  local run_id="$1"
  local state_file="$STATE_DIR/$(safe_name "$run_id").state"
  if [ -f "$state_file" ]; then
    cat "$state_file"
  else
    printf "pending"
  fi
}

state_icon() {
  case "$1" in
    done) printf "done" ;;
    skipped) printf "skipped" ;;
    running) printf "running" ;;
    failed) printf "failed" ;;
    *) printf "pending" ;;
  esac
}

render_status() {
  mkdir -p "$(dirname "$STATUS_FILE")" "$LOG_DIR" "$STATE_DIR"
  local tmp="${STATUS_FILE}.tmp"
  local total="${#PLANNED_RUNS[@]}"
  local done_count=0
  local skipped_count=0
  local running_count=0
  local failed_count=0
  local pending_count=0

  for spec in "${PLANNED_RUNS[@]}"; do
    IFS='|' read -r run_id _dataset_id _data_path _model _model_id _surface _real_split <<< "$spec"
    case "$(run_state "$run_id")" in
      done) done_count=$((done_count + 1)) ;;
      skipped) skipped_count=$((skipped_count + 1)) ;;
      running) running_count=$((running_count + 1)) ;;
      failed) failed_count=$((failed_count + 1)) ;;
      *) pending_count=$((pending_count + 1)) ;;
    esac
  done

  {
    echo "# Final Experiment Run Status"
    echo
    echo "Last updated: $(now_utc)"
    echo
    echo "Configuration:"
    echo
    echo '```text'
    echo "MODEL_SET=$MODEL_SET"
    echo "RUN_EVERYTHING=$RUN_EVERYTHING"
    echo "OUTPUT_DIR=$OUTPUT_DIR"
    echo "BATCH_SIZE=$BATCH_SIZE"
    echo "DTYPE=$DTYPE"
    echo "SAVE_REPRESENTATIONS=$SAVE_REPRESENTATIONS"
    echo "RUN_BASE_DIAGNOSTICS=$RUN_BASE_DIAGNOSTICS"
    echo '```'
    echo
    echo "Progress:"
    echo
    echo '```text'
    echo "total:   $total"
    echo "done:    $done_count"
    echo "skipped: $skipped_count"
    echo "running: $running_count"
    echo "failed:  $failed_count"
    echo "pending: $pending_count"
    echo '```'
    echo
    echo "Monitor commands:"
    echo
    echo '```bash'
    echo "watch -n 20 'sed -n \"1,220p\" $STATUS_FILE'"
    echo "tail -f $LOG_DIR/<run_id>.log"
    echo '```'
    echo
    echo "| State | Run | Model | Dataset | Surface | Split | Log |"
    echo "|---|---|---|---|---|---|---|"
    for spec in "${PLANNED_RUNS[@]}"; do
      IFS='|' read -r run_id dataset_id _data_path model _model_id surface real_split <<< "$spec"
      local state
      state="$(run_state "$run_id")"
      local log_path="$LOG_DIR/${run_id}.log"
      echo "| $(state_icon "$state") | \`$run_id\` | \`$model\` | \`$dataset_id\` | \`$surface\` | \`$real_split\` | \`$log_path\` |"
    done
    echo
    if [ -f "$STATE_DIR/events.log" ]; then
      echo "## Event Log"
      echo
      echo '```text'
      tail -40 "$STATE_DIR/events.log"
      echo '```'
    fi
  } > "$tmp"
  mv "$tmp" "$STATUS_FILE"
}

set_run_state() {
  local run_id="$1"
  local state="$2"
  local message="${3:-}"
  mkdir -p "$STATE_DIR"
  printf "%s" "$state" > "$STATE_DIR/$(safe_name "$run_id").state"
  printf "[%s] %-8s %s %s\n" "$(now_utc)" "$state" "$run_id" "$message" >> "$STATE_DIR/events.log"
  render_status
}

build_plan() {
  PLANNED_RUNS=()
  for i in "${!MODELS[@]}"; do
    local model="${MODELS[$i]}"
    local model_id="${MODEL_IDS[$i]}"

    add_plan "AKEEL30" "data/productivity_dataset.json" "$model" "$model_id" "full" "family"
    add_plan "NATURAL100" "data/productivity_dataset_natural_almost100.json" "$model" "$model_id" "full" "family"

    if [ "$RUN_BASE_DIAGNOSTICS" = "1" ]; then
      add_plan "AKEEL30" "data/productivity_dataset.json" "$model" "$model_id" "base" "item"
      add_plan "NATURAL100" "data/productivity_dataset_natural_almost100.json" "$model" "$model_id" "base" "item"
    fi
  done
}

run_probe() {
  local dataset_id="$1"
  local data_path="$2"
  local model="$3"
  local model_id="$4"
  local surface="$5"
  local real_split="$6"
  local run_id="${dataset_id}_${model_id}_${surface}_last_${real_split}"
  local run_dir="$OUTPUT_DIR/$run_id"
  local log_file="$LOG_DIR/${run_id}.log"

  if [ -f "$run_dir/results.json" ]; then
    step "Skipping ${run_id}; results already exist"
    set_run_state "$run_id" "skipped" "results.json already exists"
    return 0
  fi
  if [ -d "$run_dir" ]; then
    step "Blocking ${run_id}; partial output folder exists"
    set_run_state "$run_id" "failed" "partial output exists at $run_dir"
    echo "Partial output folder exists: $run_dir" >&2
    echo "Move/remove it or set OUTPUT_DIR to a fresh path, then rerun." >&2
    return 2
  fi

  step "Running ${run_id}"
  set_run_state "$run_id" "running" "started"
  mkdir -p "$LOG_DIR"
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
  {
    echo "started: $(now_utc)"
    echo "run_id: $run_id"
    echo "model: $model"
    echo "data: $data_path"
    echo "command: ${cmd[*]}"
    echo
  } > "$log_file"

  set +e
  "${cmd[@]}" 2>&1 | tee -a "$log_file"
  local exit_code="${PIPESTATUS[0]}"
  set -e

  if [ "$exit_code" -eq 0 ]; then
    {
      echo
      echo "finished: $(now_utc)"
      echo "status: success"
    } >> "$log_file"
    set_run_state "$run_id" "done" "finished successfully"
  else
    {
      echo
      echo "finished: $(now_utc)"
      echo "status: failed"
      echo "exit_code: $exit_code"
    } >> "$log_file"
    set_run_state "$run_id" "failed" "exit_code=$exit_code"
    return "$exit_code"
  fi
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

build_plan
render_status
step "Status file: $STATUS_FILE"

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
render_status
find "$OUTPUT_DIR" -maxdepth 2 -type f -print | sort
