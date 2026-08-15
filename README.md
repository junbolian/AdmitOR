<div align="center">

# AdmitOR

### Admission Without Answers<br>Label-Free Certification and Experience Learning for LLM-Based Optimization Modeling

**Junbo Jacob Lian** &nbsp;·&nbsp; **Huiling Chen** &nbsp;·&nbsp; **Hanzhang Qin** &nbsp;·&nbsp; **Chung-Piaw Teo**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![arXiv](https://img.shields.io/badge/arXiv-forthcoming-b31b1b.svg)
[![Release](https://img.shields.io/badge/release-v1.0.0-2ea44f.svg)](https://github.com/junbolian/AdmitOR/releases/tag/v1.0.0)
[![Tests](https://img.shields.io/badge/tests-14%20passing%20offline-2ea44f.svg)](#installation)
[![Artifacts](https://img.shields.io/badge/artifacts-MANIFEST-informational.svg)](artifacts/MANIFEST.md)
[![Host](https://img.shields.io/badge/host-OptSkills-181717.svg?logo=github)](https://github.com/fujiwaranoM0kou/OptSkills)

**Certify an optimization model's answer without ever seeing an answer key.**

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
  journal = {arXiv preprint arXiv:XXXX.XXXXX},
  year    = {2026}
}
```

## License and acknowledgements

MIT, see [`LICENSE`](LICENSE). Datasets under `datasets/` are third-party and
keep their own terms ([attribution](datasets/README.md)).

AdmitOR runs inside [**OptSkills**](https://github.com/fujiwaranoM0kou/OptSkills)
(Yang, Zhao, Qian, arXiv:2605.29829), and we thank its authors. No host source
is redistributed; our changes ship as unified diffs in [`patches/`](patches/).
