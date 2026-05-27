# Reviewed Pilot Handoff

This document records the current clean handoff state for the Almasryalyoum pilot.
It is suitable for pilot experiments and pipeline validation.
It is not the final large dataset because it still comes from one source.

## Source

```text
oserikov/arabic_billion_words:Almasryalyoum
sampled sentences: 10,000
```

## Main Reviewed Dataset

```text
data_generation/runs/abw_10k_audit_v1/review_pass_001/decision_applied_002/productivity_dataset_reviewed.json
```

Counts:

```text
rows: 623
roots: 162
templates: 12
missing sentence fields: 0
missing source fields: 0
remaining review queue: 0
rejected after second-pass review: 2
```

Template distribution:

```text
افتعال: 119
فعالة: 71
مفعول: 67
مفتعل: 66
استفعل: 62
انفعل: 52
فاعل: 42
فعول: 41
فعيل: 39
فعلاء: 32
فعال: 27
مفعال: 5
```

Rejected rows:

```text
وخادم       فاعل   rejected as lexicalized honorific title: خادم الحرمين
بالمرصاد   مفعال  rejected as lexicalized fixed expression
```

The reviewed data includes explicit decisions for all previously queued rows:

```text
data_generation/runs/abw_10k_audit_v1/review_pass_001/manual_review_decisions_001_002.jsonl
```

## Family-Balanced Reviewed Dataset

```text
data_generation/runs/abw_10k_audit_v1/review_pass_001/decision_applied_002/family_balanced/productivity_dataset_family_balanced_reviewed.json
```

Counts:

```text
rows: 198
roots: 57
families: 66
```

This view is useful for affix-family experiments but is still too small and template-skewed as the only final dataset.

## Scientific Judgment

The pilot is clean enough for local probing checks and for validating the full pipeline.
It should not be treated as the final paper dataset because it has one-source bias and weak coverage for:

```text
فعلان
مفعال
noun/adjective family-balanced variants
```

The next required step is multi-source expansion with the same audit standard.
The source-expansion baseline report is:

```text
data_generation/runs/abw_10k_audit_v1/source_expansion_baseline/source_expansion_summary.md
```

Key baseline lesson:

```text
Almasryalyoum raw type-level candidates include فعلان=85 and مفعال=14.
The reviewed handoff still has no clean فعلان row and only مفعال=5.
```

So the next sources should be judged by whether they add clean weak-template rows after audit, not merely by raw candidate counts.

Recommended next sources:

```text
Alittihad
Alqabas
Ryiadh
Sabanews
Techreen
```

Generate the commands with:

```bash
python data_generation/scripts/print_multisource_commands.py \
  --run-dir data_generation/runs/abw_multisource_v1
```
