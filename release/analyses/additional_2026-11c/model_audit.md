# Response-side model audit per run, second host

Calls sent to the relay (ledger records of kind `llm`) per evaluation run. (a) calls whose response-side name is neither `deepseek-v4-flash` nor `deepseek-v4-flash-0731`; (b) calls with reasoning tokens > 0. Limits fixed before the runs: at most 3% per run, and at most 2 percentage points between libraries on the same benchmark.

| Library | Benchmark | Calls | (a) other names | share | (b) reasoning > 0 | share | Response-side names |
|---|---|---:|---:|---:|---:|---:|---|
| `gate_asdeployed` | complexor | 85 | 0 | 0.00% | 0 | 0.00% | deepseek-v4-flash-0731 85 |
| `gate_asdeployed` | industryor | 544 | 0 | 0.00% | 0 | 0.00% | deepseek-v4-flash-0731 544 |
| `gate_asdeployed` | mamo_c | 1043 | 0 | 0.00% | 0 | 0.00% | deepseek-v4-flash-0731 1043 |
| `gate_asdeployed` | optmath | 884 | 0 | 0.00% | 0 | 0.00% | deepseek-v4-flash-0731 884 |
| `gate_asdeployed` | optibench | 2678 | 0 | 0.00% | 16 | 0.60% | deepseek-v4-flash-0731 2678 |
| `panel_base_3of3` | complexor | 83 | 0 | 0.00% | 0 | 0.00% | deepseek-v4-flash-0731 83 |
| `panel_base_3of3` | industryor | 547 | 0 | 0.00% | 5 | 0.91% | deepseek-v4-flash-0731 547 |
| `panel_base_3of3` | mamo_c | 1074 | 0 | 0.00% | 4 | 0.37% | deepseek-v4-flash-0731 1074 |
| `panel_base_3of3` | optmath | 974 | 0 | 0.00% | 0 | 0.00% | deepseek-v4-flash-0731 974 |
| `panel_base_3of3` | optibench | 2672 | 0 | 0.00% | 9 | 0.34% | deepseek-v4-flash-0731 2672 |
| `vote` | complexor | 87 | 0 | 0.00% | 1 | 1.15% | deepseek-v4-flash-0731 87 |
| `vote` | industryor | 558 | 0 | 0.00% | 3 | 0.54% | deepseek-v4-flash-0731 558 |
| `vote` | mamo_c | 1160 | 0 | 0.00% | 1 | 0.09% | deepseek-v4-flash-0731 1160 |
| `vote` | optmath | 974 | 0 | 0.00% | 0 | 0.00% | deepseek-v4-flash-0731 953, deepseek-v4-flash 21 |
| `vote` | optibench | 2873 | 0 | 0.00% | 21 | 0.73% | deepseek-v4-flash-0731 2669, deepseek-v4-flash 204 |

WITHIN TOLERANCE on every run
