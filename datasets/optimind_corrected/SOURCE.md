# Corrected releases of IndustryOR and Mamo-Complex (OptiMind)

The two CSV files are the corrected releases of IndustryOR and Mamo-Complex by the authors of OptiMind
(Zhang et al., "OptiMind: Improving Small Language Models for Optimization Modeling through Formulation Guidance
and Multi-Turn Learning", arXiv:2509.22979). They are redistributed unchanged under the MIT license of the source
repository, included here as `LICENSE` ("Copyright (c) Microsoft Corporation.").

- Repository: https://github.com/microsoft/OptiGuide
- Commit: `3da334a48c68af9f82035d6dece9e952a46626a9`
- Downloaded from `https://raw.githubusercontent.com/microsoft/OptiGuide/<commit>/<path>`: the two CSV files on
  2026-11-26 00:42 UTC, `LICENSE` on 2026-11-26 04:03 UTC.
- Columns: `problem_class`, `question`, `answer`. The Mamo file starts with a byte order mark; read both with
  `encoding="utf-8-sig"` and a raised `csv.field_size_limit`.

| Repository path | File | Rows | Bytes | SHA-256 |
|---|---|---:|---:|---|
| `optimind/data/optimind_cleaned_classified_industryor.csv` | `optimind_cleaned_classified_industryor.csv` | 99 | 108712 | `fd80b3061e13edc040a7ff395f4f664fd761ad26b651e5dc8dcbbd7d3a48b427` |
| `optimind/data/optimind_cleaned_classified_mamo_complex.csv` | `optimind_cleaned_classified_mamo_complex.csv` | 210 | 381290 | `214df853487992f6c76c77f49d48a3f51c060958e635dc35515c0afc6b0947f8` |
| `LICENSE` | `LICENSE` | | 1141 | `c2cfccb812fe482101a8f04597dfc5a9991a6b2748266c47ac91b6a5aae15383` |

The run records built from these files are in `artifacts/v2/optimind/`; `scripts/human_problems.py` rebuilds
their problem files (`workorder.jsonl`, `problems.csv`) from this folder.
