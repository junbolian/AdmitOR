# Provenance

This folder holds two solver-only analyses run on 2026-11-17. No model was called.

`scripts/redraw_suite.py` re-draws the five resampled instances of every stored certification run (298 stream problems, 148 calibration problems) under five samplers, re-solves the stored candidate programs, and applies the gate's decision rule unchanged: `orig` (the sampler of `admitor.consensus.sample_params`, seed 42), `screen1` (a draw is redrawn, up to ten times, unless one program that solved the stated instance solves it), `domain` (indicator structures kept at their stated values and non-negative parameters never drawn below zero), `domain_screen1`, and `domain_screen2` (a draw is accepted only when two programs solve it). Outputs: `stream/`, `calib/`.

`scripts/param_redraw.py` perturbs each parameter alone, twice, and keeps it when the programs that solved the stated instance still return a value (`pscreen_all`: all of them; `pscreen_two`: at least two). The resampled instances perturb the kept parameters jointly with the `domain` sampler. Outputs: `stream_param/`, `calib_param/`.

Gates passed in every run: variant `orig` reproduces every stored decision, clique, informative set and objective value; the stated-instance judges are identical across variants; and for the stream the candidate-level reconciliation of `scripts/candidate_crosstab.py` passed, with `orig` equal to the stored deployed gate (413 admitted, 30 wrong).

Inputs: the specifications and candidate programs of the certification runs, part of the release asset `admitor-v1.1.0-run-records-core.zip` (`outputs/e1/certify_runs`, `outputs/e3/certify_runs`).
