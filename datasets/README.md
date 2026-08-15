# Datasets

The problem sets the AdmitOR experiments run on, redistributed here so the
repository reproduces end to end without hunting for files.

**These are third-party benchmarks. We did not create them, we claim no
ownership of them, and each remains subject to its own upstream terms.** They
are included in the form in which the OptSkills host distributes them, which
is the exact form our experiments consumed. If you use any of them, cite the
original work, listed below. Only the files the AdmitOR experiments actually
touch are included; the host also ships MIPLIB-NL, NLCO and RetailOpt-190,
which no experiment here uses and which are not copied.

## Evaluation benchmarks

`datasets/benchmark/`, the five public benchmarks of the E1 downstream table.

| File | Records | Benchmark | Cite |
|---|---|---|---|
| `complexor.jsonl` | 18 | ComplexOR | Chain-of-Experts: When LLMs Meet Complex Operations Research Problems, ICLR 2024 |
| `industryor.jsonl` | 100 | IndustryOR | ORLM: Training Large Language Models for Optimization Modeling, 2024 |
| `mamo_complex_test.jsonl` | 211 | Mamo.Complex | Mamo: A Mathematical Modeling Benchmark with Solvers, 2024 |
| `optibench.jsonl` | 605 | OptiBench | OptiBench Meets ReSocratic: Measure and Improve LLMs for Optimization Modeling, 2024 |
| `optmath_bench.jsonl` | 166 | OptMATH-Bench | OptMATH: A Scalable Bidirectional Data Synthesis Framework for Optimization Modeling, 2025 |

## Mining and calibration sets

`datasets/train_set/`.

| File | Records | Role |
|---|---|---|
| `optmath-train-300.jsonl` | 300 | OptMATH-Train, the mining pool, with answers |
| `optmath-train-300-blind.jsonl` | 300 | the same pool with the answer column removed, which is what E1 actually mines |
| `nano-co.jsonl` | 245 | NANO-CO, the solver-verified set used for E3 conformal calibration |

## Sealed vault

`datasets/vault/optmath-train-300-labels.jsonl`, 300 records of `idx` and
`answer` only, no problem text.

This is the answer book, and the experimental protocol depends on when it is
opened. The gate never sees it. E1 mines the blind file, and the vault is
consulted only afterwards, to grade admissions in E3 and to build the GT
comparison arm. Treat it as write-once evidence, not as an input.

## Provenance and integrity

The two derived files, the blind mining file and the vault labels, are pure
deterministic functions of `optmath-train-300.jsonl`. Rebuild and verify them
against the sha256 fingerprints used in the paper:

```
python scripts/regen_derived.py --source datasets/train_set/optmath-train-300.jsonl
```

| File | sha256 |
|---|---|
| `optmath-train-300-blind.jsonl` | `48bb45321f977d5a883eb70979afa68733565cd417857ee0277e2617941e0a2b` |
| `optmath-train-300-labels.jsonl` | `c05faaa8777e04cdd61eb29239c1b5b14e5d227d8ae46a7cf5c5881b3357c155` |

Confirm the mining pool does not overlap any evaluation benchmark, which is a
hard gate before E0 runs:

```
python scripts/data_audit.py --root datasets
```

## A note on label quality

Two of these benchmarks contain labels our audit found to be wrong, and the
paper reports this rather than quietly correcting it. On ComplexOR an
instance labelled 200 has true optimum 250. On IndustryOR three labels carry
the sentinel value -99999. Per protocol, fixed before any judge ran, all main
results use the published labels as-is, so these errors count against us
everywhere, including against the gate.
