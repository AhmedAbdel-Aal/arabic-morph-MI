# Final Experiment Run Status

Last updated: 2026-05-31 16:33:44 UTC

Configuration:

```text
MODEL_SET=all
RUN_EVERYTHING=1
OUTPUT_DIR=results/final_everything
BATCH_SIZE=8
DTYPE=auto
SAVE_REPRESENTATIONS=1
RUN_BASE_DIAGNOSTICS=1
```

Progress:

```text
total:   24
done:    24
skipped: 0
running: 0
failed:  0
pending: 0
```

Monitor commands:

```bash
watch -n 20 'sed -n "1,220p" results/final_everything/RUN_STATUS.md'
tail -f results/final_everything/logs/<run_id>.log
```

| State | Run | Model | Dataset | Surface | Split | Log |
|---|---|---|---|---|---|---|
| done | `AKEEL30_qwen17b_full_last_family` | `Qwen/Qwen3-1.7B-Base` | `AKEEL30` | `full` | `family` | `results/final_everything/logs/AKEEL30_qwen17b_full_last_family.log` |
| done | `NATURAL100_qwen17b_full_last_family` | `Qwen/Qwen3-1.7B-Base` | `NATURAL100` | `full` | `family` | `results/final_everything/logs/NATURAL100_qwen17b_full_last_family.log` |
| done | `AKEEL30_qwen17b_base_last_item` | `Qwen/Qwen3-1.7B-Base` | `AKEEL30` | `base` | `item` | `results/final_everything/logs/AKEEL30_qwen17b_base_last_item.log` |
| done | `NATURAL100_qwen17b_base_last_item` | `Qwen/Qwen3-1.7B-Base` | `NATURAL100` | `base` | `item` | `results/final_everything/logs/NATURAL100_qwen17b_base_last_item.log` |
| done | `AKEEL30_qwen8b_full_last_family` | `Qwen/Qwen3-8B` | `AKEEL30` | `full` | `family` | `results/final_everything/logs/AKEEL30_qwen8b_full_last_family.log` |
| done | `NATURAL100_qwen8b_full_last_family` | `Qwen/Qwen3-8B` | `NATURAL100` | `full` | `family` | `results/final_everything/logs/NATURAL100_qwen8b_full_last_family.log` |
| done | `AKEEL30_qwen8b_base_last_item` | `Qwen/Qwen3-8B` | `AKEEL30` | `base` | `item` | `results/final_everything/logs/AKEEL30_qwen8b_base_last_item.log` |
| done | `NATURAL100_qwen8b_base_last_item` | `Qwen/Qwen3-8B` | `NATURAL100` | `base` | `item` | `results/final_everything/logs/NATURAL100_qwen8b_base_last_item.log` |
| done | `AKEEL30_fanar9b_full_last_family` | `QCRI/Fanar-1-9B` | `AKEEL30` | `full` | `family` | `results/final_everything/logs/AKEEL30_fanar9b_full_last_family.log` |
| done | `NATURAL100_fanar9b_full_last_family` | `QCRI/Fanar-1-9B` | `NATURAL100` | `full` | `family` | `results/final_everything/logs/NATURAL100_fanar9b_full_last_family.log` |
| done | `AKEEL30_fanar9b_base_last_item` | `QCRI/Fanar-1-9B` | `AKEEL30` | `base` | `item` | `results/final_everything/logs/AKEEL30_fanar9b_base_last_item.log` |
| done | `NATURAL100_fanar9b_base_last_item` | `QCRI/Fanar-1-9B` | `NATURAL100` | `base` | `item` | `results/final_everything/logs/NATURAL100_fanar9b_base_last_item.log` |
| done | `AKEEL30_allam7b_full_last_family` | `humain-ai/ALLaM-7B-Instruct-preview` | `AKEEL30` | `full` | `family` | `results/final_everything/logs/AKEEL30_allam7b_full_last_family.log` |
| done | `NATURAL100_allam7b_full_last_family` | `humain-ai/ALLaM-7B-Instruct-preview` | `NATURAL100` | `full` | `family` | `results/final_everything/logs/NATURAL100_allam7b_full_last_family.log` |
| done | `AKEEL30_allam7b_base_last_item` | `humain-ai/ALLaM-7B-Instruct-preview` | `AKEEL30` | `base` | `item` | `results/final_everything/logs/AKEEL30_allam7b_base_last_item.log` |
| done | `NATURAL100_allam7b_base_last_item` | `humain-ai/ALLaM-7B-Instruct-preview` | `NATURAL100` | `base` | `item` | `results/final_everything/logs/NATURAL100_allam7b_base_last_item.log` |
| done | `AKEEL30_llama3_8b_full_last_family` | `meta-llama/Meta-Llama-3-8B` | `AKEEL30` | `full` | `family` | `results/final_everything/logs/AKEEL30_llama3_8b_full_last_family.log` |
| done | `NATURAL100_llama3_8b_full_last_family` | `meta-llama/Meta-Llama-3-8B` | `NATURAL100` | `full` | `family` | `results/final_everything/logs/NATURAL100_llama3_8b_full_last_family.log` |
| done | `AKEEL30_llama3_8b_base_last_item` | `meta-llama/Meta-Llama-3-8B` | `AKEEL30` | `base` | `item` | `results/final_everything/logs/AKEEL30_llama3_8b_base_last_item.log` |
| done | `NATURAL100_llama3_8b_base_last_item` | `meta-llama/Meta-Llama-3-8B` | `NATURAL100` | `base` | `item` | `results/final_everything/logs/NATURAL100_llama3_8b_base_last_item.log` |
| done | `AKEEL30_acegpt7b_full_last_family` | `FreedomIntelligence/AceGPT-7B` | `AKEEL30` | `full` | `family` | `results/final_everything/logs/AKEEL30_acegpt7b_full_last_family.log` |
| done | `NATURAL100_acegpt7b_full_last_family` | `FreedomIntelligence/AceGPT-7B` | `NATURAL100` | `full` | `family` | `results/final_everything/logs/NATURAL100_acegpt7b_full_last_family.log` |
| done | `AKEEL30_acegpt7b_base_last_item` | `FreedomIntelligence/AceGPT-7B` | `AKEEL30` | `base` | `item` | `results/final_everything/logs/AKEEL30_acegpt7b_base_last_item.log` |
| done | `NATURAL100_acegpt7b_base_last_item` | `FreedomIntelligence/AceGPT-7B` | `NATURAL100` | `base` | `item` | `results/final_everything/logs/NATURAL100_acegpt7b_base_last_item.log` |

## Event Log

```text
[2026-05-31 15:10:18 UTC] running  AKEEL30_qwen8b_full_last_family started
[2026-05-31 15:16:28 UTC] done     AKEEL30_qwen8b_full_last_family finished successfully
[2026-05-31 15:16:28 UTC] running  NATURAL100_qwen8b_full_last_family started
[2026-05-31 15:18:43 UTC] done     NATURAL100_qwen8b_full_last_family finished successfully
[2026-05-31 15:18:43 UTC] running  AKEEL30_qwen8b_base_last_item started
[2026-05-31 15:24:39 UTC] done     AKEEL30_qwen8b_base_last_item finished successfully
[2026-05-31 15:24:39 UTC] running  NATURAL100_qwen8b_base_last_item started
[2026-05-31 15:26:51 UTC] done     NATURAL100_qwen8b_base_last_item finished successfully
[2026-05-31 15:26:51 UTC] running  AKEEL30_fanar9b_full_last_family started
[2026-05-31 15:33:00 UTC] done     AKEEL30_fanar9b_full_last_family finished successfully
[2026-05-31 15:33:01 UTC] running  NATURAL100_fanar9b_full_last_family started
[2026-05-31 15:35:19 UTC] done     NATURAL100_fanar9b_full_last_family finished successfully
[2026-05-31 15:35:19 UTC] running  AKEEL30_fanar9b_base_last_item started
[2026-05-31 15:41:30 UTC] done     AKEEL30_fanar9b_base_last_item finished successfully
[2026-05-31 15:41:30 UTC] running  NATURAL100_fanar9b_base_last_item started
[2026-05-31 15:43:45 UTC] done     NATURAL100_fanar9b_base_last_item finished successfully
[2026-05-31 15:43:46 UTC] running  AKEEL30_allam7b_full_last_family started
[2026-05-31 15:49:59 UTC] done     AKEEL30_allam7b_full_last_family finished successfully
[2026-05-31 15:49:59 UTC] running  NATURAL100_allam7b_full_last_family started
[2026-05-31 15:52:14 UTC] done     NATURAL100_allam7b_full_last_family finished successfully
[2026-05-31 15:52:14 UTC] running  AKEEL30_allam7b_base_last_item started
[2026-05-31 15:58:19 UTC] done     AKEEL30_allam7b_base_last_item finished successfully
[2026-05-31 15:58:19 UTC] running  NATURAL100_allam7b_base_last_item started
[2026-05-31 16:00:31 UTC] done     NATURAL100_allam7b_base_last_item finished successfully
[2026-05-31 16:00:31 UTC] running  AKEEL30_llama3_8b_full_last_family started
[2026-05-31 16:06:34 UTC] done     AKEEL30_llama3_8b_full_last_family finished successfully
[2026-05-31 16:06:34 UTC] running  NATURAL100_llama3_8b_full_last_family started
[2026-05-31 16:08:48 UTC] done     NATURAL100_llama3_8b_full_last_family finished successfully
[2026-05-31 16:08:48 UTC] running  AKEEL30_llama3_8b_base_last_item started
[2026-05-31 16:15:03 UTC] done     AKEEL30_llama3_8b_base_last_item finished successfully
[2026-05-31 16:15:03 UTC] running  NATURAL100_llama3_8b_base_last_item started
[2026-05-31 16:17:17 UTC] done     NATURAL100_llama3_8b_base_last_item finished successfully
[2026-05-31 16:17:18 UTC] running  AKEEL30_acegpt7b_full_last_family started
[2026-05-31 16:23:20 UTC] done     AKEEL30_acegpt7b_full_last_family finished successfully
[2026-05-31 16:23:21 UTC] running  NATURAL100_acegpt7b_full_last_family started
[2026-05-31 16:25:33 UTC] done     NATURAL100_acegpt7b_full_last_family finished successfully
[2026-05-31 16:25:34 UTC] running  AKEEL30_acegpt7b_base_last_item started
[2026-05-31 16:31:33 UTC] done     AKEEL30_acegpt7b_base_last_item finished successfully
[2026-05-31 16:31:34 UTC] running  NATURAL100_acegpt7b_base_last_item started
[2026-05-31 16:33:43 UTC] done     NATURAL100_acegpt7b_base_last_item finished successfully
```
