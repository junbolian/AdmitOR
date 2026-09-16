# AdmitOR reviewer round, report

Issued against the consolidated work order of 2026-09-16 and its amendments.
Every number carries the script and the output file that produced it. All
work is zero-token except Task 9.

Scripts live in `admitor-infra\`; outputs in
`AdmitOR\reanalysis\reviewer_round\` (gitignored); shipped files in
`AdmitOR\release\`.

---

## 1. Premises found false

| # | Premise in the work order | What is actually the case | Evidence |
|---|---|---|---|
| 1 | `e3_certificate_numbers.py`, `disjointness_audit.py` and `CLAUDE_CODE_E5MINI.md` exist in the repo | None of the three was present. They were delivered in chat in August and never placed on disk. All three were written from the task descriptions. | `00_inventory.md` section 4 |
| 2 | Per-arm rebuild attribution is recoverable from the runlog | It is not. `e1_rebuild.py` writes no runtime event stream, and 5,025 of the 60,000 ledger records fall in no window. Only 1,225 sit inside the library-build span; 3,800 cluster in Aug 10 06:00 to 12:00 with no surviving log or cache entry. Reported as one unattributed bucket. | `01_3_runlog_phases.md` |
| 3 | 5(c) can replay stored requests from the runlog | No request body survives anywhere. `runlog.py` stores a 16-hex digest of a sorted-keys dump; the caches store responses only, keyed by a one-way hash. Replay is possible only by reconstructing requests from `function_agent.messages`. 5(c) was later dropped. | `05b_serving_variant_join.md` method table |
| 4 | Arm B is pinned in code | `admitor-core/pipeline_one.py` defaults `ADMITOR_MODEL_B` to `gpt-5.1`, and no `.env` sets it. The operator later confirmed `gpt-5.4` was exported at run time. No response-side record exists for the candidate arms, so this cannot be verified from artifacts. | `01_code_facts_data.md`, operator confirmation |
| 5 | "A response-side model-string audit confirms every call was served by the pinned backbone" | True only if the dated variant counts as the pin. 1,425 of 60,000 host responses returned `deepseek-v3-2-251201`. Zero returned anything outside those two names. | `01_3_runlog_phases.md` |
| 6 | Algorithm 1 line 7: informative means "at least three candidates" | The code requires **two**. `consensus.py:164`: `sum(... is not None) >= 2`. | `01_code_facts_data.md` |
| 7 | "Our majority-vote arm is that rule instantiated across model families" | The Vote oracle aggregates the host's own rollout (`label_oracle.py:135`, `row["rollout"]["candidates"]`), which is exactly three trajectories per problem from the single DeepSeek backbone. It is not cross-family. | `01_code_facts_data.md` section 1.6 |
| 8 | "We adopt the instrument of ReLoop as a diagnostic layer" | No ReLoop component is imported or executed anywhere. Zero matches for `reloop` across `admitor-core`, `admitor-infra` and `OptSkills-main`. | Task 1.9 grep |
| 9 | Task 14.1: a figure generator can be found by grepping for "Conformal Gate" | No figure generator exists in the project, `fig2_pipeline.pdf` has no text layer (0 characters, 0 fonts, 0 vector drawings), and the string appears nowhere. The box already reads "Calibrated Gate" in the re-exported figure; the two sub-lines cannot be added without the drawing source. | Task 14.1 probe |
| 10 | The per-sample K3 attribution is recorded | It was not. All 22 review packets carry unticked boxes (0 of 22). The mapping was supplied by the operator and is now recorded in `release/k3_attribution.csv`, which is authoritative. | Task 12 |
| 11 | The 26 and the 22 disagreement sets are nested | They are not. 21 wrong under both, 5 wrong only under the 2dp rule (64, 75, 113, 180, 212), 1 wrong only under round-aware (37). 26 minus 22 is a net figure. | `02_calibration_table.md` |
| 12 | Proposition 2 cannot hold at 33.3 given 10 false of 103 | The threshold-selected set is 64, not 103. At 33.3: n = 64, k = 2, p_hat = 0.0312, CP95 = 0.0951. The rule holds and 33.3 is the minimum satisfying threshold. | `02_calibration_table.md` |

---

## 2. Task 2. Calibration contingency and stream reconciliation

Script `e3_certificate_numbers.py`, output `02_calibration_table.md`, `.csv`.

Observed scores take eight values only: 22.3, 22.4, 22.5, 22.6, 33.3, 33.4,
33.5, 33.6. A two-family clique scores 22.x, a three-family clique 33.x, and
nothing lies between, so **tau = 33.3 is exactly "all three families agree"**.

| Row | tau | n | k false | p_hat | CP95 | CP98.75 |
|---|---:|---:|---:|---:|---:|---:|
| all accepts | 33.3 | 64 | 2 | 0.0312 | 0.0951 | 0.1210 |
| all accepts | 33.6 | 58 | 1 | 0.0172 | 0.0792 | 0.1050 |
| value-bearing | 33.3 | 63 | 1 | 0.0159 | 0.0731 | 0.0971 |
| value-bearing | 33.4 | 62 | 1 | 0.0161 | 0.0742 | 0.0986 |
| value-bearing | 33.5 | 61 | 1 | 0.0164 | 0.0754 | 0.1001 |
| three-family | 33.3 | 64 | 2 | 0.0312 | 0.0951 | 0.1210 |
| two-family | any | 0 | 0 | - | - | - |

At delta = 0.05 the rule holds at every threshold and its minimum is 33.3, the
deployed value. At delta = 0.0125 the all-accepts reading **fails at every
threshold**; only the value-bearing subset satisfies it, at 33.3 and 33.4.

Of the 10 false cliques, 8 score 22.x (excluded by the threshold) and 2 score
33.x, one of which has no base value.

Stream reconciliation: **174 ACCEPT, 4 removed (3 dev-split, 1 without a base
value) leaves 170 value-bearing non-dev, 138 admitted at 33.3, 22 round-aware
disagreements, 26 under the 2dp ruler.** All gates hit exactly.

---

## 3. Task 1. Code facts

Script `code_facts.py` plus direct quotation, output `01_code_facts_data.md`.

| Item | Fact |
|---|---|
| 1.1 informative rule | at least **two** candidates return a finite value (`consensus.py:164`) |
| 1.1 minimum informative | 3 (`min_informative=3`, line 138) |
| 1.1 tolerance | `abs(a-b) <= 1e-4 * max(1.0, abs(a), abs(b))` (line 125); `e1_certify.py:49` never overrides it |
| 1.1 clique | maximum clique over the agreement graph; the two-family requirement is applied **after** the search (line 187), so a smaller cross-family clique is never preferred |
| 1.1 decision order | UNINFORMATIVE, then ACCEPT, then ABSTAIN |
| 1.1 base instance | inserted at index 0 (line 143) and participates in the agreement graph |
| 1.2 deployed score | `10*families + clique_size + informative/10` (`e3_calibrate.py:127`); the `informative/10` digit collides with the clique-size digit at 10 informative instances, unreachable at m = 5 (maximum 6) |
| 1.4 stream | 298 specs, **173** with at least one integer parameter, **629** integer parameters, **1,289 rel / 771 abs** |
| 1.4 calibration | 148 specs, 63, 117, 283 / 137 |
| 1.4 sampler | continuous draw then `round(v)`; not an integer-uniform draw |
| 1.5 infeasible | **1,209 of 4,470** (candidate, resampled instance) pairs = **27.0%**; **60** problems where every resample failed for every base-solving candidate |
| 1.6 vote arm | host rollout, exactly **3** trajectories per problem (min = median = max), single backbone |
| 1.7 gate arm | 151 eligible problems x 3 = 453 candidates, 413 positive; **99 clusters, all built, 101 files**; 80 clusters of 3, tail to 39 |
| 1.8 demo | `sum(x) <= 150`, `bounds=(0,60)`, floor `>= 20`, profit over `[-2, 9]`; a profit perturbation does separate the two candidates |
| 1.9 ReLoop | none found |
| 1.10 bookkeeping | **174 ACCEPT / 114 UNINFORMATIVE / 10 ABSTAIN = 298**; the two missing verdicts are `sample_108` and `sample_244`, both `ERROR`, both "extractor output not parseable JSON, likely truncated" |

### 1.3 Host ledger by phase

Script `runlog_phase_audit.py`, output `01_3_runlog_phases.md`, `.csv`.

60,000 `llm` records, all `(family=deepseek, strategy=host)`. **58,575
`deepseek-v3.2`, 1,425 `deepseek-v3-2-251201`, zero outside those two.** The
dated variant concentrates in the ground-truth arm: gt/OptiBench 728 (10.5% of
that phase), gt/Mamo.C 405 (10.4%), gt/IndustryOR 39, E1 collect 27,
unattributed 222, other phases 4.

Extractor and candidate-arm calls are absent from this ledger entirely; they
bypass the host transport. Their volume is recoverable from artifacts (298
extractions, 892 candidate generations) but their response models were never
recorded.

---

## 4. Task 3.0. Gate arm composition

Script `gate_arm_composition.py`, output `03_0_gate_arm_composition.md`.

`GateOracle.effective_gt` applies **no score threshold**. The E1 library was
built under ACCEPT-with-a-value, so two-family cliques entered it.

| Clique span | eligible problems | admitted candidates | poison | precision |
|---|---:|---:|---:|---:|
| three-family (33.x) | 121 | 344 | 22 | 0.936 |
| two-family (22.x) | 27 | 69 | 8 | 0.884 |
| total | 148 | 413 | 30 | 0.927 |

Library composition: 99 clusters built, **22 files contain at least one
two-family trajectory, 16 consist only of them** and would disappear under
tau, 11 files hold all 30 poison admissions, one file holds 9.

The appendix example "Bin Packing with Resource Activation" is
**three-family-only and survives tau**; two of the other three bin-packing
files do not.

---

## 5. Task 5b. Serving variant by eval outcome

Script `serving_variant_join.py`, output `05b_serving_variant_join.md`, `.csv`.

Attribution 97.3% (4,283 of 4,400) by cache join. Runlog join unavailable;
time-window fallback deliberately unused because 12 concurrent workers make it
unsound.

**Every one of the 117 `e1_eval_failure` rows is unattributed, and every
attributed item has zero failures.** For gt/OptiBench the two sets are
identical: the 85 unattributed items are the 85 failures. Fisher exact on
failure is p = 1.0000 in every cell. The failures occur at the selector stage
before any cacheable response exists.

Accuracy shows no consistent effect: gt/OptiBench pinned 74.9% against variant
65.4% (p = 0.0947), gt/Mamo.C pinned 52.4% against variant 65.0% (p = 0.3489).
The co-occurrence of the variant and the failures in the same cell is volume,
not association.

---

## 6. Task 3. Decomposition

Scripts `panel_base_judges.py`, `candidate_crosstab.py`, `task3_additions.py`;
outputs `03_decomposition.md`, `03_decomposition_problem.csv`,
`03_decomposition_candidate.csv`, `03_pairs.csv`, `03_verdicts/`.

Rule 9 proof: `label_oracle.py` was **not modified**. The derived verdicts are
already in GateOracle shape, so the existing gate mode was pointed at each
judge's directory. Re-running the vote arm reproduced the stored file
byte-identically at 128,677,611 bytes.

### 3.2 Problem-level certificate accuracy

| Judge | n certified | n wrong | false proportion | CP95 | CP98.75 |
|---|---:|---:|---:|---:|---:|
| host_vote | 254 | 38 | 0.1496 | 0.1914 | 0.2069 |
| panel_base_2of3 | 245 | 38 | 0.1551 | 0.1983 | 0.2142 |
| panel_base_3of3 | 200 | 26 | 0.1300 | 0.1758 | 0.1928 |
| gate_asdeployed | 170 | 29 | 0.1706 | 0.2252 | 0.2453 |
| gate_tau | 138 | 22 | 0.1594 | 0.2198 | 0.2419 |

`runsok` defines no problem-level certificate. Chain cases: **0**.

### 3.3 Candidate-level admission precision

| Judge | admitted | poison | precision | recall | eligible |
|---|---:|---:|---:|---:|---:|
| runsok | 878 | 241 | 0.726 | 1.000 | 295 |
| vote | 721 | 93 | 0.871 | 0.986 | 256 |
| panel_base_2of3 | 610 | 45 | 0.926 | 0.887 | 220 |
| panel_base_3of3 | 516 | 32 | **0.938** | **0.760** | 182 |
| gate_asdeployed | 413 | 30 | 0.927 | 0.601 | 148 |
| gate_tau | 344 | 22 | 0.936 | 0.505 | 121 |

Reconciliation gate passed on all three published rows before any new row was
accepted. Recall denominator: 637 vault-correct trajectories.

### 3.4 Pair B, what resampling removed

`gate_tau` is a strict subset of `panel_base_3of3` (0 exceptions). The
62-problem difference:

| Gate outcome | problems | base cert wrong | right |
|---|---:|---:|---:|
| gate_tau admitted | 138 | 22 | 116 |
| UNINFORMATIVE | **57** | **4** | **53** |
| ACCEPT, clique reduced to two families | 4 | 0 | 4 |
| ABSTAIN | 1 | 0 | 1 |

The 62 rejected problems were **58 right and 4 wrong**, a 6.5% false rate
against the 15.9% of what was kept. **57 of 62 were rejected for insufficient
informative instances, not for disagreement.**

### Additions

(a) Value exclusions split: **8 base-visible, 4 resample-only** (A 3/0, B 4/3,
C 1/1). Only 4 of 12 required a resampled instance to detect.

(b) The five base-unanimous problems whose candidates diverged: **the vault
confirms the base certificate in 5 of 5**. Four are sampler artefacts
(`sample_140` drew -1 into a 0/1 preference matrix; `sample_17` a continuous
value into an integer demand; `sample_288` a gurobipy dimension crash;
`sample_81` diverged on `crate_weight: -8.41`, a negative weight). Only
`sample_93` is a genuine cross-family disagreement, and its base value was
also right.

(c) Identity: on all **138** gate_tau problems the gate certificate equals the
`panel_base_3of3` certificate. **0 mismatches.** Resampling never changed a
certificate, only whether one was issued.

---

## 7. Task 4. Paired bootstrap

Script `corrected_bootstrap.py` (unmodified), output `04_bootstrap.md`.
Seed 42, 10,000 resamples, stratified by plate. Three reconciliation gates
passed.

| Pair | Scale | R0 | R1 | Excludes zero |
|---|---|---|---|---|
| gate - gt | macro | +4.46 [+2.34, +6.65] | +2.14 [+0.04, +4.29] | yes, yes |
| gate - gt | micro | +6.73 [+4.36, +9.18] | +0.59 [-1.48, +2.66] | yes, **no** |
| gate - vote | macro | +3.53 [+0.87, +6.68] | +3.49 [+0.78, +6.73] | yes, yes |
| gate - vote | micro | +1.73 [-0.27, +3.73] | +1.77 [-0.39, +3.84] | **no, no** |
| gate - runsok | macro | +1.84 [-0.27, +3.96] | +1.79 [-0.26, +3.96] | **no, no** |
| gate - runsok | micro | +1.27 [-0.73, +3.27] | +1.28 [-0.79, +3.45] | **no, no** |

**gate minus runsok includes zero on both scales at both bases.**

---

## 8. Task 5. Retrieval and selection

Scripts `retrieval_stats.py`, `retrieval_final.py`; outputs
`05b_retrieval_concentration.md`, `05_retrieval.md`, `.csv`.

`e1_eval_failure` rows: gt 95 (0/4/4/2/85), vote 10, runsok 10, gate 2.

`in_library` equals `with_skill_id` in every cell: the selector **never
returned a nonexistent id**. Every selection-failure row scores 0.00.

gt/OptiBench accuracy conditional on selection success is **73.46**, which
reproduces the paper's 73.5 sensitivity read by a third route.

Retrieval concentration on OptiBench: gt 31 distinct files / 20.3% top share;
vote 38 / 32.2%; runsok 30 / 39.5%; **gate 19 / 44.6%**. The smallest library
is used most narrowly.

---

## 9. Task 6. Provenance and disjointness

Script `disjointness_audit.py`; outputs `06_provenance.md`,
`06_similarity_pairs.md`, `06_max_similarity.csv`.

Stream: first 300 by index of the host's OptMATH training split, indices
contiguous, so selection is by index rather than a seeded sample. sha256
recorded for all four files.

| Set | items | exact | normalized | Jaccard >= 0.8 | max Jaccard |
|---|---:|---:|---:|---:|---:|
| stream | 300 | 0 | 0 | 0 | 0.2059 |
| calibration | 245 | 0 | 0 | 0 | 0.0201 |

**No contamination at any level**, including OptMATH-train against
OptMATH-Bench. difflib not run per the scope cut.

---

## 10. Task 7. Numeric-coverage screen

Script `numeric_coverage.py`; outputs `07_coverage.md`, `07_coverage.csv`.

| Group | n | F1 flagged | F2 flagged | mean coverage |
|---|---:|---|---|---:|
| 22 round-aware disagreements | 22 | 9 (40.9%) | 9 (40.9%) | 0.776 |
| 116 concordant tau-admissions | 116 | **0 (0.0%)** | 0 | 0.999 |
| value-bearing accepts not admitted | 160 | 12 (7.5%) | 14 (8.8%) | 0.946 |
| calibration specs (control) | 148 | **0 (0.0%)** | 0 | 0.998 |

**Fisher two-sided p = 0.0000** on the 138, for both rules.

By class: `d-missing` 9 of 15 flagged; `d-truncated` **0 of 5**; label error
**0 of 2**. Perfect specificity on the classes that should not flag, 60%
sensitivity on the class that should.

Packets (7.3) not built; deferred past the stop per the scope cut.

---

## 11. Task 8. Restricted K4

Script `k4_restricted.py`; output `08_k4_restricted.md`.

| Table | chi-square | df | p | Monte Carlo p |
|---|---:|---:|---:|---:|
| published 3x5 | 30.96 | 8 | 1.4e-4 | - |
| 3x2, value comparison only | **8.75** | 2 | **0.0126** | 0.0116 |
| 3x3, adding infeasible | 10.30 | 4 | 0.0356 | 0.0348 |

Crashes carry most of the published statistic, but restriction still rejects
uniformity at p = 0.013. Exact Freeman-Halton enumeration is intractable at
these margins; a fixed-margin Monte Carlo permutation test at 200,000
replicates was used and agrees with the asymptotic p to three decimals.

---

## 12. Task 9. Two- and three-extractor preliminary

Scripts `two_extractor_run.py`, `two_extractor_agreement.py`; outputs
`09_two_extractor.md`, `.csv`, `09_cases.csv`, `09_extractions/`.

Groups matched on deployed score: wrong 0/3/3/16 across 33.3/33.4/33.5/33.6,
controls 1/2/1/18.

| Level | E = 3 wrong | E = 3 control | Fisher p |
|---|---|---|---:|
| L1 key names | 22 / 22 | 22 / 22 | 1.0000 |
| L2 value alignment | 18 / 22 | 21 / 22 | 0.3449 |
| L3 elementwise values | 18 / 22 | 21 / 22 | 0.3449 |
| L4 perturbation domains | 22 / 22 | 22 / 22 | 1.0000 |

**L1 disagrees 100% in both groups**: independent extractors never agreed on
key names. **L2 and L3 do not separate the groups and the sign runs the wrong
way** (the failure class disagrees less often than controls). E = 2 shows the
same pattern (18/22 against 20/22, p = 0.664).

Truncated-precision cases behave as predicted: 1 of 5 disagrees at L2/L3
against 5 of 5 at L1 and L4.

Exploratory decomposition (not a preregistered rule): value-conflicting
shape-matched parameters total 38 for class (d), **0 for label errors**, 10
for controls. Unmatched parameters dominate everywhere (244 / 50 / 764) and
swamp that signal, which is why L2 does not separate.

The statistic "cases where all three extractors produced identical values for
data the text does not print" is **not measurable at this alignment rate**: it
requires a three-way L2 alignment, which succeeds in only 5 of 44 cases. The
table shows 0; that is an absence of measurement, not an absence of
occurrences.

---

## 13. Task 12. Packet annotation

22 copies regenerated in `reanalysis/reviewer_round/k3_packets_ticked/`:
**2 ticked (b)**, **20 annotated** with a new line `(d) text is not a faithful
encoding of the labeled instance: [x]` plus the sub-class in the notes.
**No (c) box is ticked anywhere.** The originals under `outputs/e3/review/`
were verified untouched (0 files contain `[x]`).

---

## 14. Task 13. Release hygiene

See `13_release.md`. Branch `reviewer-round-2026-09`, commit `0cd3f30`, one
commit ahead of `origin/main`, **not pushed**. Secret sweep: **0 hits over
1,203 files**. Six files shipped under `release/`, all aggregate or
identifier-only, verified to contain zero vault answers.

13.1, the full script index, is deferred past the stop.

---

## 15. Task 14. Figures

14.1 **not done**: no figure generator exists in the project, and
`fig2_pipeline.pdf` is a rasterized image with no text layer (0 characters, 0
fonts, 0 vector drawings), so the gate box cannot be edited programmatically.
The box already reads "Calibrated Gate" in the figure re-exported on
2026-08-16; the two sub-lines require the original drawing source.

14.2 cancelled by amendment. 14.3 dropped by scope cut.

---

## 16. LLM cost ledger

Task 9 only. Everything else is zero-token.

| Family | calls | prompt | completion | total | errors |
|---|---:|---:|---:|---:|---:|
| `claude-sonnet-4-6` | 44 | 60,858 | 22,209 | 83,067 | 0 |
| `gpt-5.4` | 44 | 49,660 | 23,867 | 73,527 | 0 |
| **total** | **88** | **110,518** | **46,076** | **156,594** | **0** |

Every response returned its own model name. Pre-run projection was 134,332
tokens; actual 156,594, 17% over, still far inside the $20 ceiling (public
list rates put this near $1). Two connectivity probes earlier in the round
added roughly 400 tokens.

---

## 17. Open questions for Jacob

1. **`gate_asdeployed` against `gate_tau` in the manuscript.** Table 2's
   downstream number belongs to the first rule; the K3 analysis to the second.
   The text currently reads as one gate. This needs an explicit sentence.
2. **The decomposition result.** `panel_base_3of3` certifies more problems at
   a lower false rate and admits more candidates at equal-or-better precision
   than either gate, and the certificate value is identical on all 138 shared
   problems. Three independent measurements agree. How much of Section 4 is
   rewritten around this is a decision I cannot make.
3. **Task 9's negative result.** Data-layer redundancy does not separate the
   failure class at E = 2 or E = 3. The paper proposes it as the remedy for 20
   of 22 false certificates.
4. **Task 7's positive result.** The numeric-coverage screen has zero false
   positives across 116 concordant admissions and 148 calibration specs and
   catches 9 of 15 `d-missing` cases. It is a deployable pre-filter and is not
   in the paper.
5. **`gate - runsok` interval.** It includes zero on both scales at both
   bases. The paper compares against execution success without an interval.
6. **The paper `.tex`.** No `.tex` exists in the repo. The archive
   `admitor-infra/admitor_paper.zip` holds one dated 2026-08-15 02:20, older
   than v33. All bundles carry it as reference only.
7. **`.gitignore`** remains modified and uncommitted (the `reanalysis/` entry).

---

## 18. Numbers for the manuscript

| Number | Script | Output file |
|---|---|---|
| Calibration table, both units, both deltas | `e3_certificate_numbers.py` | `02_calibration_table.md`, `.csv` |
| 174 / 170 / 138 | `e3_certificate_numbers.py` | `02_calibration_table.md` |
| 22 round-aware, 26 2dp, split 21 / 5 / 1 | `e3_certificate_numbers.py` | `02_calibration_table.md` |
| 7 of 30 poison from round-aware-right certificates | ad hoc, recorded in this report | section 1 row 11 |
| Gate arm composition 121 / 27, 344 / 69, 22 / 8, 0.936 | `gate_arm_composition.py` | `03_0_gate_arm_composition.md` |
| Library composition 99 / 101 / 16 / 6 / 11, top file 9 | `gate_arm_composition.py`, `poison_provenance.py` | `03_0_gate_arm_composition.md`, `03_0_poison_provenance.md` |
| Problem-level accuracy, five judges | `panel_base_judges.py` | `03_decomposition.md`, `03_decomposition_problem.csv` |
| Candidate-level precision and recall, six judges | `candidate_crosstab.py` | `03_decomposition_candidate.csv` |
| Pair A and Pair B counts, 62 = 57 + 4 + 1 | `panel_base_judges.py` | `03_pairs.csv` |
| Exclusion split 8 / 4; five divergences; identity 138 / 138 | `task3_additions.py` | `03_decomposition.md` |
| Bootstrap intervals, three pairs, two scales, two bases | `corrected_bootstrap.py` | `04_bootstrap.md` |
| Retrieval concentration and failure rows | `retrieval_final.py` | `05_retrieval.md`, `.csv` |
| 73.46 conditional accuracy | `retrieval_final.py` | `05_retrieval.md` |
| Serving-variant join, 117 failures all unattributed | `serving_variant_join.py` | `05b_serving_variant_join.md` |
| Provenance hashes and maximum similarities | `disjointness_audit.py` | `06_provenance.md`, `06_max_similarity.csv` |
| Coverage flag rates and Fisher | `numeric_coverage.py` | `07_coverage.md`, `.csv` |
| K4 restricted 8.75 / 2 / 0.0126 | `k4_restricted.py` | `08_k4_restricted.md` |
| Two-extractor results and spend | `two_extractor_agreement.py` | `09_two_extractor.md`, `.csv` |
| Informative >= 2; tolerance formula; decision order | quotation | `01_code_facts_data.md` |
| 173 / 629 / 1,289 / 771 and 63 / 117 / 283 / 137 | `code_facts.py` | `01_code_facts_data.md` |
| 27.0% infeasible, 60 all-dead problems | `code_facts.py` | `01_code_facts_data.md` |
| ERROR samples 108 and 244 | `code_facts.py` | `01_code_facts_data.md` |
| Demo `sum(x) <= 150`, bounds (0,60), floor 20, profit [-2, 9] | quotation | `01_code_facts_data.md` |
| Runlog audit 60,000 / 58,575 / 1,425, per-phase | `runlog_phase_audit.py` | `01_3_runlog_phases.md`, `.csv` |
| Feasibility resampling recovery | `feasibility_resampling.py` | `11_feasibility_resampling.md` |

---

## 19. Task 11. Feasibility-preserving resampling diagnostic

Script `feasibility_resampling.py`; output `11_feasibility_resampling.md`, `.csv`.
`run_l3` unmodified; only the instance generator is replaced. Retry rule:
m = 5, seed 20260916, at most 10 attempts per draw, a draw rejected when no
candidate that solved the stated instance can solve it.

| Quantity | Value |
|---|---:|
| the 57 base-unanimous UNINFORMATIVE problems | 57 |
| re-run successfully | 57 |
| reaching three informative instances | **8** |
| verdict ACCEPT | **8** |
| verdict ABSTAIN | 0 |
| verdict UNINFORMATIVE | **49** |
| certificate equals the base-unanimous value | **8 of 8** |
| certificate correct against the vault | **7** |
| certificate wrong against the vault | **1** |

Feasibility-preserving resampling recovers **8 of 57, about 14 percent** of
the coverage loss. The remaining 49 stay UNINFORMATIVE even when every draw
is screened for solvability, so the limit is not unlucky draws: the
extracted domains yield instances that are infeasible or structurally
invalid across essentially all attempts. This is consistent with Task 1.5
(27.0 percent of resampled pairs infeasible, 60 problems with every resample
dead) and with Task 3 addition (b), where four of five divergences were
sampler artefacts.

Every one of the 8 recovered certificates equals the base-unanimous value,
which is the third independent confirmation that resampling never changes a
certificate, only whether one is issued. Of the 8, **7 are correct against
the vault**; the recovered set is not less accurate than the admitted set
(116 of 138 correct).

The 8 recovered problems:

| Problem | informative | decision | families | certificate | = base value | vault correct | mean attempts |
|---|---:|---|---:|---|---|---|---:|
| sample_105 | 3 | ACCEPT | 3 | 1771562.0 | True | True | 7.2 |
| sample_137 | 6 | ACCEPT | 3 | 317278.21244160313 | True | False | 3.0 |
| sample_196 | 6 | ACCEPT | 3 | 3.0 | True | True | 5.2 |
| sample_250 | 6 | ACCEPT | 3 | 337961.4308110118 | True | True | 3.2 |
| sample_266 | 6 | ACCEPT | 3 | 69355.5 | True | True | 1.8 |
| sample_300 | 6 | ACCEPT | 3 | 4815.0 | True | True | 1.8 |
| sample_6 | 6 | ACCEPT | 3 | 14604.0 | True | True | 4.4 |
| sample_76 | 6 | ACCEPT | 3 | 13.0 | True | True | 2.8 |

Variant B (reject a draw on which fewer than two candidates return a finite
value) was **not run**: variant A alone took 45 minutes, and B rejects on a
stricter rule so it would take longer than the 2026-09-20 stop allows.

