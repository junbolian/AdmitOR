Table h1. Certification rules on the human-written benchmarks, scored with `round_aware` of scripts/score_eval.py. Coverage = certificates / problems (an ERROR counts as not certified). Binomial standard errors. single_X: family X's program value at the stated instance; gate_tau: three-family agreement on resampled instances (tau 33.4); `+ check`: withdrawn when the named families raise flag_any in the data verification (unparsed replies count as not flagged).

| benchmark | rule | problems | certificates | coverage | coverage_se | label_matches | label_misses | precision | precision_se |
|---|---|---|---|---|---|---|---|---|---|
| IndustryOR | single_A | 100 | 79 | 0.7900 | 0.0407 | 32 | 47 | 0.4051 | 0.0552 |
| IndustryOR | single_B | 100 | 86 | 0.8600 | 0.0347 | 35 | 51 | 0.4070 | 0.0530 |
| IndustryOR | single_C | 100 | 87 | 0.8700 | 0.0336 | 38 | 49 | 0.4368 | 0.0532 |
| IndustryOR | panel_base_2of3 | 100 | 73 | 0.7300 | 0.0444 | 38 | 35 | 0.5205 | 0.0585 |
| IndustryOR | panel_base_3of3 | 100 | 46 | 0.4600 | 0.0498 | 27 | 19 | 0.5870 | 0.0726 |
| IndustryOR | gate_tau | 100 | 29 | 0.2900 | 0.0454 | 17 | 12 | 0.5862 | 0.0915 |
| IndustryOR | panel_base_2of3 + check (B or C) | 100 | 62 | 0.6200 | 0.0485 | 33 | 29 | 0.5323 | 0.0634 |
| IndustryOR | panel_base_3of3 + check (B or C) | 100 | 40 | 0.4000 | 0.0490 | 25 | 15 | 0.6250 | 0.0765 |
| IndustryOR | panel_base_3of3 + check (B and C) | 100 | 43 | 0.4300 | 0.0495 | 27 | 16 | 0.6279 | 0.0737 |
| Mamo ComplexLP | single_A | 211 | 190 | 0.9005 | 0.0206 | 98 | 92 | 0.5158 | 0.0363 |
| Mamo ComplexLP | single_B | 211 | 203 | 0.9621 | 0.0131 | 121 | 82 | 0.5961 | 0.0344 |
| Mamo ComplexLP | single_C | 211 | 204 | 0.9668 | 0.0123 | 109 | 95 | 0.5343 | 0.0349 |
| Mamo ComplexLP | panel_base_2of3 | 211 | 196 | 0.9289 | 0.0177 | 114 | 82 | 0.5816 | 0.0352 |
| Mamo ComplexLP | panel_base_3of3 | 211 | 161 | 0.7630 | 0.0293 | 88 | 73 | 0.5466 | 0.0392 |
| Mamo ComplexLP | gate_tau | 211 | 145 | 0.6872 | 0.0319 | 76 | 69 | 0.5241 | 0.0415 |
| Mamo ComplexLP | panel_base_2of3 + check (B or C) | 211 | 154 | 0.7299 | 0.0306 | 91 | 63 | 0.5909 | 0.0396 |
| Mamo ComplexLP | panel_base_3of3 + check (B or C) | 211 | 129 | 0.6114 | 0.0336 | 73 | 56 | 0.5659 | 0.0436 |
| Mamo ComplexLP | panel_base_3of3 + check (B and C) | 211 | 146 | 0.6919 | 0.0318 | 84 | 62 | 0.5753 | 0.0409 |
| pooled | single_A | 311 | 269 | 0.8650 | 0.0194 | 130 | 139 | 0.4833 | 0.0305 |
| pooled | single_B | 311 | 289 | 0.9293 | 0.0145 | 156 | 133 | 0.5398 | 0.0293 |
| pooled | single_C | 311 | 291 | 0.9357 | 0.0139 | 147 | 144 | 0.5052 | 0.0293 |
| pooled | panel_base_2of3 | 311 | 269 | 0.8650 | 0.0194 | 152 | 117 | 0.5651 | 0.0302 |
| pooled | panel_base_3of3 | 311 | 207 | 0.6656 | 0.0268 | 115 | 92 | 0.5556 | 0.0345 |
| pooled | gate_tau | 311 | 174 | 0.5595 | 0.0282 | 93 | 81 | 0.5345 | 0.0378 |
| pooled | panel_base_2of3 + check (B or C) | 311 | 216 | 0.6945 | 0.0261 | 124 | 92 | 0.5741 | 0.0336 |
| pooled | panel_base_3of3 + check (B or C) | 311 | 169 | 0.5434 | 0.0282 | 98 | 71 | 0.5799 | 0.0380 |
| pooled | panel_base_3of3 + check (B and C) | 311 | 189 | 0.6077 | 0.0277 | 111 | 78 | 0.5873 | 0.0358 |
