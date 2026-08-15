# Released artifacts

Every artifact, dataset and figure this repository ships, with its size, its
sha256, and the paper table or figure it backs.

Verify the whole table at any time:

```
python release_tools/make_manifest.py
```

Exit code 0 means every hash matched and nothing under `artifacts/` is missing
from this table.

## How the hashes work

Rows whose path ends in `/` stand for a whole collection rather than a single
file, so the table stays readable when one row covers several hundred files.
Their hash is an aggregate: the sha256 of the lines
`<relative path>\t<file sha256>\n` over every file in the collection, sorted
by relative path. It is reproducible on any platform and changes if any member
file is added, removed, renamed or edited.

Rows marked `(release asset)` are not committed. They are attached to the
GitHub Release for tag `v1.0.0` and are verified against
`release_assets/<filename>` when that file is present locally.

## Table

| Artifact | Size | sha256 | Backs |
|---|---|---|---|
| `artifacts/e1/certify_verdicts/` | 235.7 KB | `55be50047df54d837819390cee5af54987c1bc0462ebb3026617913a3fee1b98` | Table 2 (E1), Figure 3; the gate arm's admission decisions (300 files) |
| `artifacts/e1/certify_runs/` | 3.1 MB | `1faa1f67cf988353a843db376cd735cd6a459ac9d60f4a9ce006f8322ccdd01a` | Table 3 (K4), Table 4 (E3); clique geometry per certification (298 files) |
| `artifacts/e1/libraries/` | 13.8 MB | `4ef1a2f5a7e75c35e7e348fd97db5d76b2da16e1e9523c3a13a4f2d92bfdc819` | Table 2 (E1), Figure 3; the four evaluated skill libraries (543 files) |
| `artifacts/e3/calibration.json` | 10.4 KB | `3d8987eeeda2ef7e2a8e4bab105d2d670215e5cf09b671d21cec5004ce7b97ab` | Table 4 (E3); conformal threshold fit on NANO-CO |
| `artifacts/e3/e3_report.json` | 3.4 KB | `8584ac5dbded1f48e1ce0df31057345395103de414630b558466245b2e663f8e` | Table 4 (E3); replay report at the calibrated threshold |
| `artifacts/e3/e3_report_v06.json` | 5.3 KB | `4f50b0e7d9f8f96a2b3521913b951d770b6014c821b2104a061abb3224ee8879` | Table 4 (E3), Table 5, Figure 4; replay report, tightening rerun |
| `artifacts/e3/k4_matrix.json` | 653 B | `07749f8549676239d764b07326f13bb6694001e2ec83f90aad804ac029d84a9c` | Table 3 (K4); family-by-outcome contingency table |
| `artifacts/runlogs/host_llm.excerpt.jsonl` | 869.0 KB | `b7bb0207296ebcdad2ea1c788ae02ac9fb47f6f50075f2bbac1d7f6218284f08` | Appendix run ledger; schema sample |
| `datasets/benchmark/` | 1.4 MB | `2140f83a22cca99df3891f2e1e4e6f7772b6bf4095d2be494c7a825be9703262` | Table 2 (E1), Table 6 (E0); the five evaluation benchmarks (5 files) |
| `datasets/train_set/` | 2.9 MB | `b047a14747ed5dc769abbe4afb21cca168e5489c99161aec3a15953fe54a1ecc` | Table 2 (E1), Table 4 (E3); mining pool, blind variant, NANO-CO (3 files) |
| `datasets/vault/optmath-train-300-labels.jsonl` | 10.2 KB | `c05faaa8777e04cdd61eb29239c1b5b14e5d227d8ae46a7cf5c5881b3357c155` | Table 2 (E1) GT arm, Table 4 (E3) grading; sealed answer book |
| `figures/fig1_overview.png` | 100.8 KB | `96eecd96ac124bf58d76b3d78d1cb97b9fb7e2813affa19566c8d1f822cb7829` | Figure 1; value functions separate, purity ladder |
| `figures/fig2_pipeline.png` | 655.3 KB | `09275af98beeba68bc228cb45542b1923ad2717bd024f20810966901fface0a8` | Figure 2; the gate pipeline |
| `figures/fig3_quality.png` | 42.3 KB | `d1f4347e99eb40eab86fb1a8ceb526478c29a8d5b2a650f56488d0f04c69e3eb` | Figure 3; library size against downstream macro |
| `figures/fig4_e3_forensics.png` | 67.5 KB | `9516f9dee23ad1693a32e742d3064b0b46943dc4c19e650e9063b0cdbc78d7cc` | Figure 4; E3 forensics |
| `figures/fig1_overview.pdf` | 21.7 KB | `be739ba245711580f6e6469a80b93412048d0496febdbbddbd0f45ad7f101805` | Figure 1; vector source |
| `figures/fig2_pipeline.pdf` | 101.1 KB | `0507e5f6fcb8de5aaed212dbbc8c454f88304b18da29872506a07c137da11a97` | Figure 2; vector source |
| `figures/fig3_quality.pdf` | 15.0 KB | `d0a8ee91d21553d4561a692c4b93c968f50ab8439af5725351d4f9897612ef5c` | Figure 3; vector source |
| `figures/fig4_e3_forensics.pdf` | 17.5 KB | `19748d36b160d685ccf8136f5fb704f47aa8a6dc25c1a4da0fe31fdeca9bdda0` | Figure 4; vector source |
| `admitor-v1.0.0-runlogs.zip` | 3.3 MB | `272d52030e1ab229547e0762b7c25f954bcfc22e6e2586eeb82bcbec682a4c0f` | (release asset) Appendix run ledger; complete scrubbed per-call ledger, 93,909 records |

## Scrubbing

Every artifact above passed through `release_tools/scrub_logs.py` before
reaching this tree. That step redacted credential-bearing fields, rewrote
absolute local paths to a `<PATH>/...` placeholder, and masked the operator
identity. Originals were never modified. For the record, the scrubber rewrote
300 absolute paths in the compact verdicts, 78 in the full verdicts (local
temporary directories inside candidate crash messages), and in the run ledger
redacted 60,000 nested `prompt_tokens_details` objects and masked 93,909
operator fields. Token counts are deliberately preserved, since they are the
accounting the ledger exists to provide and cannot carry a credential.

The complete ledger was swept a second time, after extraction from the release
zip, by an implementation independent of the scrubber. Both agree: zero hits
across all 93,909 records.

## What is deliberately not here

- **E1 eval trajectories.** These carry the benchmark problem text verbatim
  and run to 828 MB, so they are not shipped in any form. K1 and K2 therefore
  require re-running the E1 eval phase; see the README's E1 section.
- **Human-review packets** (`outputs/e3/review/*.md`). These embed the full
  problem text of each disputed admission and are regenerated in one free step
  by `scripts/review_packet.py`.
- **Unused host datasets.** The OptSkills host also ships MIPLIB-NL (364 MB),
  NLCO (30 MB) and RetailOpt-190. No AdmitOR experiment touches them, so they
  are not copied. Everything the experiments do use is in `datasets/`.
- **The host's own source.** Only our patches to it are shipped, under
  `patches/`.
