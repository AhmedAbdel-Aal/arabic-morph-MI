# Balanced50 Dataset Handoff

This is the current probing-ready dataset for the larger Arabic morphology probing study.

## Main File

```text
data_generation/runs/balanced50_v1/productivity_dataset_balanced50.json
```

Use this file when the experiment needs the same number of real contextual examples for every target template.

## Size

```text
rows: 650
templates: 13
rows per template: 50
roots: 215
families: 284
nonce rows: 0
```

Template distribution:

```text
استفعل: 50
افتعال: 50
انفعل: 50
فاعل: 50
فعال: 50
فعالة: 50
فعلاء: 50
فعلان: 50
فعول: 50
فعيل: 50
مفتعل: 50
مفعال: 50
مفعول: 50
```

## How It Was Built

The builder starts from the reviewed v3 accepted rows:

```text
data_generation/runs/abw_multisource_v3_controlled_f3lan/accepted_combined_reviewed.jsonl
```

It then adds controlled, manually written MSA examples only for templates that do not have 50 reviewed natural rows. Every controlled example is validated by CAMEL plus the local root-template matcher before export.

Builder script:

```text
data_generation/scripts/build_balanced50_dataset.py
```

Command:

```text
../.venv/bin/python data_generation/scripts/build_balanced50_dataset.py
```

## Controlled Rows

The final selected dataset contains controlled rows for these templates:

```text
فعلان: 50
مفعال: 43
فعال: 16
فعول: 6
فعيل: 4
فاعل: 2
فعلاء: 2
```

Source distribution:

```text
oserikov/arabic_billion_words:Alittihad:       293
oserikov/arabic_billion_words:Almasryalyoum:   101
oserikov/arabic_billion_words:Echoroukonline:   61
oserikov/arabic_billion_words:Techreen:         45
oserikov/arabic_billion_words:Sabanews:         27
controlled_manual:balanced50_v1:               105
controlled_manual:f3lan_v1:                     18
```

Interpretation rule: this file is valid for balanced all-template probing, but results for `فعلان` and `مفعال` must be discussed as controlled-source-sensitive. Natural-source-only conclusions should use the v2 reviewed handoff, where `فعلان` is absent.

## Validation

Validation checks passed on the emitted JSON:

```text
real rows: 650
nonce rows: 0
templates: 13
missing root/template/base/full/prefix/suffix/sentence/source fields: 0
```

Supporting files:

```text
data_generation/runs/balanced50_v1/selected_rows.jsonl
data_generation/runs/balanced50_v1/controlled_supplement.jsonl
data_generation/runs/balanced50_v1/balanced50_report.json
data_generation/runs/balanced50_v1/README.md
```
