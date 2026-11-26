# Expert-audited benchmarks: source

Portal of Xiao et al. (2025): https://llm4or.github.io/LLM4OR. The portal links the
cleaned benchmarks at https://github.com/LLM4OR/LLM4OR/tree/master/static/clean_benchmarks; the original versions it serves
are under `static/datasets/` of the same repository.

- Downloaded: 2026-11-25 15:02 (local time UTC-6), from `https://raw.githubusercontent.com/LLM4OR/LLM4OR/<commit>/<path>`.
- Repository commit (master at download): `75962df5ddf531906fda76f8708c658114e63c0e` (committed 2025-08-29T18:27:22Z).
- Files used: the cleaned `IndustryOR.jsonl` and `Mamo/Mamo_complex_lp_clean.jsonl`, and the original versions the portal serves, `static/datasets/IndustryOR/dataset.jsonl` and `static/datasets/Mamo/data/optimization/Complex_LP/mamo_complex_lp.jsonl`.
- The files were not opened before the data verification of both benchmarks had finished.
- The files are not redistributed. `expert_status.csv` holds the per-problem status derived from them (`scripts/human_expert_status.py`; columns as in table h5).

| Kind | Repository path | Local file | Bytes | SHA-256 |
|---|---|---|---:|---|
| clean | `static/clean_benchmarks/IndustryOR.jsonl` | `clean/IndustryOR.jsonl` | 62094 | `d7c2c05377ade5bc6a401ebf3075f0e00fa91068439761e5b46fa3045ffc19b5` |
| clean | `static/clean_benchmarks/Mamo/Mamo_complex_lp_clean.jsonl` | `clean/Mamo/Mamo_complex_lp_clean.jsonl` | 215021 | `28e10dff1146ff635673293b5730abb3d7efa2f7bbe91de60fe67b729dfe7a0d` |
| original | `static/datasets/IndustryOR/dataset.jsonl` | `original/IndustryOR/dataset.jsonl` | 129718 | `4c7f8db266f2f4ccc3d4784fc754ae1ab195226880c9b19b97b67b655fa47752` |
| original | `static/datasets/Mamo/data/optimization/Complex_LP/mamo_complex_lp.jsonl` | `original/Mamo/data/optimization/Complex_LP/mamo_complex_lp.jsonl` | 387757 | `07eb3db3d2af099871dfa4425b14887775179c158c38944fe4fe152b615bbfc3` |
