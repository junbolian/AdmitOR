# Paired stratified bootstrap, second host

Output of `scripts/corrected_bootstrap.py run --arm gate_asdeployed=<PATH>/gate_asdeployed --arm panel_base_3of3=<PATH>/panel_base_3of3 --arm vote=<PATH>/vote --target gate_asdeployed --rule-arm gate_asdeployed --reps 10000 --seed 42 --score-eval scripts/score_eval.py`, unchanged except for local paths. Primary basis: the UNCORRECTED block (all 1,100 items). Sensitivity basis: the R3 block (the union of the `e1_eval_failure` rows of the three arms, 30 items, removed from all three). The Check lines and the R1 and R2 blocks are defined for the E1 arms and are not part of this result.

```
scorer: round_aware imported from scripts\score_eval.py
benchmarks aligned across arms: ['complexor', 'industryor', 'mamo', 'optibench', 'optmath']
  complexor    per-arm {'gate_asdeployed': 18, 'panel_base_3of3': 18, 'vote': 18}  common 18
  industryor   per-arm {'gate_asdeployed': 100, 'panel_base_3of3': 100, 'vote': 100}  common 100
  mamo         per-arm {'gate_asdeployed': 211, 'panel_base_3of3': 211, 'vote': 211}  common 211
  optibench    per-arm {'gate_asdeployed': 605, 'panel_base_3of3': 605, 'vote': 605}  common 605
  optmath      per-arm {'gate_asdeployed': 166, 'panel_base_3of3': 166, 'vote': 166}  common 166

RECONCILIATION: common counts must be 18 / 100 / 211 / 166 / 605. If not, the arms are not aligned and every interval below is void.

===== UNCORRECTED (as published)  (1100 items) =====
  gate_asdeployed macro  56.86   micro  61.27
  panel_base_3of3 macro  56.65   micro  60.09
  vote       macro  55.37   micro  59.55
  paired stratified bootstrap, 10000 resamples, seed 42
  gate_asdeployed - panel_base_3of3   macro +0.21  95% [-3.06, +3.00]  P(>0)=0.5607
                                      micro +1.18  95% [-0.82, +3.27]  P(>0)=0.8637
  gate_asdeployed - vote   macro +1.49  95% [-1.79, +4.21]  P(>0)=0.8359
                           micro +1.73  95% [-0.36, +3.82]  P(>0)=0.9391

  Check 1: the UNCORRECTED macro column must equal Table 2 exactly: gt 53.89, vote 54.82, runsok 56.51, gate 58.35.
  Check 2: gate-vote about +3.53 [+0.87, +6.75], gate-gt about +4.46 [+2.37, +6.64].
  Check 3: the R1 block must put gt macro at 55.95.
  Any of these failing means the row reader is wrong, not the paper. STOP and report.

===== CORRECTED, R1 flagged rows of the gate_asdeployed arm on optibench only  [PAPER BASIS]  (removed 3: {'optibench': 3})  (1097 items) =====
  gate_asdeployed macro  56.93   micro  61.44
  panel_base_3of3 macro  56.62   micro  59.98
  vote       macro  55.34   micro  59.43
  paired stratified bootstrap, 10000 resamples, seed 42
  gate_asdeployed - panel_base_3of3   macro +0.31  95% [-2.87, +3.12]  P(>0)=0.6066
                                      micro +1.46  95% [-0.55, +3.46]  P(>0)=0.9210
  gate_asdeployed - vote   macro +1.59  95% [-1.54, +4.30]  P(>0)=0.8580
                           micro +2.01  95% [-0.09, +4.10]  P(>0)=0.9699

===== CORRECTED, R2 flagged rows of the gate_asdeployed arm on every plate  (removed 8: {'industryor': 1, 'mamo': 2, 'optibench': 3, 'optmath': 2})  (1092 items) =====
  gate_asdeployed macro  57.25   micro  61.72
  panel_base_3of3 macro  56.80   micro  60.16
  vote       macro  55.63   micro  59.71
  paired stratified bootstrap, 10000 resamples, seed 42
  gate_asdeployed - panel_base_3of3   macro +0.45  95% [-2.81, +3.21]  P(>0)=0.6344
                                      micro +1.56  95% [-0.46, +3.48]  P(>0)=0.9294
  gate_asdeployed - vote   macro +1.62  95% [-1.61, +4.37]  P(>0)=0.8554
                           micro +2.01  95% [-0.09, +4.12]  P(>0)=0.9684

===== CORRECTED, R3 union of flagged rows across all arms, every plate  (removed 30: {'industryor': 2, 'mamo': 5, 'optibench': 18, 'optmath': 5})  (1070 items) =====
  gate_asdeployed macro  57.28   micro  61.78
  panel_base_3of3 macro  57.15   micro  60.47
  vote       macro  56.14   micro  60.65
  paired stratified bootstrap, 10000 resamples, seed 42
  gate_asdeployed - panel_base_3of3   macro +0.13  95% [-3.10, +2.89]  P(>0)=0.5505
                                      micro +1.31  95% [-0.75, +3.27]  P(>0)=0.8903
  gate_asdeployed - vote   macro +1.14  95% [-2.10, +3.89]  P(>0)=0.7785
                           micro +1.12  95% [-0.93, +3.18]  P(>0)=0.8414

HOW TO READ THIS
  R1 is the basis the paper already prints. It must reproduce the
  published sensitivity numbers exactly (ground truth 73.5 on
  OptiBench, 55.95 macro). If it does, R1 is the interval to print
  and R2/R3 stay internal: they exist so you know where the
  boundary is, not so the paper reports three of everything.
  Every rule removes the same items from EVERY arm, which is what
  keeps the bootstrap paired. The correction favours the baseline,
  so an interval that still excludes zero is the stronger claim.

wrote <PATH>/excluded_ids.txt
```
