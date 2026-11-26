# Changelog

## v2.1.0

- Replies of the extraction and the data verification that cannot be parsed are requested again with identical settings, up to three attempts. The rule is applied to every set, and the records and tables are updated: 586 three-family certificates over the four sets (was 581), 516 after data verification (was 513).
- Runs on human-written texts: IndustryOR and Mamo ComplexLP in their published releases (`artifacts/v2/humanbench/`) and in the releases with corrected texts and answers of the OptiMind authors (`artifacts/v2/optimind/`), with the audit of every three-family label miss (`artifacts/v2/audit/AUDIT_human_texts.md`).
- Corrected releases added under `datasets/optimind_corrected/` with their MIT license.
- Framework figure of the certifier in the README (`figures/fig0_framework.png`, script `scripts/make_framework_figure.py`).
- Figures regenerated with the new counts.

## v2.0.0

- All experiments rerun with DeepSeek-V4-Flash, GPT-6.1 Sol, and Claude Sonnet 5.5.
- Certification by agreement of three model families at the stated instance, with data verification: the two families that did not perform the extraction compare the extracted data with the problem text.
- OptMATH-200 added, a second sample of OptMATH-Train drawn after the verification rule was set.
- Audit of every certificate whose value misses the label, with classes and evidence per problem (`artifacts/v2/audit/AUDIT.md`).
- Scripts that recompute every table and figure from the stored records (`scripts/paper_tables.py`, `scripts/make_figures.py`).
- Description of the first OptMATH-Train sample corrected: it is a uniform random sample with seed 42, not the first 300 records by index.
- Framework figure of the certifier added to the README (`figures/fig0_framework.png`, script `scripts/make_framework_figure.py`).

## v1.1.0 and v1.0.0

Code and records of the earlier version, in which resampled agreement served as the admission gate of an experience library.
