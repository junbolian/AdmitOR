Table 6. Downstream accuracy, `round_aware` of scripts/score_eval.py on the 1,100 evaluation items (unparseable predictions count as wrong); per pass, mean over the passes and standard error of the mean (n-1 in the variance); micro-average over the 1,100 items, macro-average = mean of the five benchmark accuracies. Accuracies in percent.

| configuration | benchmark | n | passes | solved_r1 | solved_r2 | solved_r3 | acc_r1 | acc_r2 | acc_r3 | mean | se_mean |
|---|---|---|---|---|---|---|---|---|---|---|---|
| panel_base_3of3 | ComplexOR | 18 | 3 | 12 | 12 | 13 | 66.67 | 66.67 | 72.22 | 68.52 | 1.85 |
| panel_base_3of3 | IndustryOR | 100 | 3 | 35 | 34 | 32 | 35.00 | 34.00 | 32.00 | 33.67 | 0.88 |
| panel_base_3of3 | Mamo.Complex | 211 | 3 | 107 | 118 | 115 | 50.71 | 55.92 | 54.50 | 53.71 | 1.56 |
| panel_base_3of3 | OptMATH-Bench | 166 | 3 | 95 | 84 | 97 | 57.23 | 50.60 | 58.43 | 55.42 | 2.43 |
| panel_base_3of3 | OptiBench | 605 | 3 | 398 | 410 | 413 | 65.79 | 67.77 | 68.26 | 67.27 | 0.76 |
| panel_base_3of3 | micro-average | 1100 | 3 | 647 | 658 | 670 | 58.82 | 59.82 | 60.91 | 59.85 | 0.60 |
| panel_base_3of3 | macro-average (mean of the five benchmarks) |  | 3 |  |  |  | 55.08 | 54.99 | 57.08 | 55.72 | 0.68 |
| panel_base_2of3 | ComplexOR | 18 | 3 | 12 | 12 | 12 | 66.67 | 66.67 | 66.67 | 66.67 | 0.00 |
| panel_base_2of3 | IndustryOR | 100 | 3 | 34 | 36 | 39 | 34.00 | 36.00 | 39.00 | 36.33 | 1.45 |
| panel_base_2of3 | Mamo.Complex | 211 | 3 | 113 | 115 | 113 | 53.55 | 54.50 | 53.55 | 53.87 | 0.32 |
| panel_base_2of3 | OptMATH-Bench | 166 | 3 | 95 | 90 | 95 | 57.23 | 54.22 | 57.23 | 56.22 | 1.00 |
| panel_base_2of3 | OptiBench | 605 | 3 | 398 | 399 | 409 | 65.79 | 65.95 | 67.60 | 66.45 | 0.58 |
| panel_base_2of3 | micro-average | 1100 | 3 | 652 | 652 | 668 | 59.27 | 59.27 | 60.73 | 59.76 | 0.48 |
| panel_base_2of3 | macro-average (mean of the five benchmarks) |  | 3 |  |  |  | 55.45 | 55.47 | 56.81 | 55.91 | 0.45 |
| vote | ComplexOR | 18 | 3 | 12 | 12 | 12 | 66.67 | 66.67 | 66.67 | 66.67 | 0.00 |
| vote | IndustryOR | 100 | 3 | 34 | 36 | 37 | 34.00 | 36.00 | 37.00 | 35.67 | 0.88 |
| vote | Mamo.Complex | 211 | 3 | 110 | 108 | 114 | 52.13 | 51.18 | 54.03 | 52.45 | 0.84 |
| vote | OptMATH-Bench | 166 | 3 | 95 | 95 | 97 | 57.23 | 57.23 | 58.43 | 57.63 | 0.40 |
| vote | OptiBench | 605 | 3 | 394 | 387 | 402 | 65.12 | 63.97 | 66.45 | 65.18 | 0.72 |
| vote | micro-average | 1100 | 3 | 645 | 638 | 662 | 58.64 | 58.00 | 60.18 | 58.94 | 0.65 |
| vote | macro-average (mean of the five benchmarks) |  | 3 |  |  |  | 55.03 | 55.01 | 56.52 | 55.52 | 0.50 |
| runsok | ComplexOR | 18 | 1 | 13 |  |  | 72.22 |  |  | 72.22 |  |
| runsok | IndustryOR | 100 | 1 | 33 |  |  | 33.00 |  |  | 33.00 |  |
| runsok | Mamo.Complex | 211 | 1 | 107 |  |  | 50.71 |  |  | 50.71 |  |
| runsok | OptMATH-Bench | 166 | 1 | 96 |  |  | 57.83 |  |  | 57.83 |  |
| runsok | OptiBench | 605 | 1 | 392 |  |  | 64.79 |  |  | 64.79 |  |
| runsok | micro-average | 1100 | 1 | 641 |  |  | 58.27 |  |  | 58.27 |  |
| runsok | macro-average (mean of the five benchmarks) |  | 1 |  |  |  | 55.71 |  |  | 55.71 |  |
| gt | ComplexOR | 18 | 1 | 12 |  |  | 66.67 |  |  | 66.67 |  |
| gt | IndustryOR | 100 | 1 | 34 |  |  | 34.00 |  |  | 34.00 |  |
| gt | Mamo.Complex | 211 | 1 | 106 |  |  | 50.24 |  |  | 50.24 |  |
| gt | OptMATH-Bench | 166 | 1 | 92 |  |  | 55.42 |  |  | 55.42 |  |
| gt | OptiBench | 605 | 1 | 410 |  |  | 67.77 |  |  | 67.77 |  |
| gt | micro-average | 1100 | 1 | 654 |  |  | 59.45 |  |  | 59.45 |  |
| gt | macro-average (mean of the five benchmarks) |  | 1 |  |  |  | 54.82 |  |  | 54.82 |  |
| host without learned library | ComplexOR | 18 | 3 | 12 | 12 | 12 | 66.67 | 66.67 | 66.67 | 66.67 | 0.00 |
| host without learned library | IndustryOR | 100 | 3 | 34 | 35 | 35 | 34.00 | 35.00 | 35.00 | 34.67 | 0.33 |
| host without learned library | Mamo.Complex | 211 | 3 | 116 | 123 | 118 | 54.98 | 58.29 | 55.92 | 56.40 | 0.99 |
| host without learned library | OptMATH-Bench | 166 | 3 | 98 | 95 | 94 | 59.04 | 57.23 | 56.63 | 57.63 | 0.72 |
| host without learned library | OptiBench | 605 | 3 | 440 | 429 | 435 | 72.73 | 70.91 | 71.90 | 71.85 | 0.53 |
| host without learned library | micro-average | 1100 | 3 | 700 | 694 | 694 | 63.64 | 63.09 | 63.09 | 63.27 | 0.18 |
| host without learned library | macro-average (mean of the five benchmarks) |  | 3 |  |  |  | 57.48 | 57.62 | 57.22 | 57.44 | 0.12 |
| released library (host); build data as described in the host README, no build record | ComplexOR | 18 | 1 | 12 |  |  | 66.67 |  |  | 66.67 |  |
| released library (host); build data as described in the host README, no build record | IndustryOR | 100 | 1 | 27 |  |  | 27.00 |  |  | 27.00 |  |
| released library (host); build data as described in the host README, no build record | Mamo.Complex | 211 | 1 | 120 |  |  | 56.87 |  |  | 56.87 |  |
| released library (host); build data as described in the host README, no build record | OptMATH-Bench | 166 | 1 | 101 |  |  | 60.84 |  |  | 60.84 |  |
| released library (host); build data as described in the host README, no build record | OptiBench | 605 | 1 | 434 |  |  | 71.74 |  |  | 71.74 |  |
| released library (host); build data as described in the host README, no build record | micro-average | 1100 | 1 | 694 |  |  | 63.09 |  |  | 63.09 |  |
| released library (host); build data as described in the host README, no build record | macro-average (mean of the five benchmarks) |  | 1 |  |  |  | 56.62 |  |  | 56.62 |  |

Host without learned library: `main.py --phase cluster` (learning-phase solve path) with `--top-k 1` on blind copies of the benchmarks, process ended before any library build; prediction = the solver agent's final_result, else the result of the first successful attempt. Its two differences from the evaluation path besides the absent skill: (1) the keyword extractor has no library keyword reference; (2) a backend selector replaces the skill selector.
Released library (host); build data as described in the host README, no build record: pass r1 with the evaluation command of the other passes and `--source-skill-library` = the host's `skill_library/skill_library_learned`; its build data is taken from the host README (clustering on the first 150 problems of optmath-train-300.jsonl, learning phase on the other 150), for which no build record exists.

Table 6b. Paired comparisons (`round_aware`; solved = round-aware hit). r1: pass r1 of each configuration; majority: per item solved in at least two of r1 to r3, only where both have three passes; one mixed row set compares released r1 with the majority of r1 to r3 of the host without learned library. Exact two-sided McNemar p on the discordant items.

| first | second | passes | benchmark | n | both | only_first | only_second | neither | mcnemar_p |
|---|---|---|---|---|---|---|---|---|---|
| panel_base_3of3 | panel_base_2of3 | r1 | ComplexOR | 18 | 11 | 1 | 1 | 5 | 1 |
| panel_base_3of3 | panel_base_2of3 | r1 | IndustryOR | 100 | 29 | 6 | 5 | 60 | 1 |
| panel_base_3of3 | panel_base_2of3 | r1 | Mamo.Complex | 211 | 97 | 10 | 16 | 88 | 0.3269 |
| panel_base_3of3 | panel_base_2of3 | r1 | OptMATH-Bench | 166 | 79 | 16 | 16 | 55 | 1 |
| panel_base_3of3 | panel_base_2of3 | r1 | OptiBench | 605 | 357 | 41 | 41 | 166 | 1 |
| panel_base_3of3 | panel_base_2of3 | r1 | all 1,100 | 1100 | 573 | 74 | 79 | 374 | 0.7465 |
| panel_base_3of3 | vote | r1 | ComplexOR | 18 | 11 | 1 | 1 | 5 | 1 |
| panel_base_3of3 | vote | r1 | IndustryOR | 100 | 31 | 4 | 3 | 62 | 1 |
| panel_base_3of3 | vote | r1 | Mamo.Complex | 211 | 96 | 11 | 14 | 90 | 0.69 |
| panel_base_3of3 | vote | r1 | OptMATH-Bench | 166 | 77 | 18 | 18 | 53 | 1 |
| panel_base_3of3 | vote | r1 | OptiBench | 605 | 360 | 38 | 34 | 173 | 0.7239 |
| panel_base_3of3 | vote | r1 | all 1,100 | 1100 | 575 | 72 | 70 | 383 | 0.9332 |
| panel_base_3of3 | runsok | r1 | ComplexOR | 18 | 12 | 0 | 1 | 5 | 1 |
| panel_base_3of3 | runsok | r1 | IndustryOR | 100 | 30 | 5 | 3 | 62 | 0.7266 |
| panel_base_3of3 | runsok | r1 | Mamo.Complex | 211 | 95 | 12 | 12 | 92 | 1 |
| panel_base_3of3 | runsok | r1 | OptMATH-Bench | 166 | 77 | 18 | 19 | 52 | 1 |
| panel_base_3of3 | runsok | r1 | OptiBench | 605 | 361 | 37 | 31 | 176 | 0.5446 |
| panel_base_3of3 | runsok | r1 | all 1,100 | 1100 | 575 | 72 | 66 | 387 | 0.6705 |
| panel_base_3of3 | gt | r1 | ComplexOR | 18 | 11 | 1 | 1 | 5 | 1 |
| panel_base_3of3 | gt | r1 | IndustryOR | 100 | 27 | 8 | 7 | 58 | 1 |
| panel_base_3of3 | gt | r1 | Mamo.Complex | 211 | 96 | 11 | 10 | 94 | 1 |
| panel_base_3of3 | gt | r1 | OptMATH-Bench | 166 | 77 | 18 | 15 | 56 | 0.7283 |
| panel_base_3of3 | gt | r1 | OptiBench | 605 | 371 | 27 | 39 | 168 | 0.1753 |
| panel_base_3of3 | gt | r1 | all 1,100 | 1100 | 582 | 65 | 72 | 381 | 0.6084 |
| panel_base_3of3 | host without learned library | r1 | ComplexOR | 18 | 11 | 1 | 1 | 5 | 1 |
| panel_base_3of3 | host without learned library | r1 | IndustryOR | 100 | 30 | 5 | 4 | 61 | 1 |
| panel_base_3of3 | host without learned library | r1 | Mamo.Complex | 211 | 99 | 8 | 17 | 87 | 0.1078 |
| panel_base_3of3 | host without learned library | r1 | OptMATH-Bench | 166 | 79 | 16 | 19 | 52 | 0.7359 |
| panel_base_3of3 | host without learned library | r1 | OptiBench | 605 | 380 | 18 | 60 | 147 | 1.973e-06 |
| panel_base_3of3 | host without learned library | r1 | all 1,100 | 1100 | 599 | 48 | 101 | 352 | 1.687e-05 |
| panel_base_3of3 | released library (host); build data as described in the host README, no build record | r1 | ComplexOR | 18 | 11 | 1 | 1 | 5 | 1 |
| panel_base_3of3 | released library (host); build data as described in the host README, no build record | r1 | IndustryOR | 100 | 24 | 11 | 3 | 62 | 0.05737 |
| panel_base_3of3 | released library (host); build data as described in the host README, no build record | r1 | Mamo.Complex | 211 | 99 | 8 | 21 | 83 | 0.02412 |
| panel_base_3of3 | released library (host); build data as described in the host README, no build record | r1 | OptMATH-Bench | 166 | 78 | 17 | 23 | 48 | 0.4296 |
| panel_base_3of3 | released library (host); build data as described in the host README, no build record | r1 | OptiBench | 605 | 364 | 34 | 70 | 137 | 0.0005343 |
| panel_base_3of3 | released library (host); build data as described in the host README, no build record | r1 | all 1,100 | 1100 | 576 | 71 | 118 | 335 | 0.0007755 |
| panel_base_2of3 | vote | r1 | ComplexOR | 18 | 11 | 1 | 1 | 5 | 1 |
| panel_base_2of3 | vote | r1 | IndustryOR | 100 | 28 | 6 | 6 | 60 | 1 |
| panel_base_2of3 | vote | r1 | Mamo.Complex | 211 | 100 | 13 | 10 | 88 | 0.6776 |
| panel_base_2of3 | vote | r1 | OptMATH-Bench | 166 | 77 | 18 | 18 | 53 | 1 |
| panel_base_2of3 | vote | r1 | OptiBench | 605 | 362 | 36 | 32 | 175 | 0.7163 |
| panel_base_2of3 | vote | r1 | all 1,100 | 1100 | 578 | 74 | 67 | 381 | 0.6135 |
| panel_base_2of3 | runsok | r1 | ComplexOR | 18 | 12 | 0 | 1 | 5 | 1 |
| panel_base_2of3 | runsok | r1 | IndustryOR | 100 | 31 | 3 | 2 | 64 | 1 |
| panel_base_2of3 | runsok | r1 | Mamo.Complex | 211 | 100 | 13 | 7 | 91 | 0.2632 |
| panel_base_2of3 | runsok | r1 | OptMATH-Bench | 166 | 75 | 20 | 21 | 50 | 1 |
| panel_base_2of3 | runsok | r1 | OptiBench | 605 | 358 | 40 | 34 | 173 | 0.5614 |
| panel_base_2of3 | runsok | r1 | all 1,100 | 1100 | 576 | 76 | 65 | 383 | 0.3998 |
| panel_base_2of3 | gt | r1 | ComplexOR | 18 | 11 | 1 | 1 | 5 | 1 |
| panel_base_2of3 | gt | r1 | IndustryOR | 100 | 30 | 4 | 4 | 62 | 1 |
| panel_base_2of3 | gt | r1 | Mamo.Complex | 211 | 99 | 14 | 7 | 91 | 0.1892 |
| panel_base_2of3 | gt | r1 | OptMATH-Bench | 166 | 80 | 15 | 12 | 59 | 0.7011 |
| panel_base_2of3 | gt | r1 | OptiBench | 605 | 371 | 27 | 39 | 168 | 0.1753 |
| panel_base_2of3 | gt | r1 | all 1,100 | 1100 | 591 | 61 | 63 | 385 | 0.9285 |
| panel_base_2of3 | host without learned library | r1 | ComplexOR | 18 | 11 | 1 | 1 | 5 | 1 |
| panel_base_2of3 | host without learned library | r1 | IndustryOR | 100 | 31 | 3 | 3 | 63 | 1 |
| panel_base_2of3 | host without learned library | r1 | Mamo.Complex | 211 | 106 | 7 | 10 | 88 | 0.6291 |
| panel_base_2of3 | host without learned library | r1 | OptMATH-Bench | 166 | 80 | 15 | 18 | 53 | 0.7283 |
| panel_base_2of3 | host without learned library | r1 | OptiBench | 605 | 378 | 20 | 62 | 145 | 3.715e-06 |
| panel_base_2of3 | host without learned library | r1 | all 1,100 | 1100 | 606 | 46 | 94 | 354 | 6.106e-05 |
| panel_base_2of3 | released library (host); build data as described in the host README, no build record | r1 | ComplexOR | 18 | 11 | 1 | 1 | 5 | 1 |
| panel_base_2of3 | released library (host); build data as described in the host README, no build record | r1 | IndustryOR | 100 | 25 | 9 | 2 | 64 | 0.06543 |
| panel_base_2of3 | released library (host); build data as described in the host README, no build record | r1 | Mamo.Complex | 211 | 102 | 11 | 18 | 80 | 0.2649 |
| panel_base_2of3 | released library (host); build data as described in the host README, no build record | r1 | OptMATH-Bench | 166 | 79 | 16 | 22 | 49 | 0.4177 |
| panel_base_2of3 | released library (host); build data as described in the host README, no build record | r1 | OptiBench | 605 | 371 | 27 | 63 | 144 | 0.0001878 |
| panel_base_2of3 | released library (host); build data as described in the host README, no build record | r1 | all 1,100 | 1100 | 588 | 64 | 106 | 342 | 0.001586 |
| vote | runsok | r1 | ComplexOR | 18 | 12 | 0 | 1 | 5 | 1 |
| vote | runsok | r1 | IndustryOR | 100 | 29 | 5 | 4 | 62 | 1 |
| vote | runsok | r1 | Mamo.Complex | 211 | 93 | 17 | 14 | 87 | 0.7201 |
| vote | runsok | r1 | OptMATH-Bench | 166 | 78 | 17 | 18 | 53 | 1 |
| vote | runsok | r1 | OptiBench | 605 | 365 | 29 | 27 | 184 | 0.8939 |
| vote | runsok | r1 | all 1,100 | 1100 | 577 | 68 | 64 | 391 | 0.7941 |
| vote | gt | r1 | ComplexOR | 18 | 12 | 0 | 0 | 6 | 1 |
| vote | gt | r1 | IndustryOR | 100 | 27 | 7 | 7 | 59 | 1 |
| vote | gt | r1 | Mamo.Complex | 211 | 95 | 15 | 11 | 90 | 0.5572 |
| vote | gt | r1 | OptMATH-Bench | 166 | 75 | 20 | 17 | 54 | 0.7428 |
| vote | gt | r1 | OptiBench | 605 | 372 | 22 | 38 | 173 | 0.05189 |
| vote | gt | r1 | all 1,100 | 1100 | 581 | 64 | 73 | 382 | 0.4944 |
| vote | host without learned library | r1 | ComplexOR | 18 | 12 | 0 | 0 | 6 | 1 |
| vote | host without learned library | r1 | IndustryOR | 100 | 29 | 5 | 5 | 61 | 1 |
| vote | host without learned library | r1 | Mamo.Complex | 211 | 100 | 10 | 16 | 85 | 0.3269 |
| vote | host without learned library | r1 | OptMATH-Bench | 166 | 78 | 17 | 20 | 51 | 0.7428 |
| vote | host without learned library | r1 | OptiBench | 605 | 377 | 17 | 63 | 148 | 2.266e-07 |
| vote | host without learned library | r1 | all 1,100 | 1100 | 596 | 49 | 104 | 351 | 1.031e-05 |
| vote | released library (host); build data as described in the host README, no build record | r1 | ComplexOR | 18 | 12 | 0 | 0 | 6 | 1 |
| vote | released library (host); build data as described in the host README, no build record | r1 | IndustryOR | 100 | 25 | 9 | 2 | 64 | 0.06543 |
| vote | released library (host); build data as described in the host README, no build record | r1 | Mamo.Complex | 211 | 101 | 9 | 19 | 82 | 0.08716 |
| vote | released library (host); build data as described in the host README, no build record | r1 | OptMATH-Bench | 166 | 81 | 14 | 20 | 51 | 0.3915 |
| vote | released library (host); build data as described in the host README, no build record | r1 | OptiBench | 605 | 369 | 25 | 65 | 146 | 2.966e-05 |
| vote | released library (host); build data as described in the host README, no build record | r1 | all 1,100 | 1100 | 588 | 57 | 106 | 349 | 0.0001533 |
| runsok | gt | r1 | ComplexOR | 18 | 12 | 1 | 0 | 5 | 1 |
| runsok | gt | r1 | IndustryOR | 100 | 29 | 4 | 5 | 62 | 1 |
| runsok | gt | r1 | Mamo.Complex | 211 | 95 | 12 | 11 | 93 | 1 |
| runsok | gt | r1 | OptMATH-Bench | 166 | 74 | 22 | 18 | 52 | 0.6358 |
| runsok | gt | r1 | OptiBench | 605 | 373 | 19 | 37 | 176 | 0.02224 |
| runsok | gt | r1 | all 1,100 | 1100 | 583 | 58 | 71 | 388 | 0.2907 |
| runsok | host without learned library | r1 | ComplexOR | 18 | 12 | 1 | 0 | 5 | 1 |
| runsok | host without learned library | r1 | IndustryOR | 100 | 30 | 3 | 4 | 63 | 1 |
| runsok | host without learned library | r1 | Mamo.Complex | 211 | 100 | 7 | 16 | 88 | 0.09314 |
| runsok | host without learned library | r1 | OptMATH-Bench | 166 | 79 | 17 | 19 | 51 | 0.8679 |
| runsok | host without learned library | r1 | OptiBench | 605 | 374 | 18 | 66 | 147 | 1.333e-07 |
| runsok | host without learned library | r1 | all 1,100 | 1100 | 595 | 46 | 105 | 354 | 1.765e-06 |
| runsok | released library (host); build data as described in the host README, no build record | r1 | ComplexOR | 18 | 12 | 1 | 0 | 5 | 1 |
| runsok | released library (host); build data as described in the host README, no build record | r1 | IndustryOR | 100 | 24 | 9 | 3 | 64 | 0.146 |
| runsok | released library (host); build data as described in the host README, no build record | r1 | Mamo.Complex | 211 | 97 | 10 | 23 | 81 | 0.03508 |
| runsok | released library (host); build data as described in the host README, no build record | r1 | OptMATH-Bench | 166 | 80 | 16 | 21 | 49 | 0.5114 |
| runsok | released library (host); build data as described in the host README, no build record | r1 | OptiBench | 605 | 364 | 28 | 70 | 143 | 2.64e-05 |
| runsok | released library (host); build data as described in the host README, no build record | r1 | all 1,100 | 1100 | 577 | 64 | 117 | 342 | 9.995e-05 |
| gt | host without learned library | r1 | ComplexOR | 18 | 12 | 0 | 0 | 6 | 1 |
| gt | host without learned library | r1 | IndustryOR | 100 | 30 | 4 | 4 | 62 | 1 |
| gt | host without learned library | r1 | Mamo.Complex | 211 | 99 | 7 | 17 | 88 | 0.06391 |
| gt | host without learned library | r1 | OptMATH-Bench | 166 | 79 | 13 | 19 | 55 | 0.3771 |
| gt | host without learned library | r1 | OptiBench | 605 | 390 | 20 | 50 | 145 | 0.0004403 |
| gt | host without learned library | r1 | all 1,100 | 1100 | 610 | 44 | 90 | 356 | 8.745e-05 |
| gt | released library (host); build data as described in the host README, no build record | r1 | ComplexOR | 18 | 12 | 0 | 0 | 6 | 1 |
| gt | released library (host); build data as described in the host README, no build record | r1 | IndustryOR | 100 | 23 | 11 | 4 | 62 | 0.1185 |
| gt | released library (host); build data as described in the host README, no build record | r1 | Mamo.Complex | 211 | 98 | 8 | 22 | 83 | 0.01612 |
| gt | released library (host); build data as described in the host README, no build record | r1 | OptMATH-Bench | 166 | 78 | 14 | 23 | 51 | 0.1877 |
| gt | released library (host); build data as described in the host README, no build record | r1 | OptiBench | 605 | 380 | 30 | 54 | 141 | 0.01163 |
| gt | released library (host); build data as described in the host README, no build record | r1 | all 1,100 | 1100 | 591 | 63 | 103 | 343 | 0.002369 |
| host without learned library | released library (host); build data as described in the host README, no build record | r1 | ComplexOR | 18 | 12 | 0 | 0 | 6 | 1 |
| host without learned library | released library (host); build data as described in the host README, no build record | r1 | IndustryOR | 100 | 25 | 9 | 2 | 64 | 0.06543 |
| host without learned library | released library (host); build data as described in the host README, no build record | r1 | Mamo.Complex | 211 | 107 | 9 | 13 | 82 | 0.5235 |
| host without learned library | released library (host); build data as described in the host README, no build record | r1 | OptMATH-Bench | 166 | 79 | 19 | 22 | 46 | 0.7552 |
| host without learned library | released library (host); build data as described in the host README, no build record | r1 | OptiBench | 605 | 403 | 37 | 31 | 134 | 0.5446 |
| host without learned library | released library (host); build data as described in the host README, no build record | r1 | all 1,100 | 1100 | 626 | 74 | 68 | 332 | 0.6749 |
| panel_base_3of3 | panel_base_2of3 | majority of r1-r3 | ComplexOR | 18 | 12 | 1 | 0 | 5 | 1 |
| panel_base_3of3 | panel_base_2of3 | majority of r1-r3 | IndustryOR | 100 | 32 | 1 | 5 | 62 | 0.2188 |
| panel_base_3of3 | panel_base_2of3 | majority of r1-r3 | Mamo.Complex | 211 | 110 | 8 | 7 | 86 | 1 |
| panel_base_3of3 | panel_base_2of3 | majority of r1-r3 | OptMATH-Bench | 166 | 82 | 12 | 13 | 59 | 1 |
| panel_base_3of3 | panel_base_2of3 | majority of r1-r3 | OptiBench | 605 | 396 | 20 | 15 | 174 | 0.4996 |
| panel_base_3of3 | panel_base_2of3 | majority of r1-r3 | all 1,100 | 1100 | 632 | 42 | 40 | 386 | 0.9122 |
| panel_base_3of3 | vote | majority of r1-r3 | ComplexOR | 18 | 12 | 1 | 0 | 5 | 1 |
| panel_base_3of3 | vote | majority of r1-r3 | IndustryOR | 100 | 32 | 1 | 4 | 63 | 0.375 |
| panel_base_3of3 | vote | majority of r1-r3 | Mamo.Complex | 211 | 111 | 7 | 5 | 88 | 0.7744 |
| panel_base_3of3 | vote | majority of r1-r3 | OptMATH-Bench | 166 | 79 | 15 | 17 | 55 | 0.8601 |
| panel_base_3of3 | vote | majority of r1-r3 | OptiBench | 605 | 394 | 22 | 9 | 180 | 0.02945 |
| panel_base_3of3 | vote | majority of r1-r3 | all 1,100 | 1100 | 628 | 46 | 35 | 391 | 0.2664 |
| panel_base_3of3 | host without learned library | majority of r1-r3 | ComplexOR | 18 | 12 | 1 | 0 | 5 | 1 |
| panel_base_3of3 | host without learned library | majority of r1-r3 | IndustryOR | 100 | 32 | 1 | 3 | 64 | 0.625 |
| panel_base_3of3 | host without learned library | majority of r1-r3 | Mamo.Complex | 211 | 111 | 7 | 7 | 86 | 1 |
| panel_base_3of3 | host without learned library | majority of r1-r3 | OptMATH-Bench | 166 | 83 | 11 | 14 | 58 | 0.69 |
| panel_base_3of3 | host without learned library | majority of r1-r3 | OptiBench | 605 | 404 | 12 | 34 | 155 | 0.001641 |
| panel_base_3of3 | host without learned library | majority of r1-r3 | all 1,100 | 1100 | 642 | 32 | 58 | 368 | 0.008046 |
| panel_base_2of3 | vote | majority of r1-r3 | ComplexOR | 18 | 12 | 0 | 0 | 6 | 1 |
| panel_base_2of3 | vote | majority of r1-r3 | IndustryOR | 100 | 34 | 3 | 2 | 61 | 1 |
| panel_base_2of3 | vote | majority of r1-r3 | Mamo.Complex | 211 | 109 | 8 | 7 | 87 | 1 |
| panel_base_2of3 | vote | majority of r1-r3 | OptMATH-Bench | 166 | 81 | 14 | 15 | 56 | 1 |
| panel_base_2of3 | vote | majority of r1-r3 | OptiBench | 605 | 391 | 20 | 12 | 182 | 0.2153 |
| panel_base_2of3 | vote | majority of r1-r3 | all 1,100 | 1100 | 627 | 45 | 36 | 392 | 0.3742 |
| panel_base_2of3 | host without learned library | majority of r1-r3 | ComplexOR | 18 | 12 | 0 | 0 | 6 | 1 |
| panel_base_2of3 | host without learned library | majority of r1-r3 | IndustryOR | 100 | 32 | 5 | 3 | 60 | 0.7266 |
| panel_base_2of3 | host without learned library | majority of r1-r3 | Mamo.Complex | 211 | 112 | 5 | 6 | 88 | 1 |
| panel_base_2of3 | host without learned library | majority of r1-r3 | OptMATH-Bench | 166 | 84 | 11 | 13 | 58 | 0.8388 |
| panel_base_2of3 | host without learned library | majority of r1-r3 | OptiBench | 605 | 402 | 9 | 36 | 158 | 6.575e-05 |
| panel_base_2of3 | host without learned library | majority of r1-r3 | all 1,100 | 1100 | 642 | 30 | 58 | 370 | 0.003747 |
| vote | host without learned library | majority of r1-r3 | ComplexOR | 18 | 12 | 0 | 0 | 6 | 1 |
| vote | host without learned library | majority of r1-r3 | IndustryOR | 100 | 34 | 2 | 1 | 63 | 1 |
| vote | host without learned library | majority of r1-r3 | Mamo.Complex | 211 | 110 | 6 | 8 | 87 | 0.7905 |
| vote | host without learned library | majority of r1-r3 | OptMATH-Bench | 166 | 80 | 16 | 17 | 53 | 1 |
| vote | host without learned library | majority of r1-r3 | OptiBench | 605 | 396 | 7 | 42 | 160 | 3.625e-07 |
| vote | host without learned library | majority of r1-r3 | all 1,100 | 1100 | 632 | 31 | 68 | 369 | 0.0002553 |
| released library (host); build data as described in the host README, no build record | host without learned library | released r1 against majority of r1-r3 | ComplexOR | 18 | 12 | 0 | 0 | 6 | 1 |
| released library (host); build data as described in the host README, no build record | host without learned library | released r1 against majority of r1-r3 | IndustryOR | 100 | 26 | 1 | 9 | 64 | 0.02148 |
| released library (host); build data as described in the host README, no build record | host without learned library | released r1 against majority of r1-r3 | Mamo.Complex | 211 | 108 | 12 | 10 | 81 | 0.8318 |
| released library (host); build data as described in the host README, no build record | host without learned library | released r1 against majority of r1-r3 | OptMATH-Bench | 166 | 81 | 20 | 16 | 49 | 0.6177 |
| released library (host); build data as described in the host README, no build record | host without learned library | released r1 against majority of r1-r3 | OptiBench | 605 | 404 | 30 | 34 | 137 | 0.708 |
| released library (host); build data as described in the host README, no build record | host without learned library | released r1 against majority of r1-r3 | all 1,100 | 1100 | 631 | 63 | 69 | 337 | 0.6636 |

Table 6c. Library size (files in the built library folder) and the share of wrong trajectories among those admitted (Table 5, host rule against the vault label, rows sample_6..300).

| configuration | library_files | admitted_trajectories | wrong_trajectories | wrong_share | wrong_share_se |
|---|---|---|---|---|---|
| panel_base_3of3 | 159 | 644 | 53 | 0.0823 | 0.0108 |
| panel_base_2of3 | 174 | 712 | 67 | 0.0941 | 0.0109 |
| vote | 186 | 758 | 94 | 0.1240 | 0.0120 |
| runsok | 211 | 862 | 193 | 0.2239 | 0.0142 |
| gt | 167 | 669 | 0 | 0.0000 | 0.0000 |
| host without learned library | 0 |  |  |  |  |
| released library (host); build data as described in the host README, no build record | 58 |  |  |  |  |
