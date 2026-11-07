# Per-run audit, second host

Per evaluation run: submitted rows; no-answer items (no prediction after all 12 agent rounds); `run_code` calls and their nonzero exit codes (0xC06D007F = 3228369023, the numpy.linalg DLL crash of the earlier, discarded attempts; 1 = a Python exception in the agent's program; -1 = the 120 s timeout; 3221226505 = 0xC0000409, a native fail-fast); package-install attempts in the agent's programs (blocked or without effect under `PIP_NO_INDEX=1`); calls and response-side names from the run's ledger.

| Run | Rows | No-answer | run_code calls | 0xC06D007F | Other nonzero exit codes | pip install attempts | Calls | (a) other names | (b) reasoning > 0 | Response-side names |
|---|---:|---:|---:|---:|---|---:|---:|---:|---:|---|
| `serial_gate_asdeployed_complexor` | 18 | 0 (0.0%) | 28 | 0 | 1: 4 | 0 | 85 | 0 (0.00%) | 0 (0.00%) | deepseek-v4-flash-0731 85 |
| `serial_gate_asdeployed_industryor` | 100 | 2 (2.0%) | 246 | 0 | -1: 2, 1: 23 | 0 | 544 | 0 (0.00%) | 0 (0.00%) | deepseek-v4-flash-0731 544 |
| `serial_gate_asdeployed_mamo_c` | 211 | 0 (0.0%) | 405 | 0 | -1: 1, 1: 66 | 0 | 1043 | 0 (0.00%) | 0 (0.00%) | deepseek-v4-flash-0731 1043 |
| `serial_gate_asdeployed_optmath` | 166 | 1 (0.6%) | 376 | 0 | -1: 1, 1: 31 | 0 | 884 | 0 (0.00%) | 0 (0.00%) | deepseek-v4-flash-0731 884 |
| `serial_gate_asdeployed_optibench` | 605 | 1 (0.2%) | 839 | 0 | -1: 5, 1: 45, 3221226505: 1 | 0 | 2678 | 0 (0.00%) | 16 (0.60%) | deepseek-v4-flash-0731 2678 |
| `serial_panel_base_3of3_complexor` | 18 | 0 (0.0%) | 29 | 0 | 1: 2 | 0 | 83 | 0 (0.00%) | 0 (0.00%) | deepseek-v4-flash-0731 83 |
| `serial_panel_base_3of3_industryor` | 100 | 0 (0.0%) | 235 | 0 | -1: 2, 1: 20 | 0 | 547 | 0 (0.00%) | 5 (0.91%) | deepseek-v4-flash-0731 547 |
| `serial_panel_base_3of3_mamo_c` | 211 | 0 (0.0%) | 434 | 0 | 1: 58 | 0 | 1074 | 0 (0.00%) | 4 (0.37%) | deepseek-v4-flash-0731 1074 |
| `serial_panel_base_3of3_optmath` | 166 | 2 (1.2%) | 461 | 0 | -1: 2, 1: 53 | 0 | 974 | 0 (0.00%) | 0 (0.00%) | deepseek-v4-flash-0731 974 |
| `serial_panel_base_3of3_optibench` | 605 | 0 (0.0%) | 839 | 0 | -1: 4, 1: 58 | 0 | 2672 | 0 (0.00%) | 9 (0.34%) | deepseek-v4-flash-0731 2672 |
| `serial_vote_complexor` | 18 | 0 (0.0%) | 32 | 0 | 1: 2 | 0 | 87 | 0 (0.00%) | 1 (1.15%) | deepseek-v4-flash-0731 87 |
| `serial_vote_industryor` | 100 | 0 (0.0%) | 252 | 0 | -1: 1, 1: 18, 3221226505: 1 | 1 | 558 | 0 (0.00%) | 3 (0.54%) | deepseek-v4-flash-0731 558 |
| `serial_vote_mamo_c` | 211 | 0 (0.0%) | 521 | 0 | 1: 73 | 0 | 1160 | 0 (0.00%) | 1 (0.09%) | deepseek-v4-flash-0731 1160 |
| `serial_vote_optmath` | 166 | 3 (1.8%) | 463 | 0 | 1: 53 | 1 | 974 | 0 (0.00%) | 0 (0.00%) | deepseek-v4-flash-0731 953, deepseek-v4-flash 21 |
| `serial_vote_optibench` | 605 | 1 (0.2%) | 876 | 0 | -1: 2, 1: 43, 3221226505: 1 | 1 | 2873 | 0 (0.00%) | 21 (0.73%) | deepseek-v4-flash-0731 2669, deepseek-v4-flash 204 |
