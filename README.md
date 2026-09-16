<div align="center">

# AdmitOR

### Admission Without Answers<br>Label-Free Certification and Experience Learning for LLM-Based Optimization Modeling

**Junbo Jacob Lian** &nbsp;·&nbsp; **Huiling Chen** &nbsp;·&nbsp; **Hanzhang Qin** &nbsp;·&nbsp; **Chung-Piaw Teo**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![arXiv](https://img.shields.io/badge/arXiv-2608.15565-b31b1b.svg)](https://arxiv.org/abs/2608.15565)
[![Release](https://img.shields.io/badge/release-v1.1.0-2ea44f.svg)](https://github.com/junbolian/AdmitOR/releases/tag/v1.1.0)
[![Tests](https://img.shields.io/badge/tests-14%20passing%20offline-2ea44f.svg)](#installation)
[![Artifacts](https://img.shields.io/badge/artifacts-MANIFEST-informational.svg)](artifacts/MANIFEST.md)
[![Host](https://img.shields.io/badge/host-OptSkills-181717.svg?logo=github)](https://github.com/fujiwaranoM0kou/OptSkills)

**Certify an optimization model's answer without ever seeing an answer key.**

[**Paper**](https://arxiv.org/abs/2608.15565) &nbsp;·&nbsp; [**Release v1.1.0**](https://github.com/junbolian/AdmitOR/releases/tag/v1.1.0) &nbsp;·&nbsp; [**Artifacts**](artifacts/MANIFEST.md)

</div>

Revised manuscript (September 2026) and the reviewer-round analyses: see
"Reviewer-round analyses (September 2026)" below. The arXiv version will be updated after the
review period.

---

## What this is

AdmitOR is an admission gate that decides whether a model-produced answer to an
optimization problem may be trusted, **without ever consulting an answer key**.

One extractor turns the problem text into a base-anchored parameter-domain
specification. Three model families independently write solver code against
that shared specification, and each candidate is re-examined over a set of
**resampled instantiations** of the parameter domain, so what is compared is an
entire induced value function rather than a single number. Agreement is
compressed into a maximum clique, and a verdict is issued only when that clique
**spans at least two model families**:

| Verdict | Meaning |
|---|---|
| `ACCEPT` | a cross-family clique agrees everywhere; its value at the base instance is the certified answer |
| `ABSTAIN` | informative instances exist, but no cross-family clique does |
| `UNINFORMATIVE` | too few instantiations were solvable to judge |

A conformal calibration step thresholds admission to a target false-discovery
budget, so the gate can be tuned to a **stated purity** rather than a hope.

![Overview](figures/fig1_overview.png)

![Pipeline](figures/fig2_pipeline.png)

---

## Key results

Downstream accuracy (%, round-aware scorer) of the host equipped with each
judge's library. Every arm replays the same collection logs, so **the judge is
the only difference between rows**. Bold marks the column best (Table 2).

| Admission policy | ComplexOR | IndustryOR | Mamo.Complex | OptMATH-Bench | OptiBench | **Macro** |
|:---|---:|---:|---:|---:|---:|---:|
| GT labels | **66.67** | 31.00 | 52.61 | **56.02** | 63.14 | 53.89 |
| Vote | 61.11 | 33.00 | 53.55 | 54.22 | 72.23 | 54.82 |
| RunsOK | **66.67** | 35.00 | 53.08 | 55.42 | **72.40** | 56.51 |
| **Gate (AdmitOR)** | **66.67** | **39.00** | **57.82** | **56.02** | 72.23 | **58.35** |

**The certified library is the smallest of the four and scores highest.** All
three label-free policies clear the preregistered bar of 70% of the
GT-supervised macro, landing at **102 to 108%** of it. Under a plate-stratified
paired bootstrap, gate minus vote is **+3.53pp** macro, 95% CI
**[+0.87, +6.68]**; gate minus GT is **+4.46pp**, 95% CI **[+2.34, +6.65]**.

The family-by-outcome matrix over 298 certification runs is significantly
non-uniform (**chi-squared 30.96**, df 8, **p = 1.4e-4**): crash behavior
tracks the solver stack rather than being spread evenly across arms.

![Library size against downstream accuracy](figures/fig3_quality.png)

> [!NOTE]
> Two results are reported with caveats in the paper and are worth knowing
> before you build on this. The GT/OptiBench cell is depressed by 85
> selector-failure rows; excluding them as a sensitivity read puts ground truth
> at 73.5 on OptiBench and 55.95 macro, and the gate still leads. And the
> conformal budget calibrated on solver-verified problems does **not** transfer
> to the wild stream: replayed FDR is 15.9%, against a preregistered 5%. See
> Sections 4.2 and 4.3 of the paper for both in full.

---

## Repository structure

```
AdmitOR/
├── admitor/          THE GATE          consensus · ir_extract · generate · pipeline_one
├── scripts/          EXPERIMENT DRIVERS
│   ├── E0            data_audit · e0_scorecard
│   ├── E1            label_oracle · e1_relabel · e1_certify · e1_rebuild
│   ├── E3            e3_calibrate · k4_matrix · review_packet
│   ├── shared        score_eval · paired_bootstrap · regen_derived · runlog
│   └── reviewer      the reviewer-round analyses (see "Reproducing the paper's numbers")
├── datasets/         benchmark/ · train_set/ · vault/   (third-party, see datasets/README.md)
├── artifacts/        verdicts · skill libraries · E3 reports · run-ledger excerpt
├── release/          reviewer-round outputs · K3 review packets · E0 scorecard
├── patches/          OptSkills host patches as unified diffs
├── release_tools/    scrub_logs.py · make_manifest.py
├── tests/            offline suite, no API key needed
└── figures/          paper figures (PNG + PDF source)
```

---

## Installation

```bash
conda env create -f environment.yml -n optskills
conda activate optskills
pytest -q          # 14 passed, fully offline, no API key
```

`environment.yml` is the pinned specification. It is the environment the E1 experiments ran
in, and every shipped output under `release/reviewer_round/` was re-verified in it: Python
3.12.12, numpy 2.4.4, scipy 1.18.0, Pyomo 6.10.0, HiGHS 1.15.1 (gurobipy 13.0.1 optional).
The code runs on Python 3.8+.

**HiGHS** is the default solver and is installed for you. **Gurobi is optional
and commercial**, needed only to reproduce the `C-direct` candidate arm live
(`pip install gurobipy==13.0.1`, [academic licences](https://www.gurobi.com/academics)).
Everything else, including the whole test suite, runs without it.

---

## Quickstart

Offline self-test, no network and no credentials:

```bash
python -m admitor.pipeline_one --mock
```

To certify a real problem, put the statement in a text file and set the
endpoint. Credentials are read from **environment variables only**; no endpoint
is baked into the code.

```bash
export ADMITOR_API_KEY="your-key"
export ADMITOR_BASE_URL="https://api.openai.com/v1"
python -m admitor.pipeline_one --question my_problem.txt --m 5
```

The three families default to `deepseek-v3.2`, `gpt-5.4` and
`claude-sonnet-4-6` (override with `ADMITOR_MODEL_A/B/C`), all at temperature 0
with **m = 5** resampled instances plus the base instance.

Artifacts land in `runs/<timestamp>/`, including the verdict:

```json
{
  "decision": "ACCEPT",
  "clique": ["B-structured", "C-direct"],
  "families": ["claude", "gpt"],
  "objectives": {
    "A-direct":     [960.0, 363.54, 706.35, 627.31, 237.84, 320.16],
    "B-structured": [960.0, 329.04, 706.35, 606.43, 204.39, 285.99],
    "C-direct":     [960.0, 329.04, 706.35, 606.43, 204.39, 285.99]
  },
  "diagnoses": {
    "A-direct": "diverges from consensus by 34.5 on instance 1 (params: ...)"
  }
}
```

Index 0 is the base instance, so `objectives[clique[0]][0]` is the certified
answer. `diagnoses` explains what excluded every candidate outside the clique.
A non-ACCEPT verdict certifies nothing: abstain or escalate, never fall back on
an uncertified value.

---

## Reproducing the paper

Datasets ship in `datasets/`, so nothing needs downloading. All three
experiments need the OptSkills host, which is not redistributed here.

<details>
<summary><b>Host setup</b></summary>

```bash
git clone https://github.com/fujiwaranoM0kou/OptSkills.git
cd OptSkills
git checkout 7d3194098e17f8f032359d8ad507bbe6bfc208fa
git apply /path/to/AdmitOR/patches/llm_caller.patch
git apply /path/to/AdmitOR/patches/runner.patch
```

See [`patches/README.md`](patches/README.md) for what each patch does.

</details>

<details>
<summary><b>E0 · bench calibration</b></summary>

```bash
# free: mining pool must not overlap any benchmark
python scripts/data_audit.py --root datasets

# costs tokens: host eval, once per benchmark, from the host root
python main.py --phase eval --data <AdmitOR>/datasets/benchmark/optibench.jsonl \
    --run-dir outputs/eval/optibench --resume --eval-workers 12 --timeout 120

# free: score and read the verdict
python scripts/score_eval.py <host>/outputs/eval/optibench/trajectories.jsonl
python scripts/e0_scorecard.py scorecard.json
```

</details>

<details>
<summary><b>E1 · the judge swap</b> (the main result)</summary>

```bash
# free: verify the blind mining file against the paper's sha256
python scripts/regen_derived.py --source datasets/train_set/optmath-train-300.jsonl

# costs tokens: collect rollouts once, from the host root
python main.py --phase cluster \
    --data <AdmitOR>/datasets/train_set/optmath-train-300-blind.jsonl \
    --run-dir outputs/e1/collect --resume \
    --cluster-eps 0.05 --cluster-min-samples 1 --agent-max-turns 12

# costs tokens: certify. Skip this by pointing --verdicts-dir at
# artifacts/e1/certify_verdicts/, which ships all 300 verdicts.
python scripts/e1_relabel.py --collect <collect>/trajectories.jsonl --arm gate \
    --verdicts-dir outputs/e1/verdicts --out outputs/e1/arms/gate.jsonl \
    --work-order outputs/e1/gate_workorder.jsonl
python scripts/e1_certify.py --work-order outputs/e1/gate_workorder.jsonl \
    --verdicts-dir outputs/e1/verdicts --runs-dir outputs/e1/certify_runs --m 5

# free: relabel the other three arms
python scripts/e1_relabel.py --collect <collect> --arm vote   --out outputs/e1/arms/vote.jsonl
python scripts/e1_relabel.py --collect <collect> --arm runsok --out outputs/e1/arms/runsok.jsonl
python scripts/e1_relabel.py --collect <collect> --arm gt \
    --labels datasets/vault/optmath-train-300-labels.jsonl --out outputs/e1/arms/gt.jsonl

# costs tokens: rebuild one library per arm (the four we used ship in
# artifacts/e1/libraries/), then evaluate each on all five benchmarks
python <AdmitOR>/scripts/e1_rebuild.py --relabeled <arm>.jsonl \
    --library outputs/e1/libs/skill_library_gate \
    --cluster-eps 0.05 --cluster-min-samples 1 \
    --archetype-fusion-alpha 0.55 --agent-max-turns 12

# free: score the matrix and the intervals
python scripts/paired_bootstrap.py --eval-root <your e1 eval root> \
    --pairs gate:vote gate:gt --reps 10000 --seed 42
```

Pass exactly the cluster geometry the collect run used, or the comparison is
confounded. Eval trajectories run to hundreds of megabytes, so they ship as the release
asset `admitor-v1.1.0-run-records-eval.zip` rather than in git (see "Reproducing the
paper's numbers").

</details>

<details>
<summary><b>E3 · conformal calibration</b></summary>

```bash
# free
python scripts/e3_calibrate.py workorder --nano datasets/train_set/nano-co.jsonl \
    --out outputs/e3/e3_workorder.jsonl --labels outputs/e3/e3_labels.jsonl --n 150 --seed 42

# costs tokens
python scripts/e1_certify.py --work-order outputs/e3/e3_workorder.jsonl \
    --verdicts-dir outputs/e3/verdicts --runs-dir outputs/e3/certify_runs

# free: fit, then replay onto the 300 E1 verdicts using shipped artifacts
python scripts/e3_calibrate.py fit --runs outputs/e3/certify_runs \
    --labels outputs/e3/e3_labels.jsonl --alpha 0.05 --out outputs/e3/calibration.json
python scripts/e3_calibrate.py replay --calibration artifacts/e3/calibration.json \
    --e1-runs artifacts/e1/certify_runs --verdicts artifacts/e1/certify_verdicts \
    --workorder outputs/e1/gate_workorder.jsonl \
    --vault datasets/vault/optmath-train-300-labels.jsonl --out outputs/e3/e3_report.json

# free: the K4 contingency table
python scripts/k4_matrix.py --e1-runs artifacts/e1/certify_runs --out outputs/e3/k4_matrix.json
```

`k4_matrix.py` emits the table; this reproduces the reported statistic from it:

```bash
python -c "import json;from scipy.stats import chi2;m=json.load(open('artifacts/e3/k4_matrix.json'))['matrix'];a=sorted(m);o=sorted({x for c in m.values() for x in c});O=[[m[i].get(j,0) for j in o] for i in a];R=[sum(r) for r in O];C=[sum(O[i][j] for i in range(len(a))) for j in range(len(o))];N=sum(R);s=sum((O[i][j]-R[i]*C[j]/N)**2/(R[i]*C[j]/N) for i in range(len(a)) for j in range(len(o)));d=(len(a)-1)*(len(o)-1);print(f'chi2={s:.2f} df={d} p={chi2.sf(s,d):.1e}')"
# chi2=30.96 df=8 p=1.4e-04
```

</details>

---

## Artifacts

| Path | Contents |
|:---|:---|
| `artifacts/e1/certify_verdicts/` | **300** compact gate verdicts |
| `artifacts/e1/certify_runs/` | **298** full verdicts with clique geometry |
| `artifacts/e1/libraries/` | the **four** skill libraries exactly as evaluated |
| `artifacts/e3/` | calibration, both replay reports, the K4 matrix |
| `artifacts/runlogs/` | a **2,000**-record excerpt of the per-call ledger |

[`artifacts/MANIFEST.md`](artifacts/MANIFEST.md) lists every artifact with its
size, sha256 and the paper table it backs. Verify the whole set with
`python release_tools/make_manifest.py`.

The complete scrubbed run ledger (**93,909** records) is attached to the
[v1.0.0 Release](https://github.com/junbolian/AdmitOR/releases/tag/v1.0.0)
rather than committed, since it grows with every campaign. The run records of every arm
(collection, relabeled arms, certification runs with specifications and candidate programs,
evaluation trajectories, response cache, runtime logs) are the four-part v1.1.0 release asset;
`release/` holds the reviewer-round outputs, the 22 K3 review packets and the E0 scorecard.
Everything released passed through `release_tools/scrub_logs.py`, which is committed so the
scrubbing is auditable.

---

## Reviewer-round analyses (September 2026)

All analyses in this section are zero-token: no script in it calls a model. Their inputs are
the released verdicts and libraries (in git), the run records (release asset
`admitor-v1.1.0-run-records.zip`, see "Reproducing the paper's numbers"), and the host call
ledger (release asset of v1.0.0). Outputs are under `release/reviewer_round/`;
`REPORT_reviewer_round_2026-09.md` there is the full report. Three of the analyses run from
the git checkout alone (`task3_additions.py`, `disjointness_audit.py`, `k4_restricted.py`);
the others need the run-records asset unpacked next to the checkout. One exception:
`feasibility_resampling.py` re-solves candidate programs and its outputs are shipped as
recorded; the other numbers below were regenerated from the released inputs before this
release and matched the shipped files byte for byte.

### Judge ablation on the stored records (manuscript Table 3)

Three judges are derived from the stored certification verdicts without model calls:
agreement of any two panel families at the stated instance, unanimity of all three at the
stated instance, and the calibrated rule tau = 33.3.

| Judge | certificates | wrong (round-aware) | admitted candidates | poisoned | precision | recall |
|---|---:|---:|---:|---:|---:|---:|
| execution success | - | - | 878 | 241 | 0.726 | 1.000 |
| majority vote over host samples | 254 | 38 | 721 | 93 | 0.871 | 0.986 |
| panel, any two families agree at the stated instance | 245 | 38 | 610 | 45 | 0.926 | 0.887 |
| panel, all three families agree at the stated instance | 200 | 26 | 516 | 32 | 0.938 | 0.760 |
| AdmitOR, admission-time rule (the E1 library) | 170 | 29 | 413 | 30 | 0.927 | 0.601 |
| AdmitOR, calibrated tau = 33.3 | 138 | 22 | 344 | 22 | 0.936 | 0.505 |

Recall is over the 637 vault-correct trajectories. The calibrated gate admits a strict subset of
the base-unanimous problems with the same certified value on all 138; the 62 problems it
withholds carry 4 wrong and 58 correct base certificates (57 uninformative, 4 clique
reductions, 1 abstention; the stated-instance value is correct in all five of the latter).
Scripts: `panel_base_judges.py`, `candidate_crosstab.py`, `task3_additions.py`.

### Calibration table (manuscript Table 8)

Value-bearing three-family certificates on the 150 NANO-CO instances, per threshold:

| tau | n | false | p_hat | U at delta 0.05 | U at delta 0.0125 |
|---:|---:|---:|---:|---:|---:|
| 33.3 | 63 | 1 | 1.59% | 7.31% | 9.71% |
| 33.4 | 62 | 1 | 1.61% | 7.42% | 9.86% |
| 33.5 | 61 | 1 | 1.64% | 7.54% | 10.01% |
| 33.6 | 58 | 1 | 1.72% | 7.92% | 10.50% |

Counting the one three-family accept without a value at the stated instance gives 64 / 2
(3.12%, 9.51%, 12.10%) at 33.3. Of the 103 calibration accepts, 39 are two-family cliques
(score 22.x) and are excluded by the threshold; 8 of the 10 false cliques are among them.
Replay on the stream: 174 accepts, 170 value-bearing non-dev, 138 admitted, 22 wrong under
the round-aware scorer (26 under the host's equality rule; 21 in common).
Script: `e3_certificate_numbers.py`.

### Paired bootstrap (manuscript Section 4.2 and Appendix C)

Seed 42, 10,000 stratified resamples, script `corrected_bootstrap.py`. Macro: gate minus vote
+3.53 [+0.87, +6.68], on the sensitivity item set +3.49 [+0.78, +6.73]; gate minus ground truth
+4.46 [+2.34, +6.65], sensitivity +2.14 [+0.04, +4.29]; gate minus execution success
+1.84 [-0.27, +3.96]. Micro: gate minus vote +1.73 [-0.27, +3.73]; gate minus execution success
+1.27 [-0.73, +3.27].

### Retrieval (manuscript Appendix C, Table 10)

Selection-failure rows per arm: ground truth 95 (85 on OptiBench), majority vote 10,
execution success 10, AdmitOR 2. Distinct library files selected on OptiBench: 31 / 38 / 30 / 19
(ground truth / vote / execution success / AdmitOR), top-file share 20.3 / 32.2 / 39.5 / 44.6%.
Script: `retrieval_final.py`.

### Numeric-coverage check and two-extractor preliminary (manuscript Appendix B.1)

The numeric-coverage check (`numeric_coverage.py`) asks whether every base value of the
extracted specification is printed in the problem text. Applied after the fact to the stored
specifications it flags 9 of the 15 missing-data cases, 0 of the 5 truncated-precision cases,
0 of the 2 label errors, 0 of the 116 concordant admissions, and 0 of the 148 calibration
specifications.

The two-extractor preliminary (`two_extractor_run.py`, `two_extractor_agreement.py`; 88 calls,
the only model calls in this round) compares three extractor families on the 22 audited
disagreements and 22 concordant controls: raw parameter names disagree in 22/22 of both groups;
after aligning parameters by shape and value, 18/22 against 21/22 (Fisher p = 0.34); a full
three-way alignment succeeds in 5 of 44 cases. Outputs under `release/reviewer_round/09_*`.

### Feasibility-preserving resampling (manuscript Appendix C)

Re-drawing the 57 base-unanimous uninformative problems with draws rejected when no
base-solving candidate solves them (at most 10 attempts per draw, seed 20260916): 8 reach three
informative instances, all 8 accept with the base-unanimous value, 7 correct against the vault.
Script: `feasibility_resampling.py`.

### Restricted K4 (manuscript Appendix C)

Restricted to candidates that reached value comparison: chi-square 8.75, df 2, p = 0.013
(permutation p = 0.012); adding the infeasible column: 10.30, df 4, p = 0.036.
Script: `k4_restricted.py`.

### Stream provenance and disjointness

The 300-problem stream is the first 300 problems by index of the OptMATH training split; the
calibration set is a stratified sample of NANO-CO. No stream or calibration item matches any of
the 1,100 evaluation items exactly, after normalization, or as a near duplicate (5-gram Jaccard
at least 0.8); maximum Jaccard 0.2059 (stream) and 0.0201 (calibration). Hashes in
`release/reviewer_round/06_provenance.md`. Script: `disjointness_audit.py`.

## Model pins and the response-side audit

| Component | Pin | How pinned | Response-side record |
|---|---|---|---|
| Host backbone (OptSkills) | `deepseek-v3.2` | host configuration | 60,000 host calls in the run ledger: 58,575 `deepseek-v3.2`, 1,425 `deepseek-v3-2-251201` (a hosting provider's dated tag for the same December 2025 release), 0 other |
| Extractor | `deepseek-v3.2`, temperature 0, 8,192-token output limit | request-side | not recorded |
| Candidate arm A | `deepseek-v3.2` + Pyomo/HiGHS, direct prompting | request-side | not recorded |
| Candidate arm B | `gpt-5.4` + Pyomo/HiGHS, structured prompting | `ADMITOR_MODEL_B` at run time; code default aligned in `8fd0397` | not recorded |
| Candidate arm C | `claude-sonnet-4-6` + gurobipy, direct prompting | request-side | not recorded |

The extractor and candidate calls bypass the host transport and were never written to the run
ledger, so only their request-side pins can be stated. Of the 60,000 ledger records, 5,025 fall
in no runtime window and are reported as one unattributed bucket. A per-item join shows no
association between the dated tag and either selection failures or accuracy
(`release/reviewer_round/05b_serving_variant_join.md`).

## Host backbone availability

Re-running any arm that calls the host backbone requires an endpoint that serves
`deepseek-v3.2` under its own name. Observed: the relay used for the pilot returned
`deepseek-flash` for requests naming `deepseek-v3.2` on 2026-09-16; Tencent Cloud removed
V3.2 on 2026-07-16; Alibaba Bailian announced removal for 2026-10-10. The manuscript's numbers are recomputable without model calls from the git checkout plus the
two release assets (run records, host call ledger); the exceptions are the 88 extractor calls of
the two-extractor preliminary, whose outputs are shipped under
`release/reviewer_round/09_extractions/`, and the feasibility-resampling diagnostic, whose
outputs are shipped as recorded. Only new candidate generation needs the host backbone.

## Reproducing the paper's numbers

**Inputs.** `git` is this checkout. `run records` is the v1.1.0 release asset, published in four
parts that unpack into one directory, `admitor-v1.1.0-run-records/`, with the host's
`outputs/` layout; unpack all four next to the checkout, so that `<rr>` below is
`../admitor-v1.1.0-run-records`. `ledger` is `host_llm.scrubbed.jsonl` from the v1.0.0 release
asset. Every record was scrubbed with `release_tools/scrub_logs.py` (credentials and absolute
local paths only) and checked with `scripts/secret_sweep.py` and
`scripts/release_content_check.py`.

| Part | Contents | Files | Uncompressed | Zipped | sha256 |
|---|---|---:|---:|---:|---|
| `admitor-v1.1.0-run-records-core.zip` | `outputs/e1/arms`, `outputs/e1/collect`, `outputs/e1/gate_workorder.jsonl`, `outputs/e1/certify_runs` (specifications, candidate programs, verdicts), `outputs/e3/certify_runs`, `outputs/e3/e3_labels.jsonl`, every `runtime_logs/*.events.jsonl` | 2,330 | 849,470,251 | 93,940,328 | `ff5f80a5bc6a26ce037cbe0e34c7c03a108a81b571f79ceb902561d4bff176bb` |
| `admitor-v1.1.0-run-records-eval.zip` | `outputs/e1/eval/<arm>/<plate>/trajectories.jsonl`, four arms x five plates | 20 | 735,883,632 | 100,333,853 | `d72c2ad67195f6c0151c102da9748495cdd6adc40a689b3ac2affaeb2deaa5ba` |
| `admitor-v1.1.0-run-records-e0.zip` | `outputs/eval/<plate>/trajectories.jsonl`, the E0 host reproduction and the 17-item OptMATH recheck | 6 | 173,263,054 | 22,242,226 | `4510871a975a9943e541890ba9c900f48e9cdd14c47e05ca6dbfb302cc5269be` |
| `admitor-v1.1.0-run-records-cache.zip` | `outputs/e1/llm_cache_eval`, eval response cache | 40,208 | 162,549,387 | 71,862,628 | `f65e9541e6f4d209a59aae6e8b617103675d80e8a7b11934281961c17885127e` |

All commands run from the repository root in the pinned environment (see Installation). Scripts
without `--out` in the command write to `reanalysis/reviewer_round/` (gitignored); compare
against the shipped files under `release/`.

| Script | Inputs | Command | Output | Paper location |
|---|---|---|---|---|
| `e0_scorecard.py` | git + run records | `python scripts/e0_scorecard.py release/e0/scorecard.json --eval-root <rr>/outputs/eval` | stdout | Section 4.1, Appendix C Table 9 |
| `score_eval.py` | git + run records | `python scripts/score_eval.py <rr>/outputs/eval/optibench/trajectories.jsonl` (one plate per call; E1 arms under `<rr>/outputs/e1/eval/`) | stdout | Section 4.1, Appendix C Table 9 |
| `e1_relabel.py` | git + run records | `python scripts/e1_relabel.py --collect <rr>/outputs/e1/collect/trajectories.jsonl --arm vote --out arms/vote.jsonl` (`--arm gate --verdicts-dir artifacts/e1/certify_verdicts`; `--arm gt --labels datasets/train_set/optmath-train-300.jsonl`) | arm jsonl and summary | Section 4.2 (candidate counts 878 / 721 / 413), Table 2 |
| `e1_rebuild.py` | git + run records | `python scripts/e1_rebuild.py --relabeled <rr>/outputs/e1/arms/gate.jsonl --library libs/skill_library_gate --cluster-eps 0.05 --cluster-min-samples 1 --archetype-fusion-alpha 0.55 --agent-max-turns 12` (needs the host and the host backbone; the libraries used are in `artifacts/e1/libraries/`) | skill library | Section 4.2 (candidate counts 878 / 721 / 413), Table 2 |
| `e1_certify.py` | git + run records | `python scripts/e1_certify.py --work-order <rr>/outputs/e1/gate_workorder.jsonl --verdicts-dir verdicts --runs-dir certify_runs --m 5` (model calls; the resulting runs are in `<rr>/outputs/e1/certify_runs`) | verdicts, certification runs | Section 4.2 (candidate counts 878 / 721 / 413), Table 2 |
| `e3_calibrate.py` | git + run records | `python scripts/e3_calibrate.py fit --runs <rr>/outputs/e3/certify_runs --labels <rr>/outputs/e3/e3_labels.jsonl --alpha 0.05 --out calibration.json`; `python scripts/e3_calibrate.py replay --calibration artifacts/e3/calibration.json --e1-runs artifacts/e1/certify_runs --verdicts artifacts/e1/certify_verdicts --workorder <rr>/outputs/e1/gate_workorder.jsonl --vault datasets/vault/optmath-train-300-labels.jsonl --out e3_report.json` (add `--tau 33.4`, `33.5`, `33.6` for the threshold sweep) | `calibration.json`, `e3_report.json` | Section 4.3 (103 accepts, tau = 33.3, 138 admitted, 22 wrong; threshold sweep 15.9 / 16.5 / 16.0 / 14.7%) |
| `e3_certificate_numbers.py` | git + run records | `python scripts/e3_certificate_numbers.py --calib-runs <rr>/outputs/e3/certify_runs --calib-labels <rr>/outputs/e3/e3_labels.jsonl` | `02_calibration_table.md`/`.csv`, `admitted_ids_*.txt` | Section 4.3, Appendix C Table 8 |
| `k4_matrix.py` | git | `python scripts/k4_matrix.py --e1-runs artifacts/e1/certify_runs --out k4_matrix.json` | `k4_matrix.json` | Section 4.2 (chi-square 30.96), Appendix C Table 5 |
| `k4_restricted.py` | git | `python scripts/k4_restricted.py` | `08_k4_restricted.md` | Section 4.2 (chi-square 8.75), Appendix C |
| `panel_base_judges.py` | git + run records | `python scripts/panel_base_judges.py --collect <rr>/outputs/e1/collect/trajectories.jsonl` | `03_verdicts/`, `03_decomposition.md`, `03_decomposition_problem.csv`, `03_pairs.csv` | Section 4.2 Table 3, Appendix C "Judge ablation details" |
| `candidate_crosstab.py` | git + run records | `python scripts/candidate_crosstab.py --arms runsok=<rr>/outputs/e1/arms/runsok.jsonl --arms vote=<rr>/outputs/e1/arms/vote.jsonl --arms gate_asdeployed=<rr>/outputs/e1/arms/gate.jsonl --arms panel_base_2of3=<arm> --arms panel_base_3of3=<arm> --arms gate_tau=<arm>` (derived arms: `python scripts/e1_relabel.py --collect <rr>/outputs/e1/collect/trajectories.jsonl --arm gate --verdicts-dir reanalysis/reviewer_round/03_verdicts/<judge> --out <arm>`) | `03_decomposition_candidate.csv` | Section 4.2 Table 3, Appendix C "Judge ablation details" |
| `task3_additions.py` | git | `python scripts/task3_additions.py` | appends to `03_decomposition.md` | Section 4.2 Table 3, Appendix C "Judge ablation details" |
| `assemble_decomposition_report.py` | git + run records | `python scripts/assemble_decomposition_report.py --problem-md reanalysis/reviewer_round/03_decomposition.md --candidate-csv reanalysis/reviewer_round/03_decomposition_candidate.csv --out release/reviewer_round/03_decomposition.md` | `03_decomposition.md` | Section 4.2 Table 3, Appendix C "Judge ablation details" |
| `gate_arm_composition.py` | git + run records | `python scripts/gate_arm_composition.py --arm <rr>/outputs/e1/arms/gate.jsonl --build-summary artifacts/e1/libraries/skill_library_gate.build_summary.json` | `03_0_gate_arm_composition.md` | Section 4.2 (27 problems / 69 candidates / 8 poisoned, precision 0.936), Appendix C |
| `poison_provenance.py` | git + run records | `python scripts/poison_provenance.py --arm <rr>/outputs/e1/arms/gate.jsonl --runs artifacts/e1/certify_runs --vault datasets/vault/optmath-train-300-labels.jsonl --build-summary artifacts/e1/libraries/skill_library_gate.build_summary.json --admitted release/reviewer_round/admitted_ids_wild_138.txt --eval-root <rr>/outputs/e1/eval --out reanalysis/reviewer_round` | `03_0_poison_provenance.md` | Section 4.2 (27 problems / 69 candidates / 8 poisoned, precision 0.936), Appendix C |
| `corrected_bootstrap.py` | git + run records | `python scripts/corrected_bootstrap.py run --arm gt=<rr>/outputs/e1/eval/gt --arm vote=<rr>/outputs/e1/eval/vote --arm runsok=<rr>/outputs/e1/eval/runsok --arm gate=<rr>/outputs/e1/eval/gate --reps 10000 --seed 42 --score-eval scripts/score_eval.py --out release/reviewer_round` | stdout (`04_bootstrap_raw.txt`), `excluded_ids.txt` | Section 4.2 intervals, Appendix C |
| `format_bootstrap_report.py` | git | `python scripts/format_bootstrap_report.py` | `04_bootstrap.md` | Section 4.2 intervals, Appendix C |
| `retrieval_final.py` | git + run records | `python scripts/retrieval_final.py --eval-root <rr>/outputs/e1/eval` | `05_retrieval.md`, `05_retrieval.csv` | Section 4.2 (19 vs 30 files, 45%), Appendix C Table 10 |
| `retrieval_stats.py` | git + run records | `python scripts/retrieval_stats.py --eval-root <rr>/outputs/e1/eval` | `05b_retrieval_concentration.md` | Section 4.2 (19 vs 30 files, 45%), Appendix C Table 10 |
| `disjointness_audit.py` | git | `python scripts/disjointness_audit.py` | `06_provenance.md`, `06_similarity_pairs.md`, `06_max_similarity.csv` | Section 4 setup, Appendix C "Stream provenance and disjointness" |
| `numeric_coverage.py` | git + run records | `python scripts/numeric_coverage.py --runs <rr>/outputs/e1/certify_runs --workorder <rr>/outputs/e1/gate_workorder.jsonl --admitted release/reviewer_round/admitted_ids_wild_138.txt --k3 release/k3_attribution.csv --calib-runs <rr>/outputs/e3/certify_runs --calib-labels <rr>/outputs/e3/e3_labels.jsonl --out reanalysis/reviewer_round` | `07_coverage.md`, `07_coverage.csv` | Section 4.3 (9 / 15 etc.), Appendix B.1 |
| `two_extractor_run.py` | git + run records | `python scripts/two_extractor_run.py --family claude-sonnet-4-6 --workorder <rr>/outputs/e1/gate_workorder.jsonl` (and `--family gpt-5.4`; model calls, credentials from `OPTSKILL_BASE_URL` / `OPTSKILL_API_KEY`; outputs shipped under `release/reviewer_round/09_extractions/`) | `09_extractions/` | Section 4.3 (22/22, 21/22 vs 18/22), Appendix B.1 Table 4 |
| `two_extractor_agreement.py` | git + run records | `python scripts/two_extractor_agreement.py --runs <rr>/outputs/e1/certify_runs --workorder <rr>/outputs/e1/gate_workorder.jsonl` | `09_two_extractor.md`, `09_two_extractor.csv` | Section 4.3 (22/22, 21/22 vs 18/22), Appendix B.1 Table 4 |
| `feasibility_resampling.py` | git + run records | `python scripts/feasibility_resampling.py --runs <rr>/outputs/e1/certify_runs` (re-solves the candidate programs; outputs shipped as recorded) | `11_feasibility_resampling.md`, `.csv` | Section 4.2 (8 of 57), Appendix C |
| `runlog_phase_audit.py` | git + run records + ledger | `python scripts/runlog_phase_audit.py --runlog host_llm.scrubbed.jsonl --outputs <rr>/outputs` | `01_3_runlog_phases.md`, `.csv` | Appendix B pins paragraph |
| `serving_variant_join.py` | git + run records | `python scripts/serving_variant_join.py --eval-root <rr>/outputs/e1/eval --cache <rr>/outputs/e1/llm_cache_eval` | `05b_serving_variant_join.md`, `.csv` | Appendix B pins paragraph |
| `code_facts.py` | git + run records | `python scripts/code_facts.py --stream-runs <rr>/outputs/e1/certify_runs --calib-runs <rr>/outputs/e3/certify_runs --collect <rr>/outputs/e1/collect/trajectories.jsonl` | `01_code_facts_data.md` | Section 3 Step 2 and Step 3 (informative rule, tolerance), Appendix A remark (5) (173 of 298) |
| `review_packet.py` | git + run records | `python scripts/review_packet.py --report artifacts/e3/e3_report_v06.json --e1-runs <rr>/outputs/e1/certify_runs --workorder <rr>/outputs/e1/gate_workorder.jsonl --out packets` | `release/k3_packets/`, classes in `release/k3_attribution.csv` | Section 4.3 audit, `release/k3_attribution.csv` |
| `admitor_reanalysis.py` | git | `python scripts/admitor_reanalysis.py score --only-samples release/reviewer_round/admitted_ids_wild_138.txt` | stdout, `admitted_rows.json` | Section 4.3 (no continuous statistic reaches FDR <= 5% at >= 50% coverage) |

Release hygiene tools, not tied to a paper number: `scripts/secret_sweep.py`,
`scripts/release_content_check.py`, `release_tools/scrub_logs.py`,
`release_tools/make_manifest.py`.

## Limitations

The certificate is conditional on the extracted specification: all three
families consume one shared base spec, so consensus cannot detect an
extraction-layer error. The gate certifies cross-derivation agreement, not
intent. Purity is bought with coverage, since the gate abstains on part of the
stream. Transferability to other generation backbones is untested. See the
paper's Limitations section for the full discussion.

---

## Citation

```bibtex
@article{lian2026admitor,
  title   = {Admission Without Answers: Label-Free Certification and
             Experience Learning for LLM-Based Optimization Modeling},
  author  = {Lian, Junbo Jacob and Chen, Huiling and Qin, Hanzhang and
             Teo, Chung-Piaw},
  journal = {arXiv preprint arXiv:2608.15565},
  year    = {2026},
  eprint  = {2608.15565},
  archivePrefix = {arXiv},
  primaryClass  = {cs.AI},
  url     = {https://arxiv.org/abs/2608.15565}
}
```

## License and acknowledgements

MIT, see [`LICENSE`](LICENSE). Datasets under `datasets/` are third-party and
keep their own terms ([attribution](datasets/README.md)).

AdmitOR runs inside [**OptSkills**](https://github.com/fujiwaranoM0kou/OptSkills)
(Yang, Zhao, Qian, arXiv:2605.29829), and we thank its authors. No host source
is redistributed; our changes ship as unified diffs in [`patches/`](patches/).
