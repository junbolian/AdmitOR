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
| `figures/fig1_overview.png` | 149.7 KB | `3ee8cd895fafcd9270ead8286c38f3b4bf384e7c21095dc0f564f5317272cc2e` | Figure 1; value functions separate, admission precision |
| `figures/fig2_pipeline.png` | 246.8 KB | `9a2c57157b37d16b2f8dbca0346191154e2c14d9792d5c0b3fa1d37c3a0c9638` | Figure 2; the gate pipeline |
| `figures/fig3_quality.png` | 42.3 KB | `d1f4347e99eb40eab86fb1a8ceb526478c29a8d5b2a650f56488d0f04c69e3eb` | Figure 3; library size against downstream macro |
| `figures/fig4_e3_forensics.png` | 67.5 KB | `9516f9dee23ad1693a32e742d3064b0b46943dc4c19e650e9063b0cdbc78d7cc` | Figure 4; E3 forensics |
| `figures/fig1_overview.pdf` | 21.6 KB | `38127856ff4b27885e153429529d6e86a7a7bfa4e6bfc629fc3878fb2b49138a` | Figure 1; vector source |
| `figures/fig2_pipeline.pdf` | 95.5 KB | `e00c6bdb5d70032993594e347ab8c3c55bee9e3ec045c7bd5acbea97e3683a95` | Figure 2; vector source |
| `figures/fig3_quality.pdf` | 15.0 KB | `d0a8ee91d21553d4561a692c4b93c968f50ab8439af5725351d4f9897612ef5c` | Figure 3; vector source |
| `figures/fig4_e3_forensics.pdf` | 17.5 KB | `19748d36b160d685ccf8136f5fb704f47aa8a6dc25c1a4da0fe31fdeca9bdda0` | Figure 4; vector source |
| `admitor-v1.0.0-runlogs.zip` | 3.3 MB | `272d52030e1ab229547e0762b7c25f954bcfc22e6e2586eeb82bcbec682a4c0f` | (release asset) Appendix run ledger; complete scrubbed per-call ledger, 93,909 records |
| `artifacts/v2/README.md` | 10.8 KB | `ece77384fd6d0dc7017ffb147e05a757620c0bb44418ffd7cd3a19e35f7b87fd` | Version 2; description of the run records |
| `artifacts/v2/optmath_295/` | 9.8 MB | `f8c865391c6c3eefb145499dbba50cb8a4c6646a30c96bad6c0a110a5cc4399b` | Version 2, Tables 1 to 4, 7, 8; OptMATH-295 per-problem records |
| `artifacts/v2/optmath_200/` | 6.6 MB | `775aef94f67ca1936cd60839e4068c8190c7d94a5bffb13cb01a18aa99c4fd5e` | Version 2, Tables 1 to 3, 7, 8; OptMATH-200 per-problem records and draw |
| `artifacts/v2/nanoco_150/` | 5.6 MB | `64256d3f461e252d201889c39ccc94d4334cb3edb02174db5de799b4351632a0` | Version 2, Tables 1 to 3, 7; NANO-CO-150 per-problem records |
| `artifacts/v2/nanoco_95/` | 3.6 MB | `e996fa213c94d9cc5727dd4706c5e74435124b187c98212d4b1b5170d6b4db03` | Version 2, Tables 1 to 4, 7; NANO-CO-95 per-problem records |
| `artifacts/v2/optmath_295_k2/` | 12.2 MB | `52440ee7777a6a09c69ddfa9bc60d6db1524e8104e60482e75039e80ad9e2cf5` | Version 2, Tables 4, 7; OptMATH-295 with two programs per family |
| `artifacts/v2/nanoco_95_k2/` | 4.5 MB | `3a38d71464cda8345bd44e0a56f48d9d6585f65e9c0e5c60fc668af6e354c576` | Version 2, Tables 4, 7; NANO-CO-95 with two programs per family |
| `artifacts/v2/audit/` | 41.3 KB | `1ce12b2d5d3afdd81af624dbfd4e39e185dfebe4bca6a157016d6d6b5decf980` | Version 2, Table 2, Figures 1 and 2; audit of label misses |
| `artifacts/v2/downstream/` | 1.3 MB | `44fab09fdb7f0e2edd150cb33db60a0293b2ee3c9eacd61c9c59b4ba6f22f173` | Version 2, Tables 5, 6; per-item evaluation results, admitted attempts, libraries |
| `artifacts/v2/cost/` | 23.3 KB | `18755e2e319c6c6621164fd5d7ab848220a2469d56b3f9d35d438588128837df` | Version 2, Table 7; calls, tokens and verification time |
| `artifacts/v2/tables/` | 362.7 KB | `f3b4fb0935764d632fb6d24729229885373a9fa79868654e8e52c581bf209e09` | Version 2; every table, regenerated by scripts/paper_tables.py and scripts/rules_compare.py |
| `artifacts/v2/humanbench/` | 10.4 MB | `910d789a7a3ddc52de020760183dfaea4614404ebf5aaf673f60005eb16db4aa` | Version 2.1; runs on the published releases of IndustryOR and Mamo ComplexLP: per-problem records, tables h1 to h6, audit exports, expert-audit source and status |
| `artifacts/v2/optimind/` | 9.0 MB | `94d93e74a99cf0a17ff1d84b808ade168a990662292db9eb4b6c4abda2068f31` | Version 2.1; runs on the corrected releases of the OptiMind authors: per-problem records, tables o1 to o3, audit exports |
| `datasets/optimind_corrected/` | 481.3 KB | `ddcd28616c06eccb9c602b8ed6428f82411e682977db87f30adf9728e10082cc` | Version 2.1; corrected releases of IndustryOR and Mamo-Complex by the OptiMind authors, MIT license, with source |
| `figures/fig1_agreement_audit.png` | 101.3 KB | `9d2086155862442c82e1b2bd36dd2a431b6931a8a6efad4b7c30fac7195b1a24` | Version 2, Figure 1; agreement and audit |
| `figures/fig1_agreement_audit.pdf` | 31.8 KB | `b717fc01da718bbbf74ad6a6bc7ae8d41a78d4a68eed29267c54d1a95bb3fa07` | Version 2, Figure 1; vector source |
| `figures/fig2_verification_outcome.png` | 57.8 KB | `209ea567779241ddbd84ba3e67efa7bd5c0ef7637d6c719f6a41af77f3eac8d8` | Version 2, Figure 2; outcome of data verification |
| `figures/fig2_verification_outcome.pdf` | 19.2 KB | `e380c1ca0660861dd34eeb746e764085f896274bfd89cd27495ac16d824377ac` | Version 2, Figure 2; vector source |
| `figures/fig0_framework.png` | 73.1 KB | `3ca130e6baf5ddf92b9ca04ac1bad54827a83aec8a44f100f7b2b99fdbe0cb5e` | Version 2, README; framework figure of the certifier |
| `figures/fig0_framework.pdf` | 74.8 KB | `56e822683cc1f2164c057c67710689495f0e5842d3d4dba1634ec42fda323051` | Version 2, README; vector source |

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
