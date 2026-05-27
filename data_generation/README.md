# Data Generation Pipeline

This folder isolates the larger Akeel-style dataset generation work from the probing code.

The pipeline keeps one clean intermediate contract:

```text
Arabic Billion Words article records
-> sampled sentence JSONL
-> CAMEL-backed morphology candidates
-> token-level and type-level dataset views
```

The final dataset should still be audited before it is treated as gold. The scripts here produce candidates, not final linguistic truth.

## Folder Layout

```text
data_generation/
  scripts/
    sample_abw_sentences.py   # sample/split Arabic Billion Words text into sentences
    extract_candidates.py     # run CAMEL and extract root-template-affix candidates
    make_views.py             # create token-level and type-level views
    review_curated_dataset.py # second-pass flags for accepted curated rows
    apply_review_decisions.py # apply explicit reviewer accept/reject decisions
    summarize_source_expansion.py # rank/gate source-expansion runs before merge
    merge_candidate_files.py  # merge per-source candidate files after source checks
    print_multisource_commands.py # print the recommended multi-source run commands
    common.py                 # shared Arabic normalization and template logic
  runs/
    .gitkeep                  # generated data goes here and is gitignored
```

## Input Sentence Format

The extraction script expects JSONL where each line is one sentence:

```json
{"sentence_id":"abw_00000001","source_dataset":"oserikov/arabic_billion_words","record_index":0,"url":"...","date":"...","headline":"...","sentence":"..."}
```

Only `sentence_id` and `sentence` are required. The other fields are kept for provenance.

## Step 1: Sample Arabic Billion Words Sentences

Run this in an environment with `datasets` installed:

```bash
python data_generation/scripts/sample_abw_sentences.py \
  --config Almasryalyoum \
  --output data_generation/runs/abw_10k/sentences.jsonl \
  --max-records 2000 \
  --max-sentences 10000
```

Arabic Billion Words is hosted on Hugging Face as legacy dataset scripts. If you see:

```text
RuntimeError: Dataset scripts are no longer supported
```

then use an older `datasets` version for this sampling step:

```bash
uv pip install "datasets<4"
```

The source files are `.rar` archives, so this sampler intentionally does not use Hugging Face streaming by default. If extraction complains about `rarfile`, install:

```bash
uv pip install rarfile
```

On macOS, `rarfile` may also need an extraction backend:

```bash
brew install unar
```

Available ABW configs include:

```text
Alittihad, Almasryalyoum, Almustaqbal, Alqabas, Echoroukonline,
Ryiadh, Sabanews, SaudiYoum, Techreen, Youm7
```

You can also feed local article JSONL instead of Hugging Face:

```bash
python data_generation/scripts/sample_abw_sentences.py \
  --input-jsonl path/to/abw_records.jsonl \
  --output data_generation/runs/local_sample/sentences.jsonl \
  --max-sentences 10000
```

## Step 2: Extract CAMEL Candidates

Run this in the CAMEL environment:

```bash
python data_generation/scripts/extract_candidates.py \
  --sentences data_generation/runs/abw_10k/sentences.jsonl \
  --output data_generation/runs/abw_10k/candidates.jsonl \
  --report data_generation/runs/abw_10k/extraction_report.json \
  --filter-mode broad
```

The output is token-level: repeated words in different sentences remain separate rows.

Use `--filter-mode broad` for candidate discovery. Do not remove whole templates such as `فعال`, `فعيل`, or `فعول` at extraction time. Some rows in those templates are primitive lexical nouns, and some may be valid derived items. That distinction is made during item-level audit.

## Step 3: Make Token and Type Views

```bash
python data_generation/scripts/make_views.py \
  --candidates data_generation/runs/abw_10k/candidates.jsonl \
  --out-dir data_generation/runs/abw_10k/views
```

This writes:

```text
token_level.jsonl
type_level.jsonl
view_report.json
```

The type-level view deduplicates by root, template, canonical base, full form, prefix, suffix, and surface rule.
It also keeps sentence and source provenance so final exports can be audited by source.

## Step 4: Prepare Morphology Audit

Create audit hints and a diversified 500-item type-level sample:

```bash
python data_generation/scripts/prepare_morph_audit.py \
  --input data_generation/runs/abw_10k/views/type_level.jsonl \
  --annotated-output data_generation/runs/abw_10k_audit_v1/type_level_audit_prep.jsonl \
  --sample-output data_generation/runs/abw_10k_audit_v1/audit_sample_500.jsonl \
  --report data_generation/runs/abw_10k_audit_v1/audit_prep_report.json \
  --sample-size 500 \
  --seed 17
```

The audit is item-level. The reviewer labels whether a row is transparent derived morphology, a verbal noun/masdar, a primitive lexical item, a proper/place name, a context mismatch, or an analyzer/matcher error. See `AUDIT_PROTOCOL.md`.

For the current pilot counts and reviewer judgment, see:

```text
AUDIT_STATUS.md
CURRENT_DATA_REVIEW.md
SOURCE_EXPANSION_PLAN.md
```

## Multi-Source Pass

After the Almasryalyoum pilot, the next real data pass should run several ABW sources and then merge them.
Print the full command list with:

```bash
python data_generation/scripts/print_multisource_commands.py \
  --run-dir data_generation/runs/abw_multisource_v1
```

The default source set is:

```text
Alittihad, Alqabas, Ryiadh, Sabanews, Techreen
```

This command generator prints the sampling, CAMEL extraction, per-source views, candidate merge, combined views, audit prep, curated export, and family-balanced export commands.
It also prints a source-expansion summary command before the merge. That report should be checked before merging sources:

```text
data_generation/runs/abw_multisource_v1/source_expansion_summary.md
```

The source summary checks:

```text
type rows
unique roots
weak-template coverage for فعلان and مفعال
family-ready groups with one base plus at least two affixed variants
```

The intended final outputs are:

```text
data_generation/runs/abw_multisource_v1/audit_v1/curated_batch_001/productivity_dataset_multisource.json
data_generation/runs/abw_multisource_v1/audit_v1/family_balanced_001/productivity_dataset_multisource_family_balanced.json
```

Optionally build a small conservative seed of low-risk derived verbs:

```bash
python data_generation/scripts/build_conservative_seed.py \
  --input data_generation/runs/abw_10k_audit_v1/type_level_audit_prep.jsonl \
  --out-dir data_generation/runs/abw_10k_audit_v1/conservative_seed
```

## Step 5: Manual Audit UI

Start the local audit UI:

```bash
python data_generation/scripts/audit_server.py \
  --sample data_generation/runs/abw_10k_audit_v1/audit_sample_500.jsonl \
  --audit-state data_generation/runs/abw_10k_audit_v1/audit_state.json \
  --port 8765
```

Open:

```text
http://127.0.0.1:8765
```

The UI writes audit decisions continuously:

```text
audit_state.json       # current editable state
audit_summary.json     # counts by decision/reason/morphology class/dataset use/template
audited_items.jsonl    # all reviewed rows with audit labels
accepted_items.jsonl   # reviewed rows marked accept
rejected_items.jsonl   # reviewed rows marked reject
unsure_items.jsonl     # reviewed rows marked unsure
main_target_items.jsonl           # accepted rows for the main target-pattern dataset
secondary_primitive_items.jsonl   # accepted primitive lexical comparison rows
excluded_items.jsonl              # rejected/excluded rows
audited_items.csv      # spreadsheet-friendly reviewed rows
```

## Step 6: Second-Pass Curated Review

After building a curated batch, run a reviewer pass over every accepted row:

```bash
python data_generation/scripts/review_curated_dataset.py \
  --input data_generation/runs/abw_10k_audit_v1/curated_batch_001/accepted_batch_001.jsonl \
  --out-dir data_generation/runs/abw_10k_audit_v1/review_pass_001
```

This writes:

```text
all_reviewed_rows.jsonl
low_risk_accepts.jsonl
review_queue.jsonl
review_queue.csv
productivity_dataset_low_risk.json
review_report.json
review_report.md
```

Then apply explicit reviewer decisions:

```bash
python data_generation/scripts/apply_review_decisions.py \
  --reviewed-rows data_generation/runs/abw_10k_audit_v1/review_pass_001/all_reviewed_rows.jsonl \
  --decisions data_generation/runs/abw_10k_audit_v1/review_pass_001/manual_review_decisions_001.jsonl \
  --out-dir data_generation/runs/abw_10k_audit_v1/review_pass_001/decision_applied_001
```

The current Almasryalyoum pilot review state is:

```text
accepted after second-pass review: 623
rejected after second-pass review: 2
remaining review queue: 0
missing sentence/source fields: 0
```

The current best reviewed pilot export is:

```text
data_generation/runs/abw_10k_audit_v1/review_pass_001/decision_applied_002/productivity_dataset_reviewed.json
```

See `PILOT_HANDOFF.md` for the current reviewed pilot counts and the next multi-source step.

The current multi-source interim handoff is:

```text
data_generation/MULTISOURCE_HANDOFF.md
data_generation/runs/abw_multisource_v1/audit_v1/review_pass_001/decision_applied_001/productivity_dataset_reviewed.json
```

It currently includes Almasryalyoum, Alittihad, Sabanews, and Techreen.

## Notes

- Arabic Billion Words is article-level text, not pre-annotated morphology.
- CAMEL supplies candidate roots and analyses.
- The template matcher maps candidate roots to our controlled template inventory.
- `canonical_base_form` is the root-template form before affix spelling rules.
- `base_form` is the same as `canonical_base_form`, kept for compatibility with the probing loader.
- `surface_stem` is the bound stem after spelling rules, e.g. `كتابت`.
- `full_form` is the observed surface word, e.g. `كتابتها`.
- Generated `runs/` files are ignored by git because they can become large.
