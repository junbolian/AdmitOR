# Run records, version 2

These records back every table and figure of version 2. They were produced with three model families:
family A is DeepSeek-V4-Flash (it also extracts the problem data), family B is GPT-6.1 Sol, and family C is
Claude Sonnet 5.5. Each family writes one program per problem (two in the `_k2` sets). Both table scripts
read these files only and need no key:

```bash
python scripts/paper_tables.py      # writes artifacts/v2/tables
python scripts/rules_compare.py     # writes artifacts/v2/tables/rules_compare.*
python scripts/make_figures.py      # reads artifacts/v2/tables, writes figures/
```

## Problem sets

| Folder | Problems | Source |
|---|---:|---|
| `optmath_295` | 295 | OptMATH-Train. `sample_k` is element `k-1` of `random.Random(42).sample(range(201071), 300)`, the 0-based line number in `OptMATH-Train.jsonl` (`source_record`). `sample_1` to `sample_5` were used during development and are excluded from all results and from these records. |
| `optmath_200` | 200 | OptMATH-Train, drawn with `scripts/confirm_draw.py`: `random.Random(42).sample(pool, 200)` over the 200,771 records outside the first sample, sorted by line number. `conf_<n>` is line `n`. `ids.json` holds the drawn line numbers in drawn order and `ids.sha256` its hash. |
| `nanoco_150` | 150 | NANO-CO (`datasets/train_set/nano-co.jsonl`), the part used to fit the threshold of the resampling rule. `e3_<type>_<n>` has `index` = `n` (`source_record`). |
| `nanoco_95` | 95 | The remaining NANO-CO problems. |
| `optmath_295_k2`, `nanoco_95_k2` | 295, 95 | The same problems as `optmath_295` and `nanoco_95`, certified with two programs per family. |

Labels are used for scoring only; no model saw them. OptMATH sets are scored with `round_aware` of
`scripts/score_eval.py`, NANO-CO sets with `label_match` of `scripts/e3_calibrate.py`.

## Files of a problem set

| File | Content | Feeds |
|---|---|---|
| `problems.csv` | identifier, `source_record`, label (and `problem_type` for NANO-CO) | every table |
| `workorder.jsonl` | identifier and problem text, as given to the models | data verification, `misses_2of3_only.md`, audit |
| `verdicts.jsonl` | one line per problem: decision of the primary sampler (`ACCEPT`, `ABSTAIN`, `UNINFORMATIVE`, `ERROR`), clique, families, informative instances, `elapsed_s`; an `ERROR` problem has no run folder and counts as not certified | Tables 1, 4, 7b |
| `judges.csv` | per problem and rule (`gate`, `gate_3fam`, `gate_tau`, `panel_base_2of3`, `panel_base_3of3` and the same with the `ind_` prefix for the independent sampler): decision and certified value, as written by `scripts/rerun_verdicts.py --tau 33.4` | Tables 1 to 3, 8, audit |
| `runs/<id>/spec.json` | the extracted parameter set (`spec`, with base value and resampling range of each parameter), the extractor's raw parameter list and warnings | data verification, audit |
| `runs/<id>/A-direct.py`, `B-structured.py`, `C-direct.py` | the program of each family (`-2` suffix: second program, `_k2` sets) | audit |
| `runs/<id>/verdict_full.json`, `verdict_independent.json` | verdict of the primary (parameter-screen) and of the independent sampler: decision, clique, the value and status of each program on each instance (`objectives`, `statuses`; instance 0 is the stated instance) | Tables 1, 4, 8 |
| `runs/<id>/param_screen.json` | which parameters the screen kept for resampling | none (record) |
| `runs/<id>/extraction_attempts.json` | only for the problems certified under the extraction retry rule (a reply that is not JSON, has no `params` object, has a parameter without a base value, or is cut off by the length limit is requested again with identical settings, at most three attempts): one record per attempt with status, finish reason and error; in `optmath_295`, `optmath_200` and `optmath_295_k2` these are the six problems that had ended in an extraction error before the rule (`sample_54`; `conf_133273`, `conf_159872`, `conf_52221`, `conf_98168`; `sample_199` of `optmath_295_k2`) | none (record) |
| `runs/<id>/verification_<A,B,C>.json` | the data-verification reply of each family: `status`, the reply text, `mismatch` and `not_stated` lists, `flag_mismatch`, `flag_not_stated`, `flag_any`; a reply that could not be parsed was requested again with identical settings (at most three attempts), and such a reply carries `attempts`, one record per request (not present in the `_k2` sets; on `optmath_295`, family B was asked only for the problems that `panel_base_2of3` certifies) | Tables 1 to 3, 8, Figure 2, audit |

Absolute local paths inside solver error messages are replaced by `<PATH>/`.

## Other folders

| Folder / file | Content | Feeds |
|---|---|---|
| `tables/` | every table as CSV and Markdown, written by `scripts/paper_tables.py` (`t1` to `t8`, `t2_audit_list.csv`, `misses_2of3_only.md`) and `scripts/rules_compare.py` (`rules_compare.*`); `library_diagnostics.md` is a copy of `downstream/library_diagnostics.md` | Figures 1 and 2 (`t1_rules.csv`, `t2_audit.csv`) |
| `audit/audit_classes.csv` | every audited label miss: set, identifier, class (D, P, B, T, U, E, M), agreement (`three` or `two_only`) | Tables 2, 8, Figures 1 and 2 |
| `audit/AUDIT.md` | class definitions, every audited problem with certified value, label, class, agreement and evidence, and the review of the 40 label-matching certificates that data verification withdraws | Figures 1 and 2 |
| `downstream/per_item.csv` | one row per evaluation item and pass: configuration, pass, benchmark, item identifier, prediction, label, match (`round_aware`), selected skill | Table 6 |
| `downstream/admitted_attempts.csv` | one row per attempt of the 295 OptMATH problems: result, label match under the host rule and under `round_aware`, and for each of ten arms whether the arm admits it | Tables 5, 6c |
| `downstream/libraries.csv`, `library_skills.csv` | size of each learned library and, per skill, the problems it was built from | Table 6c, `library_diagnostics.md` |
| `downstream/library_diagnostics.md` | size and build settings of the libraries, provenance and overlap check of the host's released library, and the skills selected during evaluation | text |
| `cost/calls_tokens.csv` | model calls and tokens per set, stage, family and role (aggregated from the usage records) | Table 7 |
| `cost/verification_seconds.csv` | request seconds of the data verification per problem, summed over the families | Table 7b |

The configurations of `downstream/` are the libraries built from the arms `panel_base_3of3`, `panel_base_2of3`,
`vote`, `runsok` and `gt`, the host without a learned library (`nolib`), and the host's released library
(`released`; build data as described in the host README, no build record). The host itself and the text of
its skill libraries are not redistributed; the changes made to the host are in `patches/`.

## Runs on human-written texts

The same certifier and data verification, unchanged (`scripts/e1_certify.py --m 5 --sampler param_screen --both`, the
three families DeepSeek-V4-Flash, GPT-6.1 Sol and Claude Sonnet 5.5, temperature 0, the extraction and verification
retry rules), on two releases of IndustryOR and Mamo ComplexLP. Each benchmark folder has the layout of the problem
sets above (`workorder.jsonl`, `problems.csv`, `verdicts.jsonl`, `judges.csv`, `runs/<id>/` with `spec.json`, the three
programs, `verdict_full.json`, `verdict_independent.json`, `param_screen.json`, `extraction_attempts.json` and
`verification_<A,B,C>.json`). Scoring: `round_aware` of `scripts/score_eval.py`; a data-verification reply that cannot
be parsed after three attempts counts as not flagged. Absolute local paths are replaced by `<PATH>/` as above; a relay error page that a call returned in place of
a model reply (in a program file, or as the reply of an earlier verification attempt) is replaced by
`<relay error message instead of a model reply (HTTP <code>, ...); text not published>` (14 places).

| Folder / file | Content | Rebuild |
|---|---|---|
| `humanbench/industryor`, `humanbench/mamo_complex` | published releases of IndustryOR (100 problems, `industryor_<index>`) and Mamo ComplexLP (211, `mamo_complex_<index>`), from `datasets/benchmark/industryor.jsonl` and `mamo_complex_test.jsonl`; the label is the field `answer` | `python scripts/human_problems.py` (problem files) |
| `humanbench/tables/` | `h1_rules` (certification rules), `h2_check` and `h2_check_unparsed` (data-verification flags among the `panel_base_3of3` certificates), `h3_single_vs` (single programs on the problems without a three-family certificate), `h4_joint` (agreement of the three families with the label), `h5_expert` and `h5_expert_status.csv` (certificates against the expert audit of Xiao et al. 2025), `h6_per_problem.csv` (every decision per problem, for rescoring against any release) | `python scripts/human_tables.py --run humanbench` |
| `humanbench/misses_3of3.md`, `misses_2of3_only.md`, `withdrawn_matching.md` | every `panel_base_3of3` certificate that misses the label, every `panel_base_2of3` miss without a three-family certificate, and every label-matching `panel_base_3of3` certificate that the rule "B or C" withdraws, with problem text, parameter set, programs, values and verification replies | `python scripts/human_tables.py --run humanbench` |
| `humanbench/expert/SOURCE.md` | address, commit, file names and SHA-256 of the cleaned and original files of the expert audit of Xiao et al. (2025); the files themselves are not redistributed | none |
| `humanbench/expert/expert_status.csv` | the per-problem status derived from those files (`removed`, `kept, same label`, `kept, label changed`), read by table h5 | `python scripts/human_expert_status.py --expert <folder with the downloaded files>` |
| `optimind/industryor`, `optimind/mamo_complex` | corrected releases by the OptiMind authors (99 problems, `om_industryor_<row>`, and 210, `om_mamo_<row>`; `<row>` is the 0-based row of the CSV), from `datasets/optimind_corrected/`; `problems.csv` keeps the column `problem_class`. The `answer` column holds a number (IndustryOR) or a one-element list (Mamo); an answer written with a zero decimal, such as `219816.0`, is read as the integer `219816`, so `round_aware` compares it with zero decimals | `python scripts/human_problems.py` (problem files) |
| `optimind/tables/` | `o1_rules`, `o2_check`, `o2_check_unparsed` and `o3_per_problem.csv`, as h1, h2 and h6, scored against the OptiMind answers | `python scripts/human_tables.py --run optimind` |
| `optimind/misses_3of3.md`, `misses_2of3_only.md`, `withdrawn_matching.md` | the same exports against the OptiMind answers | `python scripts/human_tables.py --run optimind` |
| `audit/AUDIT_human_texts.md` | class of every `panel_base_3of3` certificate that misses the label in both releases, with evidence, and the diet problems whose text states integrality | none |
