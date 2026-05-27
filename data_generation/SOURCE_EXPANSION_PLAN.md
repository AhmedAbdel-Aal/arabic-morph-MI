# Source Expansion Plan

The original pilot used only:

```text
oserikov/arabic_billion_words:Almasryalyoum
```

That was enough to validate the pipeline, but not enough for the final study. The current run has expanded to four usable ABW sources while keeping the same extraction and audit rules.

## Current Source Status

Processed and merged:

```text
Almasryalyoum
Alittihad
Sabanews
Techreen
```

Attempted but currently unavailable:

```text
Alqabas  -> HF mirror 404; original archive URL returned HTML, not RAR.
Ryiadh   -> HF mirror unavailable; original archive URL returned HTML, not RAR.
```

Current reviewed multi-source handoff:

```text
data_generation/MULTISOURCE_HANDOFF.md
data_generation/runs/abw_multisource_v1/audit_v1/review_pass_001/decision_applied_001/productivity_dataset_reviewed.json
```

Add these later if needed:

```text
Youm7
Almustaqbal
SaudiYoum
Echoroukonline
```

Reason:

- They can add useful coverage.
- They may introduce more repeated local vocabulary, names, or dialectal/editorial artifacts, so they should be audited after the stricter sources.

## Per-Source Pilot Command

Run each source into its own folder first:

```bash
python data_generation/scripts/sample_abw_sentences.py \
  --config Alittihad \
  --output data_generation/runs/abw_sources/Alittihad/sentences.jsonl \
  --max-records 2000 \
  --max-sentences 10000
```

Then extract candidates:

```bash
python data_generation/scripts/extract_candidates.py \
  --sentences data_generation/runs/abw_sources/Alittihad/sentences.jsonl \
  --output data_generation/runs/abw_sources/Alittihad/candidates.jsonl \
  --report data_generation/runs/abw_sources/Alittihad/extraction_report.json \
  --filter-mode broad
```

Then build views:

```bash
python data_generation/scripts/make_views.py \
  --candidates data_generation/runs/abw_sources/Alittihad/candidates.jsonl \
  --out-dir data_generation/runs/abw_sources/Alittihad/views
```

Repeat for each source. Do not merge before checking per-source extraction counts.

To avoid hand-building the full command list, use:

```bash
python data_generation/scripts/print_multisource_commands.py \
  --run-dir data_generation/runs/abw_multisource_v1
```

By default this prints commands for:

```text
Alittihad, Alqabas, Ryiadh, Sabanews, Techreen
```

In practice, merge only sources whose `source_expansion_summary.md` recommendation is `merge_candidate_pool_after_audit`.

## Acceptance Gates

For a source to be useful, it should add at least one of:

- New clean roots for already stable templates.
- Clean examples for weak templates, especially `فعلان` and `مفعال`.
- More complete families with one base form and at least two affixed variants.
- Context diversity for the same root/template forms.

Reject or downweight a source if it mostly adds:

- Proper names and place names.
- Dialect-heavy forms.
- Repeated near-duplicate articles.
- High-CAMEL-ambiguity rows that need too much manual intervention.

After per-source views are built, generate the source gate report:

```bash
python data_generation/scripts/summarize_source_expansion.py \
  --run-dir data_generation/runs/abw_multisource_v1 \
  --current-reviewed-json data_generation/runs/abw_multisource_v1/audit_v1/review_pass_001/decision_applied_001/productivity_dataset_reviewed.json \
  --output data_generation/runs/abw_multisource_v1/source_expansion_summary.json \
  --markdown data_generation/runs/abw_multisource_v1/source_expansion_summary.md
```

This report is the pre-merge checkpoint. It should show whether each source adds:

```text
فعلان candidates
مفعال candidates
new roots/templates
family-ready groups
```

The current four-source combined pool has raw `فعلان` candidates but no accepted reviewed `فعلان` row, so future sources should be judged especially by whether they yield clean `فعلان` candidates under review.

## Later Source Attempt Notes

A later expansion test was attempted after the four-source handoff:

```text
Youm7         -> original archive URL returned HTML instead of a RAR archive.
SaudiYoum     -> archive reached extraction, but local HF cache/RAR extraction failed.
Almustaqbal   -> attempted, but local disk filled during HF dataset preparation.
Echoroukonline -> succeeded after freeing Hugging Face extracted-cache space.
```

At the time of the attempt the local filesystem had only about 373 MB free, while the Hugging Face dataset cache used about 9 GB:

```text
/Users/ahmed/.cache/huggingface/datasets: 9.0G
/Users/ahmed/.cache/huggingface/datasets/downloads/extracted: 5.3G
```

Before retrying large later sources locally, free cache space first or run the sampling stage on a machine with more disk. Do not interpret disk-full failures as linguistic/source-quality failures.

The sampler now supports bypassing Hugging Face's full Arrow-cache preparation:

```bash
python data_generation/scripts/sample_abw_sentences.py \
  --config Echoroukonline \
  --prefer-original-url \
  --output data_generation/runs/abw_multisource_v1/sources/Echoroukonline/sentences.jsonl \
  --max-records 2000 \
  --max-sentences 10000
```

Use this mode for large later ABW sources when local disk is tight.

`Echoroukonline` was sampled and extracted as:

```text
data_generation/runs/abw_multisource_v1/sources/Echoroukonline/sentences.jsonl
data_generation/runs/abw_multisource_v1/sources/Echoroukonline/candidates.jsonl
data_generation/runs/abw_multisource_v1/sources/Echoroukonline/views/type_level.jsonl
```

Source-gate result:

```text
sentences: 10,000
token candidates: 36,390
type candidates: 6,712
unique roots: 957
family-ready groups: 699
raw فعلان type candidates: 118
raw مفعال type candidates: 20
recommendation: merge_candidate_pool_after_audit
```

Focused `فعلان` audit for this source:

```text
data_generation/runs/abw_multisource_v1/sources/Echoroukonline/audit/f3lan_audit/f3lan_audit_report.md
```

Result:

```text
فعلان type rows audited: 118
accepted: 0
rejected: 118
```

So `Echoroukonline` is useful for broader root/family coverage, but it does not solve the clean `فعلان` gap.

Direct original-archive retries for the remaining later sources failed because the original URLs returned HTML instead of RAR archives:

```text
SaudiYoum
Almustaqbal
Youm7
```

These may still work through the Hugging Face mirror on a machine with more disk, but they are not practical on the current local disk state. Because both v1 and Echoroukonline failed to yield clean natural `فعلان`, a controlled supplement was added as a separate, explicitly marked source:

```text
source_dataset=controlled_manual:f3lan_v1
data_generation/V3_CONTROLLED_F3LAN_HANDOFF.md
```

## Final Merge Rule

The final dataset should not simply concatenate sources. After per-source extraction:

1. Merge type-level candidates across sources.
2. Re-run audit preparation and curated selection.
3. Cap rows per `source_dataset + root + template + base_form`.
4. Keep sentence provenance for every accepted row.
5. Export both a broad curated dataset and a strict family-balanced dataset.

The source metadata must remain in the final probing JSON so later analyses can check whether a model result is driven by morphology rather than one newspaper's vocabulary.

The merge step is handled by:

```bash
python data_generation/scripts/merge_candidate_files.py \
  --inputs data_generation/runs/abw_10k_broad/candidates.jsonl data_generation/runs/abw_multisource_v1/sources/Alittihad/candidates.jsonl data_generation/runs/abw_multisource_v1/sources/Sabanews/candidates.jsonl data_generation/runs/abw_multisource_v1/sources/Techreen/candidates.jsonl \
  --output data_generation/runs/abw_multisource_v1/combined/candidates.jsonl \
  --report data_generation/runs/abw_multisource_v1/combined/merge_report.json
```

The command generator prints the complete version with all selected sources.
