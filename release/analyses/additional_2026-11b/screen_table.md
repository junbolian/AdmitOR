| Judge | Model calls | Solver runs | Certified problems | Wrong certificates | Admitted trajectories | Wrong admissions | Precision | Recall |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `screen_deepseek` | 1 + 1 | 6 | 169 | 34 | 402 | 34 | 0.9154 | 0.5777 |
| `screen_gpt` | 1 + 1 | 6 | 155 | 31 | 362 | 30 | 0.9171 | 0.5212 |
| `screen_claude` | 1 + 1 | 6 | 185 | 37 | 427 | 29 | 0.9321 | 0.6248 |
| `screenvar_deepseek` | 1 + 1 | 6 | 164 | 33 | 391 | 34 | 0.913 | 0.5604 |
| `screenvar_gpt` | 1 + 1 | 6 | 151 | 30 | 353 | 30 | 0.915 | 0.5071 |
| `screenvar_claude` | 1 + 1 | 6 | 180 | 37 | 413 | 29 | 0.9298 | 0.6028 |
| *reference rows* | | | | | | | | |
| `single_deepseek` | 1 + 1 | 1 | 240 | 40 | 594 | 46 | 0.9226 | 0.8603 |
| `single_gpt` | 1 + 1 | 1 | 226 | 35 | 559 | 40 | 0.9284 | 0.8148 |
| `single_claude` | 1 + 1 | 1 | 261 | 48 | 626 | 47 | 0.9249 | 0.9089 |
| `gate_asdeployed` | 1 + 3 | 18 | 170 | 29 | 413 | 30 | 0.9274 | 0.6013 |

Recall is over the 637 correct non-dev trajectories. Reference rows are copied from `release/analyses/additional_2026-11/judge_suite_table.md`.
