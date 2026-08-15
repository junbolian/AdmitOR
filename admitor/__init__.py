"""AdmitOR: label-free certification for LLM-based optimization modeling.

The package holds the certification engine itself. Everything that is an
experiment driver rather than part of the gate lives under ``scripts/``.

Modules
    consensus     L3 resampled cross-family value-function consensus, the
                  decision rule that turns candidate agreement into an
                  ACCEPT / ABSTAIN / UNINFORMATIVE verdict.
    ir_extract    Extraction prompt, the parameter-domain specification
                  schema, and ``validate_spec``, the semantic guardrails
                  that repair an unusable sampling domain before it can
                  produce a meaningless verdict.
    generate      Candidate generation prompts and the subprocess sandbox
                  each candidate's ``solve(params)`` runs in.
    pipeline_one  Single-problem end-to-end entry point (``live_run`` for
                  the three real model families, ``mock_run`` offline).
"""

__version__ = "1.0.0"

__all__ = ["consensus", "generate", "ir_extract", "pipeline_one"]
