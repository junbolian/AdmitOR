# v1.1.0: reviewer-round analyses (September 2026)

Every number in the revised manuscript was regenerated from these assets and the git checkout before this release; see REPORT_RELEASE.md for the per-script table. The two exceptions are those stated in the README: the 88 extractor calls of the two-extractor preliminary (outputs shipped under `release/reviewer_round/09_extractions/`) and the feasibility-resampling diagnostic (outputs shipped as recorded).

## Release assets

The run records unpack into one directory, `admitor-v1.1.0-run-records/`, with the host's `outputs/` layout. Every record passed through `release_tools/scrub_logs.py` and was checked with `scripts/secret_sweep.py` and `scripts/release_content_check.py`.

| File | Contents | Files | Uncompressed bytes | Zipped bytes | sha256 |
|---|---|---:|---:|---:|---|
| `admitor-v1.1.0-run-records-core.zip` | relabeled arms, collection, gate work order, E1 certification runs (specifications, candidate programs, verdicts), E3 calibration runs and labels, runtime event streams | 2,330 | 849,470,251 | 93,940,328 | `ff5f80a5bc6a26ce037cbe0e34c7c03a108a81b571f79ceb902561d4bff176bb` |
| `admitor-v1.1.0-run-records-eval.zip` | E1 evaluation trajectories, four arms x five plates | 20 | 735,883,632 | 100,333,853 | `d72c2ad67195f6c0151c102da9748495cdd6adc40a689b3ac2affaeb2deaa5ba` |
| `admitor-v1.1.0-run-records-e0.zip` | E0 host-reproduction trajectories and the 17-item OptMATH recheck | 6 | 173,263,054 | 22,242,226 | `4510871a975a9943e541890ba9c900f48e9cdd14c47e05ca6dbfb302cc5269be` |
| `admitor-v1.1.0-run-records-cache.zip` | E1 evaluation response cache | 40,208 | 162,549,387 | 71,862,628 | `f65e9541e6f4d209a59aae6e8b617103675d80e8a7b11934281961c17885127e` |

The host run ledger (93,909 records) remains the `v1.0.0` release asset and is unchanged: [`admitor-v1.0.0-runlogs.zip`](https://github.com/junbolian/AdmitOR/releases/tag/v1.0.0), sha256 `272d52030e1ab229547e0762b7c25f954bcfc22e6e2586eeb82bcbec682a4c0f`.

## New scripts (`scripts/`)

Reviewer-round analyses: `reviewer_inventory.py`, `e3_certificate_numbers.py`, `code_facts.py`, `runlog_phase_audit.py`, `gate_arm_composition.py`, `poison_provenance.py`, `serving_variant_join.py`, `panel_base_judges.py`, `candidate_crosstab.py`, `task3_additions.py`, `assemble_decomposition_report.py`, `corrected_bootstrap.py`, `format_bootstrap_report.py`, `retrieval_stats.py`, `retrieval_final.py`, `disjointness_audit.py`, `numeric_coverage.py`, `k4_restricted.py`, `two_extractor_run.py`, `two_extractor_agreement.py`, `feasibility_resampling.py`, `admitor_reanalysis.py`.

Release hygiene: `secret_sweep.py`, `release_content_check.py`.

Changed: `e0_scorecard.py` (`--eval-root` fills the reproduced column from the E0 run records and prints the macro row); `release_tools/scrub_logs.py` (a Windows path must have a real path shape, so escaped code text is no longer rewritten; output on the v1.0.0 inputs is byte-identical).

Each script's module docstring states its inputs (in git, run records, ledger), the exact reproduce command, its outputs, and the manuscript location of its numbers. `requirements-analysis.txt` records that nothing beyond `environment.yml` is needed.

## New files in git

- `release/reviewer_round/`: every reviewer-round output (calibration table, judge decomposition and the five derived judges' verdicts, bootstrap, retrieval, serving-variant join, provenance, numeric coverage, restricted K4, two-extractor preliminary with the 88 extractions and their call ledgers, feasibility resampling, admitted id lists) and `REPORT_reviewer_round_2026-09.md`.
- `release/k3_packets/`: the 22 K3 review packets; `release/k3_attribution.csv` points at them.
- `release/e0/scorecard.json`: the reported column of Table 9 and the plate of each row.
- `paper/make_fig1.py`: regenerates Figure 1; `figures/fig1_overview.pdf` is the regenerated figure (the PNG copy is removed).

## README

- New sections: "Reviewer-round analyses (September 2026)", "Model pins and the response-side audit", "Host backbone availability", and "Reproducing the paper's numbers" (one row per script with its inputs, command, outputs and manuscript location).
- Corrections checked: the README was searched for a three-candidate informative rule, a cross-family description of the majority-vote arm, ReLoop as a pipeline component, a library built at the calibrated threshold, a claim that every call was served by the pinned backbone, and a `gpt-5.1` pin. None occurred outside the replaced section, so no sentence needed correcting. The new sections state the admission-time rule of the E1 library and the calibrated threshold tau = 33.3 as separate rules (judge table), the majority-vote judge as a vote over host samples, the `gpt-5.4` pin set through `ADMITOR_MODEL_B`, and the response-side audit counts.
- Bootstrap intervals updated to the manuscript's values: gate minus vote +3.53 [+0.87, +6.68], gate minus ground truth +4.46 [+2.34, +6.65].
- Installation documents the pinned environment (`environment.yml`: Python 3.12.12, numpy 2.4.4, scipy 1.18.0, Pyomo 6.10.0, HiGHS 1.15.1) in which the outputs were re-verified.
