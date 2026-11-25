# Library diagnostics

Analysis (no model call) of the five libraries built from the arms of Table 5 and of the host's released library `skill_library\skill_library_learned`. Paths are relative to the host checkout (`$HOST`) or to this repository (`$REPO`). Characters are counted on the decoded UTF-8 text of the skill files listed in `index.json`; `ingredients.json` sizes are in bytes.

The per-skill problem counts and character counts behind Sections 1 and 4 are published in `artifacts/v2/downstream/library_skills.csv` and `libraries.csv`; the skill text itself is not published.

## 1. Size and structure

| Library | Skills | Clusters | Eligible problems clustered | Problems per skill: min / median / max | Skills built from one problem | Characters of skill text | ingredients.json bytes (terms: variable / constraint / objective) | Clusters whose draft inputs were subsampled (size guard) |
|---|---:|---:|---:|---|---|---:|---|---:|
| panel_base_3of3 | 157 | 157 (noise clusters 0) | 229 of 300 | 1 / 1 / 26 | 140 (89.2%) | 1,736,590 | 45,362 (298 / 686 / 231) | 2 |
| panel_base_2of3 | 172 | 172 (noise clusters 0) | 253 of 300 | 1 / 1 / 27 | 154 (89.5%) | 1,769,709 | 45,362 (298 / 686 / 231) | 4 |
| vote | 184 | 184 (noise clusters 0) | 269 of 300 | 1 / 1 / 28 | 166 (90.2%) | 2,038,275 | 45,362 (298 / 686 / 231) | 4 |
| runsok | 209 | 209 (noise clusters 0) | 300 of 300 | 1 / 1 / 28 | 188 (90.0%) | 2,337,305 | 45,362 (298 / 686 / 231) | 5 |
| gt | 165 | 165 (noise clusters 0) | 238 of 300 | 1 / 1 / 27 | 150 (90.9%) | 1,842,439 | 45,362 (298 / 686 / 231) | 4 |
| released `skill_library_learned` | 56 | not recorded | not recorded | not recorded | not recorded | 645,303 | 15,761 (80 / 128 / 29) | not recorded |

For our libraries a cluster is one DBSCAN cluster of `<library>.build_summary.json` (`build_summary.clusters`); every cluster produced exactly one skill (skill ids in the build summary equal the ids of `index.json`), and the `sample_count` of the clusters sums to the eligible problems of the arm. Problems per skill = `sample_count` of its cluster. When the draft inputs of a cluster exceeded the draft size limit (60,000 characters, `--draft-budget`), the size guard of `scripts\e1_rebuild.py` kept a deterministic subset of the candidate trajectories for drafting (last column; counts of `OVER BUDGET` lines in the build logs); the problem counts above are those of the cluster, not of the subset. `ingredients.json` is byte-identical in all five of our libraries (MD5 2ba47172...5099): it is the ingredient vocabulary of the shared collection run on the 300 OptMATH problems, not a property of the arm. The three released libraries (`skill_library_cluster`, `skill_library_learned`, `skill_library_nanoco_learned`) also share one identical `ingredients.json` (MD5 a7b6ca74...c512).

Released library: `index.json` lists 56 skills with name, description and path only; the folder holds no build summary, no cluster assignment and no list of source problems, so clusters and problems per skill are not recorded. For reference, the released initial library `skill_library\skill_library_cluster` (README: "Initial skills distilled from clustered solved trajectories") lists 46 skills (514,672 characters); 46 skill ids are present in both (every skill id of the cluster library is in the learned library). This is consistent with the README's two-stage procedure but is not a record of it.

## 2. Build settings

### Our libraries

| Setting | Value | Source |
|---|---|---|
| cluster-eps | 0.05 | `e1_rebuild.py --cluster-eps 0.05` (library build command); equal to `cluster_eps` of the stored collection run (`run_start` arguments of the host run directory `outputs/e1/collect`) and recorded as `dbscan_eps` in every build summary |
| cluster-min-samples | 1 | `--cluster-min-samples 1` (library build command); `cluster_min_samples` of the stored collect run; `dbscan_min_samples` in every build summary |
| archetype-fusion-alpha | 0.55 | `--archetype-fusion-alpha 0.55` (library build command); `archetype_fusion_alpha` of the stored collect run; also the default of `e1_rebuild.py` and the value in the host README |
| cluster-size | 300 | not an argument of `e1_rebuild.py`; the collection run used `main.py --phase cluster --cluster-size 300` (all 300 stream problems in the clustering subset), copied from the stored collect run's `run_start` argv; the rebuild clusters every eligible relabeled row of the arm |
| skill-learning stage after clustering | none | `e1_rebuild.py` ports the tail of the host's `run_cluster` (`cluster_build`); no `--phase learning` was run on any of our libraries |
| other | draft size limit 60,000 characters (`--draft-budget`); `--analysis-cap 98000` from the second panel_base_2of3 build on (not for panel_base_3of3); agent-max-turns 12; analysis-workers 4; builder-workers 4 | library build commands (`scripts/e1_rebuild.py`) |

Rule of `e1_rebuild.py` (its docstring): "Pass EXACTLY the eps / min-samples / alpha the collect run used"; the values above were taken from the stored collect run, which used the same arguments as the README's cluster command except `--cluster-size` (300 instead of 150), `--cluster-workers` (12 instead of 8) and `--builder-workers` (1 in the collection run; the rebuild used 4, as in the README).

### Released library

What the host repository records:

- `README.md`, section "Released Skill Libraries": `skill_library/skill_library_learned` is the "Default learned library for standard evaluation"; `skill_library_cluster` holds "Initial skills distilled from clustered solved trajectories"; `skill_library_nanoco_learned` is the "Learned library extended with Nano-CO trajectories".
- `README.md`, section "Usage": a documented procedure, (1) `main.py --phase cluster --data datasets/train_set/optmath-train-300.jsonl --cluster-size 150 --cluster-eps 0.05 --cluster-min-samples 1 --cluster-workers 8 --analysis-workers 8 --builder-workers 4 --archetype-fusion-alpha 0.55 --top-k 3 --timeout 120 --agent-max-turns 12` ("takes the first 150 instances of `optmath-train-300.jsonl` as the clustering subset"), then (2) `main.py --phase learning` on the same file with `--parent-run-dir` ("processes only the items not assigned to the cluster subset ... the remaining 150 OptMath instances").
- `main.py`: `DEFAULT_RELEASED_LIBRARY = skill_library/skill_library_learned`, used by `--phase eval` when `--source-skill-library` is omitted.
- The library folder: `index.json` (version 1.0, 56 skills: id, name, description, path), `ingredients.json` and the 56 skill files.
- README, section "Performance": benchmark results for OptSkills-DeepSeek (DeepSeek-V3.2) and OptSkills-Qwen; it does not say which library or run produced them.

What it does not record: that `skill_library_learned` was produced by the documented commands; the training file, the number or ids of the problems used, the clustering subset actually used, the model and embedding model, any run directory, log, ledger, `resume.json` or build summary of the build; cluster assignments; whether the learning phase ran to the end (the README describes it, but no checkpoint or learning record of the released library is present). The host checkout is not a git repository, so no history is available either. The README procedure names `datasets/train_set/optmath-train-300.jsonl` as training data, which is the file of our stream; the build data of the released library itself cannot be identified from the records.

## 3. Contamination check of the released library

The build data of the released library is not recorded (Section 2), so the check cannot be made against its build problems. It is made against the candidate build data named by the README procedure (`datasets/train_set/optmath-train-300.jsonl`: all 300, the first 150 as the documented clustering subset, the remaining 150 as the documented learning set) and, for completeness, against `datasets/train_set/nano-co.jsonl` (the data of `skill_library_nanoco_learned`). Exact: question text equal after replacing every run of whitespace by one space and stripping. Jaccard: word 5-grams of the lowercased, whitespace-normalized question; for each benchmark item the maximum over the build problems.

| Candidate build data | Benchmark | Items | Exact matches | Items with Jaccard >= 0.8 | Items with Jaccard >= 0.5 | Maximum Jaccard |
|---|---|---:|---:|---:|---:|---:|
| optmath-train-300.jsonl, all 300 | complexor | 18 | 0 | 0 | 0 | 0.0218 |
| optmath-train-300.jsonl, all 300 | industryor | 100 | 0 | 0 | 0 | 0.0093 |
| optmath-train-300.jsonl, all 300 | mamo_complex_test | 211 | 0 | 0 | 0 | 0.0225 |
| optmath-train-300.jsonl, all 300 | optmath_bench | 166 | 0 | 0 | 0 | 0.2705 |
| optmath-train-300.jsonl, all 300 | optibench | 605 | 0 | 0 | 0 | 0.0130 |
| optmath-train-300.jsonl, first 150 (README cluster subset) | complexor | 18 | 0 | 0 | 0 | 0.0218 |
| optmath-train-300.jsonl, first 150 (README cluster subset) | industryor | 100 | 0 | 0 | 0 | 0.0085 |
| optmath-train-300.jsonl, first 150 (README cluster subset) | mamo_complex_test | 211 | 0 | 0 | 0 | 0.0138 |
| optmath-train-300.jsonl, first 150 (README cluster subset) | optmath_bench | 166 | 0 | 0 | 0 | 0.2176 |
| optmath-train-300.jsonl, first 150 (README cluster subset) | optibench | 605 | 0 | 0 | 0 | 0.0130 |
| optmath-train-300.jsonl, remaining 150 (README learning phase) | complexor | 18 | 0 | 0 | 0 | 0.0197 |
| optmath-train-300.jsonl, remaining 150 (README learning phase) | industryor | 100 | 0 | 0 | 0 | 0.0093 |
| optmath-train-300.jsonl, remaining 150 (README learning phase) | mamo_complex_test | 211 | 0 | 0 | 0 | 0.0225 |
| optmath-train-300.jsonl, remaining 150 (README learning phase) | optmath_bench | 166 | 0 | 0 | 0 | 0.2705 |
| optmath-train-300.jsonl, remaining 150 (README learning phase) | optibench | 605 | 0 | 0 | 0 | 0.0116 |
| nano-co.jsonl, all 245 | complexor | 18 | 0 | 0 | 0 | 0.0060 |
| nano-co.jsonl, all 245 | industryor | 100 | 0 | 0 | 0 | 0.0059 |
| nano-co.jsonl, all 245 | mamo_complex_test | 211 | 0 | 0 | 0 | 0.0202 |
| nano-co.jsonl, all 245 | optmath_bench | 166 | 0 | 0 | 0 | 0.0126 |
| nano-co.jsonl, all 245 | optibench | 605 | 0 | 0 | 0 | 0.0097 |

No exact match and no item at Jaccard 0.8 or above for any candidate. The largest value is 0.2705: OptMATH-Bench item `index` 26 against `optmath-train-300.jsonl` record `index` 199 (position 199 of 300). Because the build data of the released library cannot be identified, this does not establish that the released library is free of benchmark problems.

Supplementary test (does the skill text itself identify its sources?): share of a dataset item's word 5-grams that occur anywhere in the library's skill text. Mean containment, released library: optmath-train-300 first 150 0.0033, remaining 150 0.0043, nano-co 0.0016, benchmarks 0.0007 to 0.0065; our gt library (built from the 238 eligible stream problems): 0.0030, 0.0037, 0.0017 and 0.0003 to 0.0025. No item of any dataset reaches 0.10 for either library. The skill text is too generic to show which problems a library was built from, so it does not identify the released library's build data.

## 4. Selected skills in the downstream evaluation (pass r1)

From `trajectories.jsonl` of the evaluation runs (published as column `selected_skill` of `artifacts/v2/downstream/per_item.csv`) (`skill_selection.skill_id`, one skill per item); problems per skill from the library's build summary; solved = `round_aware` of scripts\score_eval.py on `prediction` (unparseable counts as wrong). Single = the selected skill's cluster has one problem; several = more than one.

| Library | Benchmark | Items | Items with a selected skill | Distinct skills selected | Share of items with a single-problem skill | Single: items / solved / accuracy | Several: items / solved / accuracy | No skill: items / solved |
|---|---|---:|---:|---:|---:|---|---|---|
| panel_base_3of3 | ComplexOR | 18 | 17 | 15 | 88.2% | 15 / 12 / 80.00% | 2 / 0 / 0.00% | 1 / 0 |
| panel_base_3of3 | IndustryOR | 100 | 97 | 41 | 66.0% | 64 / 28 / 43.75% | 33 / 7 / 21.21% | 3 / 0 |
| panel_base_3of3 | Mamo.Complex | 211 | 207 | 34 | 86.5% | 179 / 102 / 56.98% | 28 / 5 / 17.86% | 4 / 0 |
| panel_base_3of3 | OptMATH-Bench | 166 | 164 | 48 | 86.0% | 141 / 76 / 53.90% | 23 / 19 / 82.61% | 2 / 0 |
| panel_base_3of3 | OptiBench | 605 | 601 | 52 | 72.5% | 436 / 296 / 67.89% | 165 / 102 / 61.82% | 4 / 0 |
| panel_base_3of3 | all 1,100 | 1100 | 1086 | 104 | 76.9% | 835 / 514 / 61.56% | 251 / 133 / 52.99% | 14 / 0 |
| gt | ComplexOR | 18 | 18 | 15 | 77.8% | 14 / 9 / 64.29% | 4 / 3 / 75.00% | 0 / 0 |
| gt | IndustryOR | 100 | 98 | 45 | 86.7% | 85 / 31 / 36.47% | 13 / 3 / 23.08% | 2 / 0 |
| gt | Mamo.Complex | 211 | 208 | 31 | 68.8% | 143 / 70 / 48.95% | 65 / 36 / 55.38% | 3 / 0 |
| gt | OptMATH-Bench | 166 | 162 | 33 | 85.8% | 139 / 76 / 54.68% | 23 / 16 / 69.57% | 4 / 0 |
| gt | OptiBench | 605 | 602 | 39 | 98.0% | 590 / 404 / 68.47% | 12 / 6 / 50.00% | 3 / 0 |
| gt | all 1,100 | 1100 | 1088 | 92 | 89.2% | 971 / 590 / 60.76% | 117 / 64 / 54.70% | 12 / 0 |

