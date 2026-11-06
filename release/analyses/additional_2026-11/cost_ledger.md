# Cost ledger of one certification (E1 stream, 298 certifications)

No model is called to produce this ledger. Cells are marked **measured** (from stored files or re-runs), **estimated** (from the code path, or from a re-serialization of stored text) or **not recorded**.

| Row | Count per problem | Total over the 298 problems | Median characters (request / response) | Median approx. tokens (request / response) | Median seconds |
|---|---|---|---|---|---|
| Extraction (model A, max_tokens 8192) | 1 (measured: spec.json) | 298 (measured) | 4,646 / 977 (request measured; response estimated, re-serialized `raw`) | not measured (tiktoken not installed) | not recorded per call |
| Generation A-direct (deepseek) | 1 (estimated: code path, one call per candidate) | 298 (estimated: code path); 298 stored programs (measured) | 4,836 / 2,004 (request measured; response measured as the stored program, a lower bound) | not measured (tiktoken not installed) | not recorded per call |
| Generation B-structured (gpt) | 1 (estimated: code path, one call per candidate) | 298 (estimated: code path); 296 stored programs (measured) | 5,021 / 2,262 (request measured; response measured as the stored program, a lower bound) | not measured (tiktoken not installed) | not recorded per call |
| Generation C-direct (claude) | 1 (estimated: code path, one call per candidate) | 298 (estimated: code path); 298 stored programs (measured) | 4,459 / 2,290 (request measured; response measured as the stored program, a lower bound) | not measured (tiktoken not installed) | not recorded per call |
| Repair rounds (regeneration after a failed probe) | not recorded (code path allows 0 to 3) | not recorded | not recorded | not recorded | not recorded |
| Probe solves at the stated instance (generation side) | 3 (estimated: code path, one per candidate before certification) | 894 (estimated) | - | - | not recorded |
| Solver runs at the stated instance (certification) | 3 (measured: stored statuses) | 894 (measured) | - | - | 0.95 per solve; 2.12 per problem (measured, re-run on 30 problems) |
| Solver runs at the five resampled instances | 15 (measured: stored statuses) | 4470 (measured) | - | - | 0.92 per solve; 10.25 per problem (measured, re-run on 30 problems) |
| Whole certification (elapsed_s, model calls and solver runs) | 1 | 298 verdicts (measured) | - | - | 59.5 median; 20,415.5 total (measured, stored elapsed_s) |

The majority-vote judge makes no additional model call, because it reads the host's three stored rollouts.

## Text volume per role (characters)

| Role | Median | Total | Status |
|---|---:|---:|---|
| Extraction request | 4,646 | 1,447,894 | measured |
| Extraction response (re-serialized `raw`) | 977 | 387,789 | estimated |
| Generation request A-direct | 4,836 | 1,520,989 | measured |
| Generation response A-direct (stored program) | 2,004 | 677,033 | measured, lower bound |
| Generation request B-structured | 5,021 | 1,576,119 | measured |
| Generation response B-structured (stored program) | 2,262 | 727,035 | measured, lower bound |
| Generation request C-direct | 4,459 | 1,408,643 | measured |
| Generation response C-direct (stored program) | 2,290 | 750,419 | measured, lower bound |

## Notes

- Stream: 298 certifications with a run folder; instances per verdict: {6: 298}.
- Two further work-order items (sample_108, sample_244) ended with an ERROR verdict after the extraction call (extractor output not parseable JSON); they made one extraction call each and are outside the 298.
- Programs missing from the run folders: B-structured 2 (the extracted program was empty, so scripts/e1_certify.py wrote no file; its six runs are stored as KeyError 'solve' crashes).
- Repair rounds: gen_candidate prints `[gen] <candidate>: base-instance probe failed` and regenerates once. The certification client in pipeline_one.live_run is not wrapped by runlog, scripts/e1_certify.py stores only the final program, and its stdout is not part of the run records, so the number of repair rounds is not recorded. Each repair round adds one model call and lengthens that call's request by the previous program and its status.
- Seconds per call of extraction and generation are not recorded; elapsed_s covers the whole certification.
- Solver timings are wall-clock seconds of make_candidate's subprocess (interpreter start, imports, model build and solve), re-measured on 2026-11-06 with timeout 60 s, sequentially.
- Timing sample (random.Random(20261106).sample(sorted(sample_ids), 30)): sample_121, sample_140, sample_161, sample_208, sample_101, sample_250, sample_288, sample_228, sample_103, sample_110, sample_151, sample_2, sample_225, sample_163, sample_179, sample_242, sample_98, sample_257, sample_10, sample_210, sample_64, sample_100, sample_135, sample_95, sample_62, sample_52, sample_69, sample_206, sample_192, sample_132.
- Re-runs: 540; per solve median 0.93 s (all), per problem median 12.40 s (all runs of the problem), total 374.5 s.
- Reproduction under the agreement rule: 0 of 540 re-runs differ from the stored objective value (listed in cost_ledger_solves.csv, column reproduces).
