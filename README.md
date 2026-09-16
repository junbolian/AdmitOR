<div align="center">

# AdmitOR

### Admission Without Answers<br>Label-Free Certification and Experience Learning for LLM-Based Optimization Modeling

**Junbo Jacob Lian** &nbsp;·&nbsp; **Huiling Chen** &nbsp;·&nbsp; **Hanzhang Qin** &nbsp;·&nbsp; **Chung-Piaw Teo**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![arXiv](https://img.shields.io/badge/arXiv-2608.15565-b31b1b.svg)](https://arxiv.org/abs/2608.15565)
[![Release](https://img.shields.io/badge/release-v1.0.0-2ea44f.svg)](https://github.com/junbolian/AdmitOR/releases/tag/v1.0.0)
[![Tests](https://img.shields.io/badge/tests-14%20passing%20offline-2ea44f.svg)](#installation)
[![Artifacts](https://img.shields.io/badge/artifacts-MANIFEST-informational.svg)](artifacts/MANIFEST.md)
[![Host](https://img.shields.io/badge/host-OptSkills-181717.svg?logo=github)](https://github.com/fujiwaranoM0kou/OptSkills)

**Certify an optimization model's answer without ever seeing an answer key.**

[**Paper**](https://arxiv.org/abs/2608.15565) &nbsp;·&nbsp; [**Release v1.0.0**](https://github.com/junbolian/AdmitOR/releases/tag/v1.0.0) &nbsp;·&nbsp; [**Artifacts**](artifacts/MANIFEST.md)

</div>

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
**[+0.87, +6.75]**; gate minus GT is **+4.46pp**, 95% CI **[+2.37, +6.64]**.

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
│   └── shared        score_eval · paired_bootstrap · regen_derived · runlog
├── datasets/         benchmark/ · train_set/ · vault/   (third-party, see datasets/README.md)
├── artifacts/        verdicts · skill libraries · E3 reports · run-ledger excerpt
├── patches/          OptSkills host patches as unified diffs
├── release_tools/    scrub_logs.py · make_manifest.py
├── tests/            offline suite, no API key needed
└── figures/          paper figures (PNG + PDF source)
```

---

## Installation

```bash
conda env create -f environment.yml
conda activate admitor
pytest -q          # 14 passed, fully offline, no API key
```

Versions are pinned to the environment the experiments ran on (Python 3.12.12,
Pyomo 6.10.0, HiGHS 1.15.1). The code runs on Python 3.8+.

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
confounded. Eval trajectories embed benchmark problem text and run to hundreds
of megabytes, so they are not shipped; the last step needs your own eval run.

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
rather than committed, since it grows with every campaign. Everything released
passed through `release_tools/scrub_logs.py`, which is committed so the
scrubbing is auditable.

---

## Reviewer-round analyses (September 2026)

Re-analysis of the released artifacts for the ICLR 2027 submission. Every
number is recomputed from the stored logs, libraries and caches with no model
calls, except the two-extractor preliminary.

### Pins, as run

| Component | Pin |
|---|---|
| Host backbone | `deepseek-v3.2`, temperature 0, non-thinking |
| Extractor | arm A, `deepseek-v3.2`, temperature 0, max_tokens 8192 |
| Candidate arm A | `deepseek-v3.2`, direct, Pyomo + HiGHS, temperature 0, max_tokens 3000 |
| Candidate arm B | `gpt-5.4`, structured, Pyomo + HiGHS, pinned through `ADMITOR_MODEL_B` |
| Candidate arm C | `claude-sonnet-4-6`, direct, gurobipy, pinned through `ADMITOR_MODEL_C` |

Response-side model audit covers host calls only: 60,000 ledger records,
**58,575 `deepseek-v3.2`** and **1,425 `deepseek-v3-2-251201`** (a hosting
provider identifier for the 2025-12-01 release of the same model), none
outside those two. Response-side model strings were **not** logged for the
extractor or the three candidate arms; those carry request-side pins only.

### Host backbone availability

`deepseek-v3.2` is being withdrawn by the hosting providers used here. Tencent
Cloud removed it on 2026-07-16. On 2026-09-16 the relay used for the original
runs accepted the name but served `deepseek-flash` in response. Alibaba Cloud
Bailian has announced removal for 2026-10-10. Open weights remain at
huggingface.co/deepseek-ai/DeepSeek-V3.2.

This does not affect reproducibility: every printed number is recomputable
from the released logs, libraries and caches without model calls.

### Two protocol facts

- An instance counts as **informative when at least two candidates** return a
  finite optimal value (`admitor/consensus.py`), not three.
- The agreement test is `abs(a - b) <= tol_rel * max(1.0, abs(a), abs(b))`
  with `tol_rel = 1e-4`, applied to every informative instance including the
  stated one.

### Two admission rules

The E1 skill library was built under **`gate_asdeployed`** (decision ACCEPT
with a base value, no score threshold), which is the rule behind the
downstream accuracy table. The calibrated threshold **`gate_tau`** (deployed
score >= 33.3) was fitted afterwards on NANO-CO and is used only for the
false-discovery analysis. They are different rules and are reported
separately.

Counterfactual, applying `gate_tau` to the E1 arm: 27 of 148 eligible problems
and 69 of 413 admitted candidates would be removed, carrying 8 of the 30
poison admissions; 16 of the 99 built library files would disappear entirely
and 6 more would be thinned; candidate-level precision would rise from 0.927
to 0.936.

### Stream provenance

The 300-problem stream is the first 300 by index of the host's OptMATH
training split (`datasets/train_set/optmath-train-300.jsonl`, indices
contiguous). The blind file used for mining is that file with the answer
column removed; the vault is its index and answer projection. Both regenerate
byte-identically via `scripts/regen_derived.py`. Disjointness against all
1,100 evaluation items: **zero exact matches, zero after normalization, zero
at 5-gram Jaccard >= 0.8**; maximum Jaccard 0.2059 for the stream and 0.0201
for the calibration set. Hashes and details in `release/06_provenance.md`.

### Shipped files

| File | Contents |
|---|---|
| `release/k3_attribution.csv` | per-case class for the 22 disagreements; authoritative, since the review packet template predates class (d) |
| `release/admitted_ids_wild_138.txt` | the 138 problems admitted at the calibrated threshold |
| `release/admitted_ids_calibration.txt` | the calibration accepts at that threshold |
| `release/02_calibration_table.csv` | per-threshold false-discovery table, both units, both confidence levels |
| `release/05b_retrieval_concentration.md` | distinct files retrieved and top-file share, per arm and plate |
| `release/06_provenance.md` | stream and calibration provenance, hashes, disjointness |

### Known deviations

- The embedding model is DashScope `text-embedding-v4`, which the paper names
  differently.
- Solver builds are the pinned versions in `environment.yml`; HiGHS and
  gurobipy minor versions may differ from a fresh install.
- The relay rehosted `deepseek-v3.2`; see the availability note above.
- 5,025 of the 60,000 host ledger records cannot be attributed to a phase: the
  library rebuild writes no runtime event stream and no cache entry survives
  in that window. All 5,025 are inside the pinned model set.

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
