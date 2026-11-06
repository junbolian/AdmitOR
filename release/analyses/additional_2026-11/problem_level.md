| Judge | Model calls | Solver runs | Certified | Wrong | False % | Gate |
|---|---|---:|---:|---:|---:|---|
| `panel_base_2of3` | 1 + 3 | 3 | 245 | 38 | 15.5 | PASS |
| `panel_base_3of3` | 1 + 3 | 3 | 200 | 26 | 13.0 | PASS |
| `gate_asdeployed` | 1 + 3 | 18 | 170 | 29 | 17.1 | PASS |
| `gate_tau` | 1 + 3 | 18 | 138 | 22 | 15.9 | PASS |
| `single_deepseek` | 1 + 1 | 1 | 240 | 40 | 16.7 | PASS |
| `single_gpt` | 1 + 1 | 1 | 226 | 35 | 15.5 | PASS |
| `single_claude` | 1 + 1 | 1 | 261 | 48 | 18.4 | PASS |
| `pair0_deepseek_gpt` | 1 + 2 | 2 | 205 | 29 | 14.1 | PASS |
| `pair0_deepseek_claude` | 1 + 2 | 2 | 228 | 33 | 14.5 | PASS |
| `pair0_gpt_claude` | 1 + 2 | 2 | 212 | 28 | 13.2 | PASS |
| `pairR_deepseek_gpt` | 1 + 2 | 12 | 140 | 23 | 16.4 | PASS |
| `pairR_deepseek_claude` | 1 + 2 | 12 | 158 | 26 | 16.5 | PASS |
| `pairR_gpt_claude` | 1 + 2 | 12 | 148 | 24 | 16.2 | PASS |
| `gate_m2` | 1 + 3 | 9 | 152 | 25 | 16.4 | PASS |
| `gate_m3` | 1 + 3 | 12 | 164 | 29 | 17.7 | PASS |
| `gate_m4` | 1 + 3 | 15 | 170 | 29 | 17.1 | PASS |
| `gate3_m2` | 1 + 3 | 9 | 123 | 18 | 14.6 | PASS |
| `gate3_m3` | 1 + 3 | 12 | 133 | 22 | 16.5 | PASS |
| `gate3_m4` | 1 + 3 | 15 | 138 | 22 | 15.9 | PASS |
| `gate_mi1` | 1 + 3 | 18 | 238 | 35 | 14.7 | PASS |
| `gate_mi2` | 1 + 3 | 18 | 178 | 30 | 16.9 | PASS |
| `gate3_mi1` | 1 + 3 | 18 | 194 | 26 | 13.4 | PASS |
| `gate3_mi2` | 1 + 3 | 18 | 144 | 23 | 16.0 | PASS |
| `base2_kept` | 1 + 3 | 18 | 170 | 29 | 17.1 | PASS |
| `base2_lost_uninformative` | 1 + 3 | 18 | 68 | 6 | 8.8 | PASS |
| `base2_lost_failure` | 1 + 3 | 18 | 1 | 0 | 0.0 | PASS |
| `base2_lost_divergence` | 1 + 3 | 18 | 6 | 3 | 50.0 | PASS |
| `base3_kept` | 1 + 3 | 18 | 138 | 22 | 15.9 | PASS |
| `base3_lost_uninformative` | 1 + 3 | 18 | 57 | 4 | 7.0 | PASS |
| `base3_lost_shrink` | 1 + 3 | 18 | 4 | 0 | 0.0 | PASS |
| `base3_lost_divergence` | 1 + 3 | 18 | 1 | 0 | 0.0 | PASS |

Stream facts: {"theta0_values_count_nondev": {"0": 26, "1": 19, "2": 36, "3": 212}, "theta0_statuses_when_no_value": {"crash": 53, "infeasible": 5, "infeasible_or_unbounded": 15, "status_4": 3, "failed": 1, "missing transport costs": 1}, "certified_value_constant_vs_varies": {"as_deployed": [4, 166], "three_family": [2, 136]}, "base2_divergence_cases": [{"sample_id": "sample_20", "base_value": 6.0, "label": "6.0", "base_value_correct": true}, {"sample_id": "sample_28", "base_value": 3.0, "label": "4.0", "base_value_correct": false}, {"sample_id": "sample_93", "base_value": 7.0, "label": "7.0", "base_value_correct": true}, {"sample_id": "sample_147", "base_value": 2927.0, "label": "3140.0", "base_value_correct": false}, {"sample_id": "sample_165", "base_value": 4.0, "label": "4.0", "base_value_correct": true}, {"sample_id": "sample_267", "base_value": 3775.0, "label": "3898.0", "base_value_correct": false}]}
