# Current Data Review

Review date: 2026-05-22

## Current Pilot Source

```text
oserikov/arabic_billion_words:Almasryalyoum
sentences: 10,000
token-level candidates: 34,489
type-level candidates: 6,599
```

This source is useful for validating the pipeline, but it is not enough for the final study because all accepted examples currently come from one newspaper domain:

```text
today.almasryalyoum.com
```

## Clean Curated Batch

Current main candidate dataset:

```text
data_generation/runs/abw_10k_audit_v1/curated_batch_001/productivity_dataset_batch_001.json
```

Current size:

```text
rows: 625
roots: 163
templates: 12
```

Template distribution:

```text
افتعال: 119
فعالة: 71
مفعول: 67
مفتعل: 66
استفعل: 62
انفعل: 52
فاعل: 43
فعول: 41
فعيل: 39
فعلاء: 32
فعال: 27
مفعال: 6
```

This is the best current broad dataset for probing because it keeps sentence context and source provenance, and it uses explicit curated allowlists plus CAMEL agreement checks.

## Second-Pass Reviewed Pilot

The best current pilot handoff is now the second-pass reviewed export:

```text
data_generation/runs/abw_10k_audit_v1/review_pass_001/decision_applied_002/productivity_dataset_reviewed.json
```

Current size:

```text
rows: 623
roots: 162
templates: 12
missing sentence fields: 0
missing source fields: 0
remaining review queue: 0
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

This export has no unresolved rows from the current Almasryalyoum pilot. It includes explicit reviewer decisions for all rows that were previously queued.

Rejected after second-pass review:

```text
وخادم       -> lexicalized honorific title: خادم الحرمين
بالمرصاد   -> lexicalized fixed expression
```

Pilot handoff summary:

```text
data_generation/PILOT_HANDOFF.md
```

## Strict Family-Balanced View

Current reviewed family-balanced dataset:

```text
data_generation/runs/abw_10k_audit_v1/review_pass_001/decision_applied_002/family_balanced/productivity_dataset_family_balanced_reviewed.json
```

Current size:

```text
rows: 198
families: 66
roots: 57
templates: 6
```

Family-balanced template coverage:

```text
افتعال: 28 families
استفعل: 10 families
مفتعل: 10 families
مفعول: 10 families
انفعل: 7 families
مفعال: 1 family
```

This view is stricter because every family must have one base row and two affixed variants. It is cleaner for affix-control experiments, but too small and template-skewed to be the main final dataset.

## What Was Fixed

The audit hint script had an over-broad name/place heuristic:

- `replace` was incorrectly triggering `place`.
- `علماء` was incorrectly triggering `علم`.
- common-country glosses such as `country;countries` were too broad for name detection.

This was fixed by only using CAMEL POS `noun_prop` and exact English gloss/POS tokens such as `proper`, `name`, `proper_name`, `person`, and `nationality`.

The audit hint script now also flags CAMEL/POS disagreement:

```text
camel_pos_mismatch
```

These rows are moved to high-review hints instead of being suggested as clean main targets.

The curated batch builder now also enforces target-class/POS compatibility and a vocalized CAMEL-pattern check for `فاعل`. This removed rows such as verbs under the active-participle allowlist and `للعالمين`, where CAMEL's vocalized pattern is `عالَم` rather than `عالِم`.

Three context-specific proper-name failures were explicitly rejected:

```text
مصباح قطب
وسليمان سعد
محيي الدين الغريب
```

The active-participle base `صالح` was also removed from the current pilot batch. The accepted examples were fixed expressions such as `لصالح الفريق` and `للصالح العام`, not clean active-participle usages.

The broken-plural/verbal-noun pass removed additional context failures:

```text
بكتابه
بالكتاب والسنة
انتصار حسين
ببلاده
```

The remaining `كتاب` rows are kept only where the context supports `كتاب` as “writers/authors,” not “book.”

## Current Scientific Judgment

Do not use the rule:

```text
template = transparent / primitive / bad
```

That is not precise enough.

Use this rule instead:

```text
row = word + root + template + CAMEL analysis + sentence context
```

Each row can then be:

- clean target morphology
- primitive or lexicalized comparison item
- proper/name/place item
- context mismatch
- analyzer/template/POS error

The main probing dataset should include only clean target morphology. Primitive/lexicalized items can be saved separately as a comparison set, but should not be mixed into the main target rows.

## Known Weak Spots

`فعلان` is still missing from the strict curated batch. The Almasryalyoum sample has candidates, but the observed examples are mostly unsuitable:

- colloquial or informal forms such as `زعلانين`
- named-entity/title contexts such as `فرحان`
- nisba/adjectival artifacts such as `العلماني` and `العمراني`
- POS mismatches such as `لبناني` and `لثماني`
- high-ambiguity or non-target nouns

This should be solved by adding more sources or targeted review, not by weakening the filters.

`مفعال` exists but is very small. It needs more sources.

The family-balanced dataset is missing many noun/adjective templates because this 10k-sentence pilot often has only affixed variants or only unaffixed variants for a family.

## Next Action

The next data step should be source expansion, not relaxing the audit.

Use additional Arabic Billion Words sources:

```text
Alittihad
Alqabas
Ryiadh
Sabanews
Techreen
```

Then merge type-level candidates and rerun the same audit/curation logic. The goal is to increase coverage while keeping the same scientific standard.
