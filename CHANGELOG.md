# Changelog

## v2.0.0

- All experiments rerun with `deepseek-v4-flash`, `gpt-6.1-sol`, and `claude-sonnet-5-5`.
- Certification by agreement of three model families at the stated instance, with data verification: the two families that did not perform the extraction compare the extracted data with the problem text.
- OptMATH-200 added, a second sample of OptMATH-Train drawn after the verification rule was set.
- Audit of every certificate whose value misses the label, with classes and evidence per problem (`artifacts/v2/audit/AUDIT.md`).
- Scripts that recompute every table and figure from the stored records (`scripts/paper_tables.py`, `scripts/make_figures.py`).
- Description of the first OptMATH-Train sample corrected: it is a uniform random sample with seed 42, not the first 300 records by index.

## v1.1.0 and v1.0.0

Code and records of the earlier version, in which resampled agreement served as the admission gate of an experience library.
