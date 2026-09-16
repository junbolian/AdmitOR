# REPORT_RELEASE: GitHub release update for the reviewer round (v1.1.0)

Work order `CLAUDE_CODE_GITHUB_RELEASE_2026-09-16` with its amendments (T5 to T13 replaced; rulings on
scipy, environment, tool fixes, and the four "every number from a released script" items).
Status: **complete**. `main` and tag `v1.1.0` pushed, GitHub release created with four assets,
the anonymized mirror was withdrawn (section 8). This is the committed copy; the local copy kept by the authors lists the path samples of
section 5.3 unmasked.

## 1. Git state

```
git log --oneline -12 main
6df8202 release: v1.1.0 release notes
2be0999 release: bootstrap report regenerated with the fixed writer
4f41ca8 paper: regenerated Figure 1 and its generator
a64a235 README: reviewer-round results, pins and availability, script index with input provenance
65e5bf4 analysis: every manuscript number from a released script
5f049d5 release: K3 review packets and repo-relative attribution paths
2978e1f release tools: real-path shape in the scrubber, sk- word boundary in the sweep, asset mode in the content check
54f8580 release: bootstrap stdout regenerated with the path-scrubbed script
655838b analysis: reviewer-round scripts, path-scrubbed, docstring reproduce commands
e6f6641 release: reviewer-round outputs (September 2026)
7e32378 gitignore: reanalysis/ (local working outputs)
0cd3f30 docs: reviewer-round analyses, pins, provenance and release files

git tag: v1.0.0, v1.1.0 (annotated, on 6df8202)
origin/main = 6df8202, fast-forward from 8fd0397; no force push, no amend
reviewer-round-2026-09 = 6df8202 (pushed)
anon-mirror = deleted 2026-09-17 (was 2e72ec2; no anonymized mirror needed)
```

The report commit itself follows `6df8202` on `main`. All commits are authored by the repository
owner identity with no co-author line. `secret_sweep.py` ran before every commit with 0 hits.

## 2. INPUTS_IN_GIT (T1, updated for v1.1.0)

| Input | v1.0.0 | v1.1.0 |
|---|---|---|
| stream `certify_runs` verdict_full.json (298) | in git `artifacts/e1/certify_runs` | in git, and in the core part next to the specifications and programs |
| stream specifications (`spec.json`) and candidate programs (`*.py`) | neither | release asset (core) |
| compact stream verdicts (300) | in git `artifacts/e1/certify_verdicts` | in git |
| calibration `certify_runs` (148) and `e3_labels.jsonl` | neither | release asset (core) |
| `e3_report_v06.json`, `calibration.json`, `k4_matrix.json` | in git `artifacts/e3/` | in git |
| four libraries (130 / 145 / 163 / 101) and build summaries | in git `artifacts/e1/libraries/` | in git |
| relabeled arms, collect trajectories, gate work order | neither | release asset (core) |
| E1 eval trajectories (4 arms x 5 plates) | neither | release asset (eval) |
| E0 eval trajectories (5 plates + 17-item recheck) | neither | release asset (e0) |
| eval response cache `llm_cache_eval` | neither | release asset (cache) |
| runtime event streams `outputs/**/runtime_logs/*.events.jsonl` (95) | neither | release asset (core) |
| host run ledger (93,909 records, scrubbed) | release asset of v1.0.0 | unchanged, release asset of v1.0.0 |
| vault, datasets | in git | in git |
| K3 review packets (22) | neither | in git `release/k3_packets/` |

SCRIPTS_DIR = `scripts/`. T1 gate: libraries 130 / 145 / 163 / 101, 298 stream verdicts: PASS.
`00_inventory.md` counts at T1: certify_runs 298; libraries gt 130, vote 145, runsok 163, gate 101 (all PASS).

## 3. Files and changes per task

| Task | Commit | Files touched |
|---|---|---|
| T2 `.gitignore` | `7e32378` | `.gitignore` |
| T2 outputs | `e6f6641` | 1,613 files under `release/reviewer_round/`: 34 top-level outputs, `03_verdicts/` 1,490 files (5 judges x 298), `09_extractions/` 88 extractions + 2 call ledgers. Names unchanged, no mapping. `REPORT_reviewer_round_2026-09.md` = bundle `REPORT.md` (byte-identical to the local one). `00_inventory.md` not shipped (section 8). |
| T3 scripts | `655838b` | 21 scripts into `scripts/` + `requirements-analysis.txt` |
| T3 follow-up | `54f8580` | `release/reviewer_round/04_bootstrap_raw.txt` (4,598 B), regenerated with the path-scrubbed script, numbers identical |
| tool fixes | `2978e1f` | `release_tools/scrub_logs.py`, `scripts/secret_sweep.py`, `scripts/release_content_check.py` |
| T6 packets | `5f049d5` | `release/k3_packets/` (22 packets), `release/k3_attribution.csv` (path column only) |
| items 1 to 4 | `65e5bf4` | `scripts/two_extractor_agreement.py`, `release/reviewer_round/09_two_extractor.md` (2,654 B), `scripts/assemble_decomposition_report.py`, `scripts/admitor_reanalysis.py`, `scripts/e0_scorecard.py`, `release/e0/scorecard.json` |
| T7 README | `a64a235` | `README.md` |
| T8 figure | `4f41ca8` | `figures/fig1_overview.pdf` (Jacob's regenerated copy), `figures/fig1_overview.png` removed from git (restored 2026-09-17 from the v2.1 zip, the PNG exported with the same PDF), `paper/make_fig1.py`, `paper/README.md`, `artifacts/MANIFEST.md` (png row removed, pdf row refreshed by `make_manifest.py --write`; verify: 19 verified, 0 mismatched, 0 missing), `README.md` (overview image replaced by a link to the PDF, since the PNG is no longer in git) |
| T9 bootstrap report | `2be0999` | `scripts/format_bootstrap_report.py`, `release/reviewer_round/04_bootstrap.md` (2,298 B; the only diff hunk is the command block, lines 7 to 17) |
| T11 notes | `6df8202` | `release/reviewer_round/RELEASE_NOTES_v1.1.0.md` |
| T12 mirror (withdrawn, branch deleted) | `2e72ec2` | `README.md`, `LICENSE`, `release/reviewer_round/RELEASE_NOTES_v1.1.0.md`, `release/reviewer_round/REPORT_reviewer_round_2026-09.md` |

T3 script byte counts at `655838b`: candidate_crosstab 5,969; code_facts 13,029; corrected_bootstrap 20,408;
disjointness_audit 8,474; e3_certificate_numbers 14,390; feasibility_resampling 10,561; gate_arm_composition 9,581;
k4_restricted 5,580; numeric_coverage 10,577; panel_base_judges 15,257; poison_provenance 10,688;
release_content_check 6,648; retrieval_final 5,282; retrieval_stats 2,792; reviewer_inventory 10,657;
runlog_phase_audit 10,312; secret_sweep 4,042; serving_variant_join 10,286; task3_additions 6,937;
two_extractor_agreement 10,894; two_extractor_run 6,763. Code changes beyond the docstrings are path scrubbing
only (repo-relative argparse defaults, `../admitor-core` imports pointed at `scripts/` and the `admitor` package,
`two_extractor_run.py` credentials from the environment or `--env-file`), verified by an AST diff against the
private copies.

`git status --short` after every task: clean except, until T8, ` M figures/fig1_overview.pdf` and
` D figures/fig1_overview.png` (Jacob's, staged in T8 per the ruling). After T13: clean.

## 4. Reproduction (T4, T4b, T5 verification, items 1 to 4)

### 4.1 Interpreter history

- The reviewer-round outputs were first produced under base Anaconda Python 3.8.5 / scipy 1.10.1.
- T4 first ran in the local `admitor` env (Python 3.11.15), which had no scipy (p-values `nan`); re-run under base
  Anaconda 3.8.5 / scipy 1.10.1: all outputs byte-identical.
- T4b: scipy 1.17.1 was installed into `admitor` per the first ruling (the `admitor` env is left as it is); the
  E1 snapshot `envsnap_optskills_pre_e1.txt` shows E1 ran in `optskills` (Python 3.12.12, scipy 1.18.0).
- **Re-verified under `optskills`, Python 3.12.12, scipy 1.18.0**: all fifteen T4 scripts byte-identical to the
  shipped outputs (documented differences only). No p-value or bound differed at any precision.
- `conda env export -n optskills --no-builds` against `environment.yml`: python 3.12.12, numpy 2.4.4, scipy 1.18.0,
  pyomo 6.10.0, highspy 1.15.1, requests 2.34.2, openai 2.53.0 match; gurobipy 13.0.1 present (optional pin);
  **`pytest==8.4.2` is pinned but absent from `optskills`** (also absent from the E1 snapshot). `environment.yml`
  not edited.

### 4.2 Per-script table

"from asset" = run from a fresh clone of the release commit next to the unpacked four-part asset and the v1.0.0
ledger. Documented differences: row order of `03_decomposition_candidate.csv` follows the `--arms` order; the
bootstrap stdout differs only in the scorer-import and write-path lines.

| Script | Inputs | Result | Printed values |
|---|---|---|---|
| `task3_additions.py` | git | PASS, identical | 138 identical, 0 mismatch; divergences 140, 17, 288, 81, 93, base cert confirmed 5 of 5 |
| `disjointness_audit.py` | git | PASS, 3 files identical | stream 300 / 0 / 0 / 0 / 0.2059; calibration 245 / 0 / 0 / 0 / 0.0201 |
| `k4_restricted.py` | git | PASS, identical | 3x5 chi2 30.9623 df 8 p 0.000143; 3x2 8.7509 df 2 p 0.01258, FFH 0.0116; 3x3 10.3048 df 4 p 0.03559 |
| `e3_certificate_numbers.py` | asset | PASS, 4 files identical | 63 / 1 / 1.59% / 7.31% / 9.71%; 64 / 2 / 3.12% / 9.51% / 12.10%; 174 -> 170 -> 138; round-aware 22, equality 26, 21 in common |
| `panel_base_judges.py` | asset | PASS, 1,490 verdicts + 2 CSV identical | 254/38, 245/38, 200/26, 170/29, 138/22; Pair B 138 / 57 / 4 / 1 with 22 / 4 / 0 / 0 wrong; chain 0 |
| `candidate_crosstab.py` | asset | PASS | 878/241/0.726/1.000, 721/93/0.871/0.986, 610/45/0.926/0.887, 516/32/0.938/0.760, 413/30/0.927/0.601, 344/22/0.936/0.505; denominator 637 |
| `assemble_decomposition_report.py` | asset outputs | PASS, byte-identical to the shipped `03_decomposition.md` | section 3.3 now script output |
| `gate_arm_composition.py` | asset | PASS, identical | 121 / 27, 344 / 69, 22 / 8, 0.936 / 0.884; 99 clusters; 22 files with a two-family trajectory; 16 two-family-only |
| `poison_provenance.py` | asset | PASS, identical | 11 poison-bearing files, top file 9, 15 distinct problem ids |
| `corrected_bootstrap.py` | asset | PASS, numbers identical | macro gate-vote +3.53 [+0.87, +6.68], R1 +3.49 [+0.78, +6.73]; gate-gt +4.46 [+2.34, +6.65], R1 +2.14 [+0.04, +4.29]; gate-runsok +1.84 [-0.27, +3.96]; micro gate-vote +1.73 [-0.27, +3.73], gate-runsok +1.27 [-0.73, +3.27]; R1 gt macro 55.95; `excluded_ids.txt` identical |
| `format_bootstrap_report.py` | git | PASS | `04_bootstrap.md` differs from the recorded copy only inside the command block |
| `retrieval_final.py` | asset | PASS, identical | failures 95 (85) / 10 / 10 / 2; OptiBench 31/38/30/19, 20.3/32.2/39.5/44.6%; Mamo.C 20/22/19/18, 20.9/20.9/19.9/22.3%; 73.46 |
| `retrieval_stats.py` | asset | PASS, identical to both copies of `05b_retrieval_concentration.md` | |
| `numeric_coverage.py` | asset | PASS, identical | 9 / 15, 0 / 5, 0 / 2, 0 / 116, 0 / 148; Fisher p = 0.0000 |
| `two_extractor_agreement.py` | asset | PASS, CSV identical; md = shipped + 2 script-output lines | L1 22/22 vs 22/22; L2, L3 18/22 vs 21/22, p 0.3449; L4 22/22 vs 22/22; E=2 18/22 vs 20/22; truncated 1/5; three-way alignment 5 of 44; unmatched 244 / 50 / 764 (total 1,058); value conflicts 38 / 0 / 10 (total 48); agreeing 146 / 33 / 121 (total 300) |
| `runlog_phase_audit.py` | asset + ledger | PASS, identical | 60,000; 1,425 dated tag; 0 outside pin; 5,025 unattributed; 95 event streams |
| `serving_variant_join.py` | asset (scrubbed cache) | PASS, identical | unattributed 117, all_pinned 4,154, any_variant 129 |
| `code_facts.py` | asset | PASS, identical | 173 / 298, 629, 1,289 rel / 771 abs, 1,209 of 4,470 (27.0%), 60 all-dead; ERROR `sample_108`, `sample_244` |
| `e0_scorecard.py` (+ `score_eval.py`) | git + e0 part | PASS | IndustryOR 36.00 (+0.00), Mamo.Complex 62.09 (-1.42), OptiBench 75.87 (-1.15), ComplexOR 66.67 (-5.55), OptMATH-Bench 56.63 (-4.82); macro 62.04 / 59.45 / -2.59; recheck 3 / 17 |
| `admitor_reanalysis.py score` | git | PASS | 138 joined, 22 wrong; AUC n_fam 0.500, clique_size 0.500, informative 0.529, trace_range 0.450, **neg_tight 0.635**, sep 0.500, n_trace 0.529, deployed_score 0.529; no statistic reaches FDR <= 5% at >= 50% coverage |
| `e3_calibrate.py fit` | asset | PASS | `calibration.json` identical to git; 103 accepts, 93 true / 10 false |
| `e3_calibrate.py replay` | git + asset work order | PASS | report identical to `e3_report_v06.json` |
| `k4_matrix.py` | git | PASS | `k4_matrix.json` identical |
| `e1_relabel.py` (4 arms) | asset | PASS | all four summaries identical to the private run (gate: 151 eligible, 421 positive, 479 negative, 127 no consensus) |
| `review_packet.py` | git + asset | PASS for numbers | 21 of 22 packets byte-identical; `sample_98.md` in the shipped set lacks the unfilled classification checklist the generator writes (removed by hand from the original packet; no numbers) |
| `feasibility_resampling.py` | asset | NOT RUN | no verification mode; outputs shipped as recorded |
| `two_extractor_run.py`, `e1_certify.py`, `e1_rebuild.py` | asset + model calls | NOT RUN | model calls |

### 4.3 Threshold sweep (Section 4.3), `e3_calibrate.py replay --tau`

| tau | admitted | wrong (round-aware) | realized proportion |
|---:|---:|---:|---:|
| 33.3 | 138 | 22 | 15.9% |
| 33.4 | 133 | 22 | 16.5% |
| 33.5 | 119 | 19 | 16.0% |
| 33.6 | 109 | 16 | 14.7% |

The work order mapped the sweep to `admitor_reanalysis.py`; that script has no sweep. The numbers come from the
released `e3_calibrate.py replay --tau` on git inputs plus the work order in the core part; the README index says so.

## 5. Release assets (T5 and item 1)

### 5.1 Contents, byte counts, hashes

| File | Files | Uncompressed | Zipped | sha256 |
|---|---:|---:|---:|---|
| `admitor-v1.1.0-run-records-core.zip` | 2,330 | 849,470,251 | 93,940,328 | `ff5f80a5bc6a26ce037cbe0e34c7c03a108a81b571f79ceb902561d4bff176bb` |
| `admitor-v1.1.0-run-records-eval.zip` | 20 | 735,883,632 | 100,333,853 | `d72c2ad67195f6c0151c102da9748495cdd6adc40a689b3ac2affaeb2deaa5ba` |
| `admitor-v1.1.0-run-records-e0.zip` | 6 | 173,263,054 | 22,242,226 | `4510871a975a9943e541890ba9c900f48e9cdd14c47e05ca6dbfb302cc5269be` |
| `admitor-v1.1.0-run-records-cache.zip` | 40,208 | 162,549,387 | 71,862,628 | `f65e9541e6f4d209a59aae6e8b617103675d80e8a7b11934281961c17885127e` |
| v1.0.0 ledger `admitor-v1.0.0-runlogs.zip` (linked, not re-uploaded) | 1 | 38,407,848 | | `272d52030e1ab229547e0762b7c25f954bcfc22e6e2586eeb82bcbec682a4c0f` |

Layout: every part unzips into `admitor-v1.1.0-run-records/outputs/...` with forward-slash entry names (built
with Python `zipfile`, not `Compress-Archive`, whose Windows PowerShell 5.1 version writes backslash entry names).
Core: `e1/arms/*.jsonl`, `e1/collect/trajectories.jsonl`, `e1/gate_workorder.jsonl`, `e1/certify_runs/<sid>/`
(spec.json, A/B/C programs, verdict_full.json), `e3/certify_runs/` (148), `e3/e3_labels.jsonl`, 95
`runtime_logs/*.events.jsonl` in their original directories (not flattened). Source bytes before scrubbing: eval
739,316,133; core 857,123,028; cache 155,277,336; e0 174,968,944. Scrubbed records: 4,400 (eval), 586,870 (core),
40,208 (cache), 1,117 (e0); 0 unparseable lines dropped; 0 literal secrets masked; sensitive-key redactions only in
the cache (40,208, one `usage.prompt_tokens_details` object per document).

### 5.2 Tool fixes recorded (approved rulings and the standing approval)

| Fix | Tool | Planted test | Before | After |
|---|---|---|---|---|
| drive letter not after a letter or digit; `\n` `\t` `\r` after the colon are escapes | `scrub_logs.py` | E/D paths in eval, arms, collect, cache records rewritten; escaped text intact | 809,742 spans rewritten (eval 356,603; core 278,738; cache 174,401), of which 452,009 in eval+arms+collect contained no path | 144,611 |
| `\"` is an escape too | `scrub_logs.py` | single- and double-backslash E/D paths rewritten; `print(\"matrix Q:\")` intact | 1,457 false spans | 143,170 (0 non-path spans) |
| drive letter may follow an escape sequence (`...\nC:\Users\...`) | `scrub_logs.py` (standing approval) | C paths directly after `\n` and `\t` rewritten, all four record types | 10 private `Users`/`AppData` path matches left in staging | 143,192 spans; `Users\`, `Users\\`, `AppData`: 0 |
| `sk-` not after a letter or digit | `secret_sweep.py` | planted key at line start, after space, quote, `=` caught; `risk-weighted` not | 111 hits (risk-weighted 62, risk-adjusted 36, risk-location 12, risk-specific 1) | 0; no other pattern changed, no hit added |
| JSON path: separator followed by another escape is not a path; doubled separators accepted | `release_content_check.py` | E/D paths flagged in JSON (single and double) and text; escaped code not flagged | 125 false hits (and doubled-backslash JSON paths were not detected at all) | 0 |
| outside a git tree, `--allow-benchmark-text` | `release_content_check.py` | n/a | the check could not run on the asset | runs; the script never had a benchmark-text check, so the flag skips nothing and says so |
| `--help` | `e0_scorecard.py` | `--help` exits 0 without writing a file | wrote a template named `--help` | prints the docstring |

Gate (a), after each scrubber fix: the fixed scrubber reproduces the published v1.0.0 ledger asset byte for byte
(93,909 lines; with the operator mask the v1.0.0 run used, 93,909 literal masks) and all 298 git
`verdict_full.json` files; old and new scrubbers are byte-identical on both inputs.

Remaining case-insensitive matches of the operator's first name in the staging tree: 384, all non-identity
(372 "Jacobian" in solver logs, 12 in the OptiBench problem "Jacob has $3000 to invest", which is in git). The
e0 part: 108 "Jacobian", 3 of the same OptiBench text.

### 5.3 Gate (c): rewritten spans

143,192 spans rewritten by the final scrubber in the staging tree (eval 48,432; core 94,753; cache 7), of which
143,176 match a known private-path shape and 16 are private paths written with doubled backslashes (listed in full).

Ten samples (private prefixes masked in this copy: `<drive>` for the drive letter, `<user>` for the Windows user name):

```
<drive>:\\Users\\<user>\\AppData\\Local\\Temp\\tmpsjp9acbf.pyomo.lp
<drive>:\\Python\\Anaconda\\envs\\optskills\\Lib\\site-packages\\pyomo\\core\\base\\block.py\
<drive>:\\AdmitOR\\OptSkills-main\\utils\\run_code.py\
<drive>:\\AdmitOR\\admitor-infra
<drive>:\\Users\\<user>\\AppData\\Local\\Temp\\tmpsjp9acbf.pyomo.soln
<drive>:\\Python\\Anaconda\\envs\\optskills\\Lib\\site-packages\\pyomo\\core\\base\\block.py\
<drive>:\\AdmitOR\\OptSkills-main\\utils\\run_code.py\
<drive>:\\AdmitOR\\admitor-infra
<drive>:\Users\<user>\AppData\Local\Temp\tmpsjp9acbf.pyomo.lp
<drive>:\\Python\\Anaconda\\envs\\optskills\\Lib\\site-packages\\pyomo\\core\\base\\param.py\
```

The 16 doubled-backslash spans (8 distinct paths, each occurring twice):

```
<drive>:\\\\Python\\\\Anaconda\\\\envs\\\\optskills\\\\Lib\\\\site-packages\\\\ortools\\\\graph\\\\python\\\\min_cost_flow.cp312-win_amd64.pyd
<drive>:\\\\AdmitOR\\\\OptSkills-main
<drive>:\\\\Python\\\\Anaconda\\\\envs\\\\optskills\\\\python312.zip
<drive>:\\\\Python\\\\Anaconda\\\\envs\\\\optskills\\\\DLLs
<drive>:\\\\Python\\\\Anaconda\\\\envs\\\\optskills\\\\Lib
<drive>:\\\\Python\\\\Anaconda\\\\envs\\\\optskills
<drive>:\\\\Python\\\\Anaconda\\\\envs\\\\optskills\\\\Lib\\\\site-packages
<drive>:\\\\AdmitOR\\\\admitor-infra
```

### 5.4 Verification gate from the asset

Fresh clone of `reviewer-round-2026-09`, the four parts unzipped into `../run-records`, the v1.0.0 ledger unzipped
next to it: every script in section 4.2 marked "asset" reproduces as listed. No number differs.

## 6. T8/T10 sweep counts (final, before push)

| Tree | Sweep | Content check |
|---|---|---|
| repository working tree | 2,866 files, 0 hits | 2,859 text files, 1,643 under `release/`: pass |
| staging `admitor-v1.1.0-run-records/` | 42,564 files, 0 hits | 42,564 text files: pass (`--allow-benchmark-text`) |
| whole staging directory (including the verification clone and unpacked copies) | 88,000 files, 0 hits | |

## 7. Release

- Release: https://github.com/junbolian/AdmitOR/releases/tag/v1.1.0, created through the GitHub API (no `gh`),
  title "v1.1.0: reviewer-round analyses (September 2026)", body = `release/reviewer_round/RELEASE_NOTES_v1.1.0.md`.
- Four assets uploaded (sizes confirmed by the API); post-upload download check in section 7.1.
- Release notes: see `release/reviewer_round/RELEASE_NOTES_v1.1.0.md` (text as published). The required sentence
  is followed by the two exceptions stated in the README.

### 7.1 Post-release download check

- `admitor-v1.1.0-run-records-e0.zip`: downloaded from the public release URL, 22,242,226 bytes, sha256 matches.
- core, eval, cache: the API confirmed the uploaded sizes (93,940,328 / 100,333,853 / 71,862,628 bytes, equal to the local files whose sha256 is listed in section 5.1). A full re-download was stopped because the connection delivered about 38 KB/s (the 22 MB part took 580 s; the other three would take about two hours). To check them later: download each file from the release page and compare `Get-FileHash -Algorithm SHA256` with section 5.1.

## 8. Anonymized mirror (T12): withdrawn

The `anon-mirror` branch (`2e72ec2`) was created and pushed, then deleted from GitHub and locally on
2026-09-17 on Jacob's instruction: no anonymized mirror is needed, the repository is released openly under
the authors' names (it is public). `main` was never touched by the anonymization.

## 9. Not done, with reasons

| Item | Reason |
|---|---|
| `00_inventory.md` not shipped | regeneration would overwrite the Task 0 snapshot and list the private tool directory (ruling: stays unshipped); gate counts in section 2 |
| `feasibility_resampling.py` not re-verified | no verification mode; re-solving needs the candidate programs and solvers; outputs shipped as recorded and the README says so |
| `two_extractor_run.py`, `e1_certify.py`, `e1_rebuild.py` not re-run | model calls; their outputs are the released records |
| README T5.1 corrections | none of the six target statements occurred outside the replaced section, so no sentence was edited; the new sections carry the correct statements |
| T7.2 sentence replacement | applied literally: the last two sentences of the availability paragraph were replaced, which also removed the sentence about open weights as the fallback |
| `sample_98.md` packet | shipped as recorded; it differs from the generator output only by a removed checklist block |
| `pytest` pin | `environment.yml` pins `pytest==8.4.2`, absent from `optskills`; file not edited per ruling; the README's "14 passed" line predates this release and was not re-run in `optskills` |
| Figure generator environment | `paper/make_fig1.py` needs matplotlib, not in `environment.yml`; run with base Anaconda (matplotlib 3.7.5) to confirm seed 157 and base value 960; the PDF in git is Jacob's copy |

## 10. Remaining items for Jacob

1. Optionally re-download the core, eval and cache parts and compare their sha256 with section 5.1
   (section 7.1).
2. arXiv v2 after 2026-09-25.
3. Optional: rotate the relay key (it was pasted in chat during the reviewer round); decide whether
   `pytest` should stay pinned in `environment.yml`.
