# Audit of label misses

Every certificate whose value misses the benchmark label was checked against the problem text by re-solving the problem. Three-family certificates (all three families A, B, C agree at the stated instance) and two-family-only certificates (exactly two families agree) are listed. Family A is DeepSeek-V4-Flash, which also extracts the data, family B is GPT-6.1 Sol, and family C is Claude Sonnet 5.5. Scoring: OptMATH sets with `round_aware` of `scripts/score_eval.py`, NANO-CO sets with `label_match` of `scripts/e3_calibrate.py`; OptMATH-295 excludes `sample_1` to `sample_5`. Machine-readable list: `audit_classes.csv`. Certified values are those of the stored judge decisions (`judges.csv` of each set); labels are those of `problems.csv`.

## Classes

- **D**: decisive data are absent from the problem text (the text gives examples, a range, or a statement that similar values apply).
- **P**: the text prints coefficients at reduced precision, and the certified value lies within 0.1% of the label.
- **B**: the text is complete, and re-solving it reproduces the certified value, so the label is not the optimum of the text.
- **T**: the label is the optimum of an instance that differs from the text in a stated rule or value.
- **U**: the text supports two readings, and the label and the certified value are the optima under the two readings.
- **E**: the extracted parameter set differs from the text, and the label is the optimum of the text.
- **M**: the parameter set equals the text, the label is the optimum of the text, and the agreeing programs share a modeling error.

## OptMATH-295

45 audited problems: 35 three-family, 10 two-family-only.

| Identifier | Record | Certified | Label | Class | Agreement | Evidence |
|---|---:|---:|---:|---|---|---|
| `sample_16` | 110604 | 46296 | 46332.0 | D | three |  |
| `sample_122` | 130870 | 370262 | 357350.0 | D | three |  |
| `sample_124` | 168519 | 5281 | 5118.0 | D | three |  |
| `sample_126` | 37452 | 358875 | 351982.0 | D | three |  |
| `sample_127` | 69436 | 9987 | 11584.0 | D | three |  |
| `sample_130` | 195294 | 125883 | 126431.0 | D | three |  |
| `sample_133` | 68876 | 1 | 41.0 | D | three |  |
| `sample_134` | 195825 | 26844 | 27004.0 | D | three |  |
| `sample_139` | 94895 | 4005 | 4075.0 | D | three |  |
| `sample_148` | 40066 | 23454 | 22960.0 | D | three |  |
| `sample_166` | 178706 | 1745 | 1835.0 | D | three |  |
| `sample_167` | 140763 | 304102 | 299884.0 | D | three |  |
| `sample_186` | 163918 | 391802 | 376561.0 | D | three |  |
| `sample_203` | 29325 | 754 | 770.0 | D | three |  |
| `sample_218` | 32967 | 2879 | 2939.0 | D | three |  |
| `sample_225` | 138326 | 48294 | 48299.0 | D | three |  |
| `sample_242` | 118354 | 124815 | 119444.70426047321 | D | three |  |
| `sample_252` | 154256 | 1.413 | 1.40052737380067 | D | three |  |
| `sample_281` | 25409 | 1.8249 | 1.520688496320867 | D | three |  |
| `sample_287` | 122427 | 19090 | 19276.0 | D | three |  |
| `sample_30` | 142853 | 10835935.26 | 10834440.371982582 | P | three |  |
| `sample_37` | 198916 | 1.546 | 1.545455400270471 | P | three |  |
| `sample_57` | 120435 | 26326703.48 | 26322521.94997295 | P | three |  |
| `sample_125` | 120285 | 490809.3261 | 490867.80000000005 | P | three |  |
| `sample_137` | 152969 | 317278.2124 | 317210.88 | P | three |  |
| `sample_177` | 850 | 1.607 | 1.606575707076325 | P | three |  |
| `sample_198` | 149 | 963943.0719 | 964259.3743630844 | P | three |  |
| `sample_269` | 56160 | 74276.52853 | 74265.5 | P | three |  |
| `sample_292` | 169392 | 1334786.129 | 1333742.601993409 | P | three |  |
| `sample_98` | 64175 | 75679 | 75312.0 | B | three | Lot sizing. The relaxation without capacities has optimum 75679, so the label is unattainable. |
| `sample_108` | 85008 | 101235 | 100841.0 | B | three | The mixed-integer program of the text has optimum 101235. |
| `sample_233` | 52730 | 122842 | 122814.0 | B | three | The mixed-integer program of the text has optimum 122842. |
| `sample_110` | 60043 | 4702 | 3856.0 | T | three | Unit commitment. The label is the optimum when an initial fleet runs without start-up cost. The text states the same numbers as limits on start-ups in the first period. |
| `sample_267` | 175368 | 4845 | 3898.0 | T | three | Same as record 60043. |
| `sample_94` | 166455 | 1806 | 1790.0 | E | three | The demand table is stored by market and product and read by product and market. The optimum of the text is 1790. |
| `sample_11` | 177392 | 10510918 | 10622791.791367784 | D | two_only |  |
| `sample_58` | 140568 | 2361 | 41673.0 | D | two_only |  |
| `sample_65` | 162141 | 780930 | 772406.0 | D | two_only |  |
| `sample_200` | 84975 | 2 | 4.0 | D | two_only |  |
| `sample_220` | 172949 | 28057.68421 | 27737.0 | D | two_only |  |
| `sample_243` | 31720 | 0.01351353483 | 0.012070001450990001 | D | two_only |  |
| `sample_290` | 176518 | 811608 | 800200.0 | D | two_only |  |
| `sample_45` | 200145 | 40911 | 41877.5 | B | two_only | The linear program of the text has maximum 40911, below the label. |
| `sample_147` | 28743 | 2927 | 3140.0 | T | two_only | Unit commitment, as record 60043. |
| `sample_77` | 26476 | 17994 | 17514.0 | U | two_only | Binary assignment variables give 17994 and general integer variables give 17514. The text supports both. |

## OptMATH-200

21 audited problems: 19 three-family, 2 two-family-only.

| Identifier | Record | Certified | Label | Class | Agreement | Evidence |
|---|---:|---:|---:|---|---|---|
| `conf_26837` | 26837 | 336514 | 332566.0 | D | three |  |
| `conf_89332` | 89332 | 306502 | 307308.0 | D | three |  |
| `conf_99380` | 99380 | 47405 | 48483.0 | D | three |  |
| `conf_168766` | 168766 | 65815 | 70127.0 | D | three |  |
| `conf_188937` | 188937 | 233938 | 251706.0 | D | three |  |
| `conf_189571` | 189571 | 49372 | 41005.0 | D | three |  |
| `conf_66014` | 66014 | 11250495.53 | 11417460.619134724 | D | three |  |
| `conf_14681` | 14681 | 322806.6949 | 322663.59090909094 | P | three |  |
| `conf_22825` | 22825 | 549394.656 | 549293.4158730159 | P | three |  |
| `conf_30081` | 30081 | 1141276.061 | 1141009.1488119946 | P | three |  |
| `conf_41525` | 41525 | 1140782.67 | 1140127.2305978902 | P | three |  |
| `conf_158046` | 158046 | 1139174.632 | 1139386.2545412816 | P | three |  |
| `conf_164155` | 164155 | 29525001.63 | 29533486.44277713 | P | three |  |
| `conf_184248` | 184248 | 329333.2844 | 329213.176 | P | three |  |
| `conf_59835` | 59835 | 277 | 276.0 | B | three | The linear program of the text has optimum 277. |
| `conf_77064` | 77064 | 10824 | 10969.0 | B | three | The linear program of the text has optimum 10824. |
| `conf_89312` | 89312 | 2396 | 2482.0 | B | three | The mixed-integer program of the text has optimum 2396. |
| `conf_144925` | 144925 | 1953 | 1987.0 | B | three | The mixed-integer program of the text has optimum 1953. The rule "B or C" withdraws the certificate: family C reports `backlog_penalty` as mismatched, which the text states as given (an over-flag). |
| `conf_187975` | 187975 | 31277 | 31871.0 | B | three | The linear program of the text has optimum 31277. |
| `conf_16675` | 16675 | 1235.569921 | 2347.1979356914976 | D | two_only |  |
| `conf_120613` | 120613 | 1844 | 1819.0 | D | two_only |  |

## NANO-CO-150

15 audited problems: 3 three-family, 12 two-family-only.

| Identifier | Certified | Label | Class | Agreement | Evidence |
|---|---:|---:|---|---|---|
| `e3_CARP_easy_36` | 380 | 552 | T | three | The text allows direct travel between any two nodes, which gives 380. The labeled route uses the listed segments only. |
| `e3_CARP_easy_37` | 356 | 377 | T | three | Same as CARP_easy_36. |
| `e3_MCF_easy_121` | 65 | 127 | E | three | The parameter set places supplies and demands on other nodes than the text. |
| `e3_CPP_easy_52` | 629 | 719 | T | two_only | Direct travel gives 629 and the listed segments give 719. |
| `e3_CPP_easy_54` | 580 | 825 | T | two_only | Direct travel gives 580 and the listed segments give 825. |
| `e3_RPP_easy_188` | 493 | 655 | T | two_only | The text states that the network is fully connected. The labeled route uses the listed segments only. |
| `e3_RPP_easy_189` | 524 | 798 | T | two_only | Same as RPP_easy_188. |
| `e3_mTSP_easy_162` | 354 | 318 | U | two_only | Same as VRP_easy_244. |
| `e3_mTSP_easy_164` | 272 | 235 | U | two_only | Same as VRP_easy_244. |
| `e3_mTSP_easy_165` | 353 | 304 | U | two_only | Same as VRP_easy_244. |
| `e3_QAP_easy_185` | 2227 | 4454 | U | two_only | The label counts every pair of facilities twice. The text gives each flow once. |
| `e3_VRP_easy_244` | 276 | 261 | U | two_only | The label leaves one vehicle unused. The text states that both vehicles start from the depot. |
| `e3_VRP_easy_245` | 238 | 233 | U | two_only | Same as VRP_easy_244. |
| `e3_JSSP_93` | 116.999999 | 132 | E | two_only | The parameter set changes the machine and the duration of two operations. The text gives 132. |
| `e3_CPP_easy_51` | 1536 | 898 | M | two_only | The complete graph gives 788 and the listed segments give 898. The certified value is neither. |

## NANO-CO-95

12 audited problems: 6 three-family, 6 two-family-only.

| Identifier | Certified | Label | Class | Agreement | Evidence |
|---|---:|---:|---|---|---|
| `e3_MC_easy_114` | 5 | 13 | T | three | The text defines the cost of a cut by unit costs, which gives 5. The label is the capacity of the cut. |
| `e3_MCC_easy_120` | 86 | 83 | T | three | The text puts a lower bound on arc 4 to 5 and the stored instance on arc 5 to 4. The text gives 86. |
| `e3_RPP_easy_187` | 554 | 712 | T | three | Direct travel gives 554 and the listed segments give 712. |
| `e3_mTSP_easy_161` | 358 | 326 | U | three | One tour gives 326 and two non-empty tours give 358. |
| `e3_mTSP_easy_163` | 324 | 305 | U | three | One tour gives 305 and two non-empty tours give 324. |
| `e3_SM_easy_197` | 13 | 12 | E | three | The parameter set changes one row of the preference table. The text gives 12. |
| `e3_CARP_easy_38` | 328 | 382 | T | two_only | Direct travel gives 328. |
| `e3_CPP_easy_55` | 418 | 501 | T | two_only | Direct travel gives 418 and the listed segments give 501. |
| `e3_RPP_easy_186` | 515 | 665 | T | two_only | Same as RPP_easy_188. |
| `e3_VRP_easy_242` | 362 | 328 | U | two_only | Same as VRP_easy_244. |
| `e3_CFLP_42` | 11855 | 1960 | M | two_only | Two programs weight the distance by the demand. The text gives a cost per pair, and the third program returns 1960. |
| `e3_TSPTW_easy_224` | 367.4883789 | 368 | M | two_only | Two programs use unrounded coordinate distances instead of the stated travel times. |

## Withdrawn label-matching certificates

The 40 three-family certificates whose value matches the label and that the rule "B or C" withdraws (family B or family C raises a flag in the data verification). Flags list the parameters each family reported as mismatched or not stated; the replies are in `runs/<identifier>/verification_<family>.json` of each set.

| Set | Identifier | Certified | Label | Family B flags | Family C flags | Finding |
|---|---|---:|---:|---|---|---|
| OptMATH-295 | `sample_210` | 54 | 54.0 | setup_cost (mismatch) | setup_cost (mismatch) | Flag correct: the extraction differs from the text, optimum unchanged |
| NANO-CO-150 | `e3_AP_easy_5` | 99 | 99 | cost_matrix (mismatch) | cost_matrix (mismatch) | Flag correct: the extraction differs from the text, optimum unchanged |
| NANO-CO-150 | `e3_MCC_easy_117` | 188 | 188 | arc_max_flow (mismatch) | arc_max_flow (mismatch) | Flag correct: the extraction differs from the text, optimum unchanged |
| NANO-CO-150 | `e3_VRP_easy_243` | 261 | 261 | distance_matrix (mismatch) | distance_matrix (mismatch) | Flag correct: the extraction differs from the text, optimum unchanged |
| NANO-CO-150 | `e3_GCP_81` | 3 | 3 | num_edges (mismatch); max_slots (not stated); slot_cost (not stated) | num_edges (mismatch); min_slots (not stated); max_slots (not stated); slot_cost (not stated) | Flag correct: the extraction differs from the text, optimum unchanged |
| OptMATH-295 | `sample_96` | 0.9565109186 | 0.956510918598474 | cost_peak0_aa0 (not stated); cost_peak0_aa1 (not stated); cost_peak0_aa2 (not stated); cost_peak0_aa4 (not stated); cost_peak1_aa0 (not stated); cost_peak1_aa1 (not stated); cost_peak1_aa2 (not stated); cost_peak1_aa3 (not stated); cost_peak2_aa0 (not stated); cost_peak2_aa2 (not stated); cost_peak2_aa3 (not stated); cost_peak2_aa5 (not stated); cost_peak3_aa0 (not stated); cost_peak3_aa1 (not stated); cost_peak3_aa2 (not stated); cost_peak3_aa5 (not stated); cost_peak4_aa0 (not stated); cost_peak4_aa1 (not stated); cost_peak4_aa3 (not stated); cost_peak4_aa4 (not stated); noe_pair_p1aa1_p2aa0_rhs (not stated); noe_pair_p1aa3_p2aa0_rhs (not stated) | cost_peak0_aa2 (not stated); cost_peak0_aa4 (not stated); cost_peak1_aa0 (not stated); cost_peak1_aa1 (not stated); cost_peak1_aa3 (not stated); cost_peak2_aa0 (not stated); cost_peak2_aa2 (not stated); cost_peak2_aa3 (not stated); cost_peak2_aa5 (not stated); cost_peak3_aa0 (not stated); cost_peak3_aa1 (not stated); cost_peak3_aa2 (not stated); cost_peak3_aa5 (not stated); cost_peak4_aa0 (not stated); cost_peak4_aa1 (not stated); cost_peak4_aa3 (not stated); cost_peak4_aa4 (not stated) | Flag correct: data absent from the text, value matches the label |
| OptMATH-200 | `conf_37513` | 6 | 6.0 | demand_1_0 (not stated) | demand_1_0 (not stated) | Flag correct: data absent from the text, value matches the label |
| OptMATH-200 | `conf_117930` | 13 | 13.0 | cost_0_1 (not stated); cost_0_2 (not stated); cost_0_3 (not stated); cost_0_4 (not stated); cost_0_5 (not stated); cost_0_6 (not stated); cost_1_2 (not stated); cost_1_3 (not stated) | cost_1_2 (not stated); cost_1_3 (not stated) | Flag correct: data absent from the text, value matches the label |
| OptMATH-200 | `conf_147375` | 25 | 25.0 | product_capacity_0_0to1 (not stated); product_capacity_1_0to1 (not stated); product_capacity_0_1to0 (not stated); product_capacity_1_1to0 (not stated) | product_capacity_generic_low (not stated); product_capacity_generic_high (not stated) | Flag correct: data absent from the text, value matches the label |
| OptMATH-200 | `conf_167866` | 96827 | 96827.0 | capacity (not stated) | capacity (not stated) | Flag correct: data absent from the text, value matches the label |
| OptMATH-295 | `sample_46` | 96627 | 96627.0 | demand (not stated); min_frequency (not stated); max_frequency (not stated); vehicle_usage_per_frequency (not stated) | min_frequency (not stated); max_frequency (not stated) | Over-flag: complete list introduced by "for example" |
| OptMATH-295 | `sample_66` | 16202 | 16202.0 | min_production (not stated); max_production (not stated) |  | Over-flag: complete list introduced by "for example" |
| OptMATH-295 | `sample_74` | 2 | 2.0 | preference_matrix (not stated) | assignment_value (not stated); participant_capacity (not stated); car_capacity (not stated) | Over-flag: complete list introduced by "for example" |
| OptMATH-295 | `sample_162` | 5174 | 5174.0 | fixed_cost (not stated); variable_cost (not stated); min_production (not stated); max_production (not stated) | fixed_cost (not stated); variable_cost (not stated); min_production (not stated); max_production (not stated) | Over-flag: complete list introduced by "for example" |
| OptMATH-295 | `sample_182` | 7610 | 7610.0 | min_production (not stated); max_production (not stated) |  | Over-flag: complete list introduced by "for example" |
| OptMATH-295 | `sample_248` | 6 | 6.0 | preferences (not stated) |  | Over-flag: complete list introduced by "for example" |
| OptMATH-295 | `sample_295` | 18287 | 18287.0 | min_production (not stated); max_production (not stated) |  | Over-flag: complete list introduced by "for example" |
| OptMATH-200 | `conf_60138` | 102362 | 102362.0 | cost (not stated) |  | Over-flag: complete list introduced by "for example" |
| OptMATH-200 | `conf_112480` | 3679 | 3679.0 | fixed_cost (not stated); variable_cost (not stated) |  | Over-flag: complete list introduced by "for example" |
| OptMATH-200 | `conf_166697` | 514.5866433 | 514.5866432928707 | demand_P0_P0 (not stated); demand_P1_P0 (not stated); demand_P0_P1 (not stated); demand_P1_P1 (not stated); demand_P0_P2 (not stated); demand_P1_P2 (not stated) |  | Over-flag: complete list introduced by "for example" |
| OptMATH-295 | `sample_13` | 4 | 4.0 |  | assignment_value (not stated) | Over-flag: constant implied by the text |
| OptMATH-295 | `sample_153` | 0.6448462125 | 0.6448462125436131 |  | peak_capacity (not stated); amino_acid_capacity (not stated) | Over-flag: constant implied by the text |
| OptMATH-295 | `sample_214` | 6 | 6.0 |  | participant_capacity (not stated); car_capacity (not stated); assignment_value (not stated) | Over-flag: constant implied by the text |
| OptMATH-295 | `sample_273` | 8 | 8.0 |  | participant_capacity (not stated); car_capacity (not stated) | Over-flag: constant implied by the text |
| OptMATH-295 | `sample_288` | 3 | 3.0 |  | num_centers_available (not stated) | Over-flag: constant implied by the text |
| OptMATH-200 | `conf_40822` | 2 | 2.0 |  | participant_assignment_capacity (not stated); car_assignment_capacity (not stated) | Over-flag: constant implied by the text |
| OptMATH-200 | `conf_78361` | 3 | 3.0 |  | assignment_value (not stated) | Over-flag: constant implied by the text |
| OptMATH-200 | `conf_191579` | 26674 | 26674.0 |  | hold_cost_A (not stated) | Over-flag: constant implied by the text |
| OptMATH-295 | `sample_136` | 14 | 14.0 | cost_matrix (not stated) |  | Over-flag: diagonal of a matrix |
| OptMATH-295 | `sample_159` | 794 | 794.0 | cost (not stated) |  | Over-flag: diagonal of a matrix |
| OptMATH-295 | `sample_199` | 275 | 275.0 | cost (not stated); capacity (not stated) | capacity (mismatch) | Over-flag: diagonal of a matrix |
| OptMATH-295 | `sample_213` | 106 | 106.0 | dispersion_weights (not stated) |  | Over-flag: diagonal of a matrix |
| OptMATH-295 | `sample_215` | 47 | 47.0 | weights (not stated) |  | Over-flag: diagonal of a matrix |
| OptMATH-200 | `conf_56528` | 12 | 12.0 | cost_matrix (not stated) |  | Over-flag: diagonal of a matrix |
| OptMATH-200 | `conf_200444` | 1859 | 1859.0 | cost (not stated) |  | Over-flag: diagonal of a matrix |
| OptMATH-295 | `sample_163` | 101 | 101.0 |  | coverage_benefit_10 (mismatch) | Over-flag: reply unrelated to the data |
| NANO-CO-95 | `e3_HCLP_87` | -4341 | -4341 |  | node_demands (not stated) | Over-flag: reply unrelated to the data |
| OptMATH-200 | `conf_7821` | 3115 | 3115.0 |  | type1_initial_slack (not stated) | Over-flag: reply unrelated to the data |
| OptMATH-200 | `conf_57581` | 20 | 20.0 |  | coverage_requirement (mismatch) | Over-flag: reply unrelated to the data |
| OptMATH-295 | `sample_119` | 64384 | 64384.0 |  | borer_downtime_period (mismatch) | Over-flag: stated value reported as different |

Summary of findings:

| Finding | Problems |
|---|---:|
| Flag correct: the extraction differs from the text, optimum unchanged | 5 |
| Flag correct: data absent from the text, value matches the label | 5 |
| Over-flag: complete list introduced by "for example" | 10 |
| Over-flag: constant implied by the text | 8 |
| Over-flag: diagonal of a matrix | 7 |
| Over-flag: reply unrelated to the data | 4 |
| Over-flag: stated value reported as different | 1 |

