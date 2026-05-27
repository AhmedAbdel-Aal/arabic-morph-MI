# Morphology Audit Protocol

This audit is item-level, not template-level.

We are not asking whether a template such as `فعال` or `فعيل` is valid in Arabic. We are asking whether this specific row is a clean item for the experiment.

## Unit To Audit

Audit the type-level rows first:

```text
data_generation/runs/abw_10k_audit_v1/type_level_audit_prep.jsonl
```

Each row is one candidate defined by:

```text
root + template + canonical base + surface stem + full form + prefix + suffix + sentence context
```

The token-level file is useful for provenance and repeated contexts, but it is not the first audit target because repeated words would waste review time.

## Audit Question

For each row, decide:

1. Is the root correct?
2. Is the template assignment correct enough for our controlled inventory?
3. Is the affix parse correct?
4. Does the sentence context support the CAMEL/root/template reading?
5. What kind of morphology item is this?
6. Should it enter the main probing dataset, a secondary/control dataset, or be excluded?

## Morphology Classes

Use these labels in the audit UI.

```text
target_broken_plural
target_form_x_verb
target_form_vii_verb
target_active_participle
target_passive_participle
target_form_viii_participle
target_verbal_noun
target_intensive_adjective
target_instrument_noun
```

Use these for rows that cleanly instantiate one of the target Akeel-style pattern classes.

Examples:

```text
رجال، زملاء، حقوق
استبعد، انخفض
كاتب، معروف، مختلف
اختبار، كتابة
كبير، فرحان
مفتاح، منظار
```

```text
primitive_lexical
```

Use for common lexical nouns that can have a valid Arabic wazn but are not instances of the target pattern class we need for the main experiment.

Example:

```text
تراب
```

This is not “wrong Arabic morphology.” It is just a different class from the controlled target-pattern rows.

```text
proper_name_or_place
```

Use for people, countries, cities, named entities, and nationalities when they are not useful as controlled morphology items.

```text
foreign_or_loanword
```

Use for foreign words, Arabized names, or obvious loanwords that should not be treated as clean root-pattern items.

```text
context_mismatch
```

Use when CAMEL gives a possible analysis but the sentence meaning is different.

Example:

```text
باسم الحكومة
```

CAMEL may analyze `باسم` as “smiling” from `ب.س.م`, but in this context it means “in the name of / on behalf of.”

```text
wrong_root
wrong_template
bad_affix_parse
non_target
unsure
```

Use these when the analyzer/matcher is wrong, the row is outside scope, or the reviewer cannot decide.

## Dataset Use

```text
main_target
```

Only for accepted rows with:

```text
target_* classes
```

These are the main experiment rows.

```text
secondary_primitive
```

Only for accepted primitive lexical rows. Keep them separate as a comparison/control set.

```text
exclude
```

For names, context mismatches, wrong roots/templates, bad affix parses, foreign/loanword rows, and non-target items.

```text
needs_review
```

For unresolved rows.

## Current Generated Files

The broad extracted data is:

```text
data_generation/runs/abw_10k_broad/
```

Current audit-prepared files are:

```text
data_generation/runs/abw_10k_audit_v1/type_level_audit_prep.jsonl
data_generation/runs/abw_10k_audit_v1/audit_sample_500.jsonl
data_generation/runs/abw_10k_audit_v1/audit_prep_report.json
```

A very conservative seed was also produced:

```text
data_generation/runs/abw_10k_audit_v1/conservative_seed/main_target_seed.jsonl
data_generation/runs/abw_10k_audit_v1/conservative_seed/review_queue.jsonl
data_generation/runs/abw_10k_audit_v1/conservative_seed/seed_report.json
```

The seed accepts only low-risk derived verbs where CAMEL and the tagger agree on a verb reading. It is intentionally small and should be spot-checked before use.

The first curated reviewed batch is:

```text
data_generation/runs/abw_10k_audit_v1/curated_batch_001/accepted_batch_001.jsonl
data_generation/runs/abw_10k_audit_v1/curated_batch_001/productivity_dataset_batch_001.json
data_generation/runs/abw_10k_audit_v1/curated_batch_001/batch_001_report.json
```

This batch uses explicit base-form allowlists for each target pattern class. It excludes obvious primitive lexical rows, nisba/template mismatches, POS mismatches, high-ambiguity rows, and rows where CAMEL's own pattern does not agree with the target template.

The current strict Almasryalyoum batch covers 12 of the 13 target templates. `فعلان` should be treated as a source/sample coverage gap until we find clean, MSA, context-supported examples. Do not lower the filters just to make every template appear.

## Reviewer Principle

Do not audit by saying “this template is transparent” or “this template is primitive.” Audit the row.

A valid row is:

```text
specific word + root + template + CAMEL analysis + sentence context
```

The same template can contain clean target morphology, lexicalized/primitive words, proper names, dialectal forms, dual/plural artifacts, or analyzer errors. For this study, the main dataset should keep clean target-pattern items and exclude or separately store the others.

## Commands

Regenerate type/token views with CAMEL analysis preserved:

```bash
python3 data_generation/scripts/make_views.py \
  --candidates data_generation/runs/abw_10k_broad/candidates.jsonl \
  --out-dir data_generation/runs/abw_10k_broad/views
```

Prepare audit hints and a balanced 500-row sample:

```bash
python3 data_generation/scripts/prepare_morph_audit.py \
  --input data_generation/runs/abw_10k_broad/views/type_level.jsonl \
  --annotated-output data_generation/runs/abw_10k_audit_v1/type_level_audit_prep.jsonl \
  --sample-output data_generation/runs/abw_10k_audit_v1/audit_sample_500.jsonl \
  --report data_generation/runs/abw_10k_audit_v1/audit_prep_report.json \
  --sample-size 500 \
  --seed 17
```

Build the conservative seed:

```bash
python3 data_generation/scripts/build_conservative_seed.py \
  --input data_generation/runs/abw_10k_audit_v1/type_level_audit_prep.jsonl \
  --out-dir data_generation/runs/abw_10k_audit_v1/conservative_seed
```

Start the audit UI:

```bash
python3 data_generation/scripts/audit_server.py \
  --sample data_generation/runs/abw_10k_audit_v1/audit_sample_500.jsonl \
  --audit-state data_generation/runs/abw_10k_audit_v1/audit_state.json \
  --port 8765
```

Open:

```text
http://127.0.0.1:8765
```

## Source Expansion Plan

Do not scale to all sources before validating this audit protocol on the current Almasryalyoum sample.

After the pilot audit is stable, add more Arabic Billion Words configs to avoid one-outlet/source bias. Prioritize MSA news sources from different regions:

```text
Alittihad
Alqabas
Ryiadh
Sabanews
Techreen
```

Then optionally add:

```text
Youm7
Almustaqbal
SaudiYoum
Echoroukonline
```

Keep source metadata in the final dataset and cap per source/root/template so a single newspaper or repeated political vocabulary does not dominate the experiments.
