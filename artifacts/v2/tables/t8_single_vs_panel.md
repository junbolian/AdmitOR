Table 8. Single families against the panel, split by audit group. Ruler `round_aware` of scripts/score_eval.py; stream without sample_1..5 (295 problems), confirm 200 problems (ERROR verdicts count as not certified). Groups, from the three-family audit list only: (i) audited, class D, P, B, T or U (benchmark side); (ii) audited, class E or M (pipeline side); (iii) not audited, and panel_base_3of3 certifies a value that matches the label; (iv) every other problem. single_X certifies the value of family X's program at the stated instance (instance 0 of verdict_full.json) whenever one is returned. `+ check (B or C)` withdraws the certificate when family B or C raises flag_any in the data verification; unparsed or missing replies count as not flagged.

| set | ruler | rule | group | problems_in_group | certificates | label_matches | label_misses |
|---|---|---|---|---|---|---|---|
| stream (OptMATH-295) | round_aware | single_A | (i) audited, class D/P/B/T/U (benchmark side) | 34 | 34 | 0 | 34 |
| stream (OptMATH-295) | round_aware | single_A | (ii) audited, class E/M (pipeline side) | 1 | 1 | 0 | 1 |
| stream (OptMATH-295) | round_aware | single_A | (iii) not audited, panel_base_3of3 certifies a matching value | 207 | 207 | 207 | 0 |
| stream (OptMATH-295) | round_aware | single_A | (iv) all other problems | 53 | 22 | 6 | 16 |
| stream (OptMATH-295) | round_aware | single_A | all groups | 295 | 264 | 213 | 51 |
| stream (OptMATH-295) | round_aware | single_B | (i) audited, class D/P/B/T/U (benchmark side) | 34 | 34 | 0 | 34 |
| stream (OptMATH-295) | round_aware | single_B | (ii) audited, class E/M (pipeline side) | 1 | 1 | 0 | 1 |
| stream (OptMATH-295) | round_aware | single_B | (iii) not audited, panel_base_3of3 certifies a matching value | 207 | 207 | 207 | 0 |
| stream (OptMATH-295) | round_aware | single_B | (iv) all other problems | 53 | 29 | 20 | 9 |
| stream (OptMATH-295) | round_aware | single_B | all groups | 295 | 271 | 227 | 44 |
| stream (OptMATH-295) | round_aware | single_C | (i) audited, class D/P/B/T/U (benchmark side) | 34 | 34 | 0 | 34 |
| stream (OptMATH-295) | round_aware | single_C | (ii) audited, class E/M (pipeline side) | 1 | 1 | 0 | 1 |
| stream (OptMATH-295) | round_aware | single_C | (iii) not audited, panel_base_3of3 certifies a matching value | 207 | 207 | 207 | 0 |
| stream (OptMATH-295) | round_aware | single_C | (iv) all other problems | 53 | 42 | 19 | 23 |
| stream (OptMATH-295) | round_aware | single_C | all groups | 295 | 284 | 226 | 58 |
| stream (OptMATH-295) | round_aware | panel_base_2of3 | (i) audited, class D/P/B/T/U (benchmark side) | 34 | 34 | 0 | 34 |
| stream (OptMATH-295) | round_aware | panel_base_2of3 | (ii) audited, class E/M (pipeline side) | 1 | 1 | 0 | 1 |
| stream (OptMATH-295) | round_aware | panel_base_2of3 | (iii) not audited, panel_base_3of3 certifies a matching value | 207 | 207 | 207 | 0 |
| stream (OptMATH-295) | round_aware | panel_base_2of3 | (iv) all other problems | 53 | 30 | 20 | 10 |
| stream (OptMATH-295) | round_aware | panel_base_2of3 | all groups | 295 | 272 | 227 | 45 |
| stream (OptMATH-295) | round_aware | panel_base_3of3 | (i) audited, class D/P/B/T/U (benchmark side) | 34 | 34 | 0 | 34 |
| stream (OptMATH-295) | round_aware | panel_base_3of3 | (ii) audited, class E/M (pipeline side) | 1 | 1 | 0 | 1 |
| stream (OptMATH-295) | round_aware | panel_base_3of3 | (iii) not audited, panel_base_3of3 certifies a matching value | 207 | 207 | 207 | 0 |
| stream (OptMATH-295) | round_aware | panel_base_3of3 | (iv) all other problems | 53 | 0 | 0 | 0 |
| stream (OptMATH-295) | round_aware | panel_base_3of3 | all groups | 295 | 242 | 207 | 35 |
| stream (OptMATH-295) | round_aware | panel_base_3of3 + check (B or C) | (i) audited, class D/P/B/T/U (benchmark side) | 34 | 14 | 0 | 14 |
| stream (OptMATH-295) | round_aware | panel_base_3of3 + check (B or C) | (ii) audited, class E/M (pipeline side) | 1 | 0 | 0 | 0 |
| stream (OptMATH-295) | round_aware | panel_base_3of3 + check (B or C) | (iii) not audited, panel_base_3of3 certifies a matching value | 207 | 187 | 187 | 0 |
| stream (OptMATH-295) | round_aware | panel_base_3of3 + check (B or C) | (iv) all other problems | 53 | 0 | 0 | 0 |
| stream (OptMATH-295) | round_aware | panel_base_3of3 + check (B or C) | all groups | 295 | 201 | 187 | 14 |
| confirm (OptMATH-200) | round_aware | single_A | (i) audited, class D/P/B/T/U (benchmark side) | 18 | 18 | 0 | 18 |
| confirm (OptMATH-200) | round_aware | single_A | (ii) audited, class E/M (pipeline side) | 0 | 0 | 0 | 0 |
| confirm (OptMATH-200) | round_aware | single_A | (iii) not audited, panel_base_3of3 certifies a matching value | 145 | 145 | 145 | 0 |
| confirm (OptMATH-200) | round_aware | single_A | (iv) all other problems | 37 | 10 | 3 | 7 |
| confirm (OptMATH-200) | round_aware | single_A | all groups | 200 | 173 | 148 | 25 |
| confirm (OptMATH-200) | round_aware | single_B | (i) audited, class D/P/B/T/U (benchmark side) | 18 | 18 | 0 | 18 |
| confirm (OptMATH-200) | round_aware | single_B | (ii) audited, class E/M (pipeline side) | 0 | 0 | 0 | 0 |
| confirm (OptMATH-200) | round_aware | single_B | (iii) not audited, panel_base_3of3 certifies a matching value | 145 | 145 | 145 | 0 |
| confirm (OptMATH-200) | round_aware | single_B | (iv) all other problems | 37 | 22 | 17 | 5 |
| confirm (OptMATH-200) | round_aware | single_B | all groups | 200 | 185 | 162 | 23 |
| confirm (OptMATH-200) | round_aware | single_C | (i) audited, class D/P/B/T/U (benchmark side) | 18 | 18 | 0 | 18 |
| confirm (OptMATH-200) | round_aware | single_C | (ii) audited, class E/M (pipeline side) | 0 | 0 | 0 | 0 |
| confirm (OptMATH-200) | round_aware | single_C | (iii) not audited, panel_base_3of3 certifies a matching value | 145 | 145 | 145 | 0 |
| confirm (OptMATH-200) | round_aware | single_C | (iv) all other problems | 37 | 24 | 14 | 10 |
| confirm (OptMATH-200) | round_aware | single_C | all groups | 200 | 187 | 159 | 28 |
| confirm (OptMATH-200) | round_aware | panel_base_2of3 | (i) audited, class D/P/B/T/U (benchmark side) | 18 | 18 | 0 | 18 |
| confirm (OptMATH-200) | round_aware | panel_base_2of3 | (ii) audited, class E/M (pipeline side) | 0 | 0 | 0 | 0 |
| confirm (OptMATH-200) | round_aware | panel_base_2of3 | (iii) not audited, panel_base_3of3 certifies a matching value | 145 | 145 | 145 | 0 |
| confirm (OptMATH-200) | round_aware | panel_base_2of3 | (iv) all other problems | 37 | 17 | 14 | 3 |
| confirm (OptMATH-200) | round_aware | panel_base_2of3 | all groups | 200 | 180 | 159 | 21 |
| confirm (OptMATH-200) | round_aware | panel_base_3of3 | (i) audited, class D/P/B/T/U (benchmark side) | 18 | 18 | 0 | 18 |
| confirm (OptMATH-200) | round_aware | panel_base_3of3 | (ii) audited, class E/M (pipeline side) | 0 | 0 | 0 | 0 |
| confirm (OptMATH-200) | round_aware | panel_base_3of3 | (iii) not audited, panel_base_3of3 certifies a matching value | 145 | 145 | 145 | 0 |
| confirm (OptMATH-200) | round_aware | panel_base_3of3 | (iv) all other problems | 37 | 0 | 0 | 0 |
| confirm (OptMATH-200) | round_aware | panel_base_3of3 | all groups | 200 | 163 | 145 | 18 |
| confirm (OptMATH-200) | round_aware | panel_base_3of3 + check (B or C) | (i) audited, class D/P/B/T/U (benchmark side) | 18 | 12 | 0 | 12 |
| confirm (OptMATH-200) | round_aware | panel_base_3of3 + check (B or C) | (ii) audited, class E/M (pipeline side) | 0 | 0 | 0 | 0 |
| confirm (OptMATH-200) | round_aware | panel_base_3of3 + check (B or C) | (iii) not audited, panel_base_3of3 certifies a matching value | 145 | 131 | 131 | 0 |
| confirm (OptMATH-200) | round_aware | panel_base_3of3 + check (B or C) | (iv) all other problems | 37 | 0 | 0 | 0 |
| confirm (OptMATH-200) | round_aware | panel_base_3of3 + check (B or C) | all groups | 200 | 143 | 131 | 12 |

Table 8b. Errors of each single family and of panel_base_2of3 on group (iii) (problems whose label panel_base_3of3 confirms) and on group (iv). value_returned = problems of the group the rule certifies; label_misses = those whose value misses the label under `round_aware`.

| set | ruler | rule | group_iii_problems | group_iii_value_returned | group_iii_label_misses | group_iv_problems | group_iv_value_returned | group_iv_label_misses |
|---|---|---|---|---|---|---|---|---|
| stream (OptMATH-295) | round_aware | single_A | 207 | 207 | 0 | 53 | 22 | 16 |
| stream (OptMATH-295) | round_aware | single_B | 207 | 207 | 0 | 53 | 29 | 9 |
| stream (OptMATH-295) | round_aware | single_C | 207 | 207 | 0 | 53 | 42 | 23 |
| stream (OptMATH-295) | round_aware | panel_base_2of3 | 207 | 207 | 0 | 53 | 30 | 10 |
| confirm (OptMATH-200) | round_aware | single_A | 145 | 145 | 0 | 37 | 10 | 7 |
| confirm (OptMATH-200) | round_aware | single_B | 145 | 145 | 0 | 37 | 22 | 5 |
| confirm (OptMATH-200) | round_aware | single_C | 145 | 145 | 0 | 37 | 24 | 10 |
| confirm (OptMATH-200) | round_aware | panel_base_2of3 | 145 | 145 | 0 | 37 | 17 | 3 |
