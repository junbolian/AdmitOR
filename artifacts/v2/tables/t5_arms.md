Table 5. Admission of trajectories by arm (rows sample_6..300). A trajectory is an attempt of an eligible row; admitted when the host's equality rule (label_oracle.host_label: success and equal after rounding to two decimals half up, else within 0.005) holds against the arm's relabeled answer; wrong when it does not hold against the vault label. Recall = admitted and correct / all vault-correct trajectories (669 under the host rule). eligible_problems = problems with at least one admitted attempt. Binomial standard errors. The last five columns score the same admitted trajectories against the vault label with `round_aware` of scripts/score_eval.py instead (vault-correct trajectories: 688).

| arm | admitted | wrong | precision | precision_se | admitted_correct | recall | recall_se | recall_denominator | eligible_problems | wrong_round_aware | precision_round_aware | admitted_correct_round_aware | recall_round_aware | recall_denominator_round_aware |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| runsok | 862 | 193 | 0.7761 | 0.0142 | 669 | 1.0000 | 0.0000 | 669 | 295 | 174 | 0.7981 | 688 | 1.0000 | 688 |
| vote | 758 | 94 | 0.8760 | 0.0120 | 664 | 0.9925 | 0.0033 | 669 | 264 | 74 | 0.9024 | 684 | 0.9942 | 688 |
| gt | 669 | 0 | 1.0000 | 0.0000 | 669 | 1.0000 | 0.0000 | 669 | 233 | 8 | 0.9880 | 661 | 0.9608 | 688 |
| gate | 685 | 67 | 0.9022 | 0.0113 | 618 | 0.9238 | 0.0103 | 669 | 239 | 50 | 0.9270 | 635 | 0.9230 | 688 |
| gate_tau | 601 | 51 | 0.9151 | 0.0114 | 550 | 0.8221 | 0.0148 | 669 | 208 | 39 | 0.9351 | 562 | 0.8169 | 688 |
| gate_3fam | 609 | 51 | 0.9163 | 0.0112 | 558 | 0.8341 | 0.0144 | 669 | 211 | 39 | 0.9360 | 570 | 0.8285 | 688 |
| panel_base_2of3 | 712 | 67 | 0.9059 | 0.0109 | 645 | 0.9641 | 0.0072 | 669 | 248 | 50 | 0.9298 | 662 | 0.9622 | 688 |
| panel_base_3of3 | 644 | 53 | 0.9177 | 0.0108 | 591 | 0.8834 | 0.0124 | 669 | 224 | 41 | 0.9363 | 603 | 0.8765 | 688 |
| ind_gate | 553 | 64 | 0.8843 | 0.0136 | 489 | 0.7309 | 0.0171 | 669 | 193 | 47 | 0.9150 | 506 | 0.7355 | 688 |
| ind_gate_tau | 465 | 48 | 0.8968 | 0.0141 | 417 | 0.6233 | 0.0187 | 669 | 161 | 36 | 0.9226 | 429 | 0.6235 | 688 |

Table 5b. Pairwise overlap of admitted trajectories (identified by problem and attempt position), rows sample_6..300; wrong under the host rule against the vault label. a_only_wrong = wrong trajectories of arm a that arm b does not admit.

| arm_a | arm_b | shared | a_only | b_only | shared_wrong | a_only_wrong | b_only_wrong |
|---|---|---|---|---|---|---|---|
| panel_base_3of3 | panel_base_2of3 | 644 | 0 | 68 | 53 | 0 | 14 |
| panel_base_3of3 | vote | 639 | 5 | 119 | 49 | 4 | 45 |
| panel_base_3of3 | runsok | 644 | 0 | 218 | 53 | 0 | 140 |
| panel_base_3of3 | gt | 591 | 53 | 78 | 0 | 53 | 0 |
| panel_base_2of3 | vote | 706 | 6 | 52 | 63 | 4 | 31 |
| panel_base_2of3 | runsok | 712 | 0 | 150 | 67 | 0 | 126 |
| panel_base_2of3 | gt | 645 | 67 | 24 | 0 | 67 | 0 |
| vote | runsok | 758 | 0 | 104 | 94 | 0 | 99 |
| vote | gt | 664 | 94 | 5 | 0 | 94 | 0 |
| runsok | gt | 669 | 193 | 0 | 0 | 193 | 0 |
