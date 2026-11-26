Table 8. Single families against the panel, split by audit group. Ruler `round_aware` of scripts/score_eval.py; stream without sample_1..5 (295 problems), confirm 200 problems (ERROR verdicts count as not certified). Groups, from the three-family audit list only: (i) audited, class D, P, B, T or U (benchmark side); (ii) audited, class E or M (pipeline side); (iii) not audited, and panel_base_3of3 certifies a value that matches the label; (iv) every other problem. single_X certifies the value of family X's program at the stated instance (instance 0 of verdict_full.json) whenever one is returned. `+ check (B or C)` withdraws the certificate when family B or C raises flag_any in the data verification; unparsed or missing replies count as not flagged.

| set | ruler | rule | group | problems_in_group | certificates | label_matches | label_misses |
|---|---|---|---|---|---|---|---|
| stream (OptMATH-295) | round_aware | single_A | (i) audited, class D/P/B/T/U (benchmark side) | 34 | 34 | 0 | 34 |
| stream (OptMATH-295) | round_aware | single_A | (ii) audited, class E/M (pipeline side) | 1 | 1 | 0 | 1 |
| stream (OptMATH-295) | round_aware | single_A | (iii) not audited, panel_base_3of3 certifies a matching value | 208 | 208 | 208 | 0 |
| stream (OptMATH-295) | round_aware | single_A | (iv) all other problems | 52 | 22 | 6 | 16 |
| stream (OptMATH-295) | round_aware | single_A | all groups | 295 | 265 | 214 | 51 |
| stream (OptMATH-295) | round_aware | single_B | (i) audited, class D/P/B/T/U (benchmark side) | 34 | 34 | 0 | 34 |
| stream (OptMATH-295) | round_aware | single_B | (ii) audited, class E/M (pipeline side) | 1 | 1 | 0 | 1 |
| stream (OptMATH-295) | round_aware | single_B | (iii) not audited, panel_base_3of3 certifies a matching value | 208 | 208 | 208 | 0 |
| stream (OptMATH-295) | round_aware | single_B | (iv) all other problems | 52 | 29 | 20 | 9 |
| stream (OptMATH-295) | round_aware | single_B | all groups | 295 | 272 | 228 | 44 |
| stream (OptMATH-295) | round_aware | single_C | (i) audited, class D/P/B/T/U (benchmark side) | 34 | 34 | 0 | 34 |
| stream (OptMATH-295) | round_aware | single_C | (ii) audited, class E/M (pipeline side) | 1 | 1 | 0 | 1 |
| stream (OptMATH-295) | round_aware | single_C | (iii) not audited, panel_base_3of3 certifies a matching value | 208 | 208 | 208 | 0 |
| stream (OptMATH-295) | round_aware | single_C | (iv) all other problems | 52 | 42 | 19 | 23 |
| stream (OptMATH-295) | round_aware | single_C | all groups | 295 | 285 | 227 | 58 |
| stream (OptMATH-295) | round_aware | panel_base_2of3 | (i) audited, class D/P/B/T/U (benchmark side) | 34 | 34 | 0 | 34 |
| stream (OptMATH-295) | round_aware | panel_base_2of3 | (ii) audited, class E/M (pipeline side) | 1 | 1 | 0 | 1 |
| stream (OptMATH-295) | round_aware | panel_base_2of3 | (iii) not audited, panel_base_3of3 certifies a matching value | 208 | 208 | 208 | 0 |
| stream (OptMATH-295) | round_aware | panel_base_2of3 | (iv) all other problems | 52 | 30 | 20 | 10 |
| stream (OptMATH-295) | round_aware | panel_base_2of3 | all groups | 295 | 273 | 228 | 45 |
| stream (OptMATH-295) | round_aware | panel_base_3of3 | (i) audited, class D/P/B/T/U (benchmark side) | 34 | 34 | 0 | 34 |
| stream (OptMATH-295) | round_aware | panel_base_3of3 | (ii) audited, class E/M (pipeline side) | 1 | 1 | 0 | 1 |
| stream (OptMATH-295) | round_aware | panel_base_3of3 | (iii) not audited, panel_base_3of3 certifies a matching value | 208 | 208 | 208 | 0 |
| stream (OptMATH-295) | round_aware | panel_base_3of3 | (iv) all other problems | 52 | 0 | 0 | 0 |
| stream (OptMATH-295) | round_aware | panel_base_3of3 | all groups | 295 | 243 | 208 | 35 |
| stream (OptMATH-295) | round_aware | panel_base_3of3 + check (B or C) | (i) audited, class D/P/B/T/U (benchmark side) | 34 | 14 | 0 | 14 |
| stream (OptMATH-295) | round_aware | panel_base_3of3 + check (B or C) | (ii) audited, class E/M (pipeline side) | 1 | 0 | 0 | 0 |
| stream (OptMATH-295) | round_aware | panel_base_3of3 + check (B or C) | (iii) not audited, panel_base_3of3 certifies a matching value | 208 | 187 | 187 | 0 |
| stream (OptMATH-295) | round_aware | panel_base_3of3 + check (B or C) | (iv) all other problems | 52 | 0 | 0 | 0 |
| stream (OptMATH-295) | round_aware | panel_base_3of3 + check (B or C) | all groups | 295 | 201 | 187 | 14 |
| confirm (OptMATH-200) | round_aware | single_A | (i) audited, class D/P/B/T/U (benchmark side) | 19 | 19 | 0 | 19 |
| confirm (OptMATH-200) | round_aware | single_A | (ii) audited, class E/M (pipeline side) | 0 | 0 | 0 | 0 |
| confirm (OptMATH-200) | round_aware | single_A | (iii) not audited, panel_base_3of3 certifies a matching value | 149 | 149 | 149 | 0 |
| confirm (OptMATH-200) | round_aware | single_A | (iv) all other problems | 32 | 10 | 3 | 7 |
| confirm (OptMATH-200) | round_aware | single_A | all groups | 200 | 178 | 152 | 26 |
| confirm (OptMATH-200) | round_aware | single_B | (i) audited, class D/P/B/T/U (benchmark side) | 19 | 19 | 0 | 19 |
| confirm (OptMATH-200) | round_aware | single_B | (ii) audited, class E/M (pipeline side) | 0 | 0 | 0 | 0 |
| confirm (OptMATH-200) | round_aware | single_B | (iii) not audited, panel_base_3of3 certifies a matching value | 149 | 149 | 149 | 0 |
| confirm (OptMATH-200) | round_aware | single_B | (iv) all other problems | 32 | 21 | 17 | 4 |
| confirm (OptMATH-200) | round_aware | single_B | all groups | 200 | 189 | 166 | 23 |
| confirm (OptMATH-200) | round_aware | single_C | (i) audited, class D/P/B/T/U (benchmark side) | 19 | 19 | 0 | 19 |
| confirm (OptMATH-200) | round_aware | single_C | (ii) audited, class E/M (pipeline side) | 0 | 0 | 0 | 0 |
| confirm (OptMATH-200) | round_aware | single_C | (iii) not audited, panel_base_3of3 certifies a matching value | 149 | 149 | 149 | 0 |
| confirm (OptMATH-200) | round_aware | single_C | (iv) all other problems | 32 | 23 | 14 | 9 |
| confirm (OptMATH-200) | round_aware | single_C | all groups | 200 | 191 | 163 | 28 |
| confirm (OptMATH-200) | round_aware | panel_base_2of3 | (i) audited, class D/P/B/T/U (benchmark side) | 19 | 19 | 0 | 19 |
| confirm (OptMATH-200) | round_aware | panel_base_2of3 | (ii) audited, class E/M (pipeline side) | 0 | 0 | 0 | 0 |
| confirm (OptMATH-200) | round_aware | panel_base_2of3 | (iii) not audited, panel_base_3of3 certifies a matching value | 149 | 149 | 149 | 0 |
| confirm (OptMATH-200) | round_aware | panel_base_2of3 | (iv) all other problems | 32 | 16 | 14 | 2 |
| confirm (OptMATH-200) | round_aware | panel_base_2of3 | all groups | 200 | 184 | 163 | 21 |
| confirm (OptMATH-200) | round_aware | panel_base_3of3 | (i) audited, class D/P/B/T/U (benchmark side) | 19 | 19 | 0 | 19 |
| confirm (OptMATH-200) | round_aware | panel_base_3of3 | (ii) audited, class E/M (pipeline side) | 0 | 0 | 0 | 0 |
| confirm (OptMATH-200) | round_aware | panel_base_3of3 | (iii) not audited, panel_base_3of3 certifies a matching value | 149 | 149 | 149 | 0 |
| confirm (OptMATH-200) | round_aware | panel_base_3of3 | (iv) all other problems | 32 | 0 | 0 | 0 |
| confirm (OptMATH-200) | round_aware | panel_base_3of3 | all groups | 200 | 168 | 149 | 19 |
| confirm (OptMATH-200) | round_aware | panel_base_3of3 + check (B or C) | (i) audited, class D/P/B/T/U (benchmark side) | 19 | 11 | 0 | 11 |
| confirm (OptMATH-200) | round_aware | panel_base_3of3 + check (B or C) | (ii) audited, class E/M (pipeline side) | 0 | 0 | 0 | 0 |
| confirm (OptMATH-200) | round_aware | panel_base_3of3 + check (B or C) | (iii) not audited, panel_base_3of3 certifies a matching value | 149 | 135 | 135 | 0 |
| confirm (OptMATH-200) | round_aware | panel_base_3of3 + check (B or C) | (iv) all other problems | 32 | 0 | 0 | 0 |
| confirm (OptMATH-200) | round_aware | panel_base_3of3 + check (B or C) | all groups | 200 | 146 | 135 | 11 |

Table 8b. Errors of each single family and of panel_base_2of3 on group (iii) (problems whose label panel_base_3of3 confirms) and on group (iv). value_returned = problems of the group the rule certifies; label_misses = those whose value misses the label under `round_aware`.

| set | ruler | rule | group_iii_problems | group_iii_value_returned | group_iii_label_misses | group_iv_problems | group_iv_value_returned | group_iv_label_misses |
|---|---|---|---|---|---|---|---|---|
| stream (OptMATH-295) | round_aware | single_A | 208 | 208 | 0 | 52 | 22 | 16 |
| stream (OptMATH-295) | round_aware | single_B | 208 | 208 | 0 | 52 | 29 | 9 |
| stream (OptMATH-295) | round_aware | single_C | 208 | 208 | 0 | 52 | 42 | 23 |
| stream (OptMATH-295) | round_aware | panel_base_2of3 | 208 | 208 | 0 | 52 | 30 | 10 |
| confirm (OptMATH-200) | round_aware | single_A | 149 | 149 | 0 | 32 | 10 | 7 |
| confirm (OptMATH-200) | round_aware | single_B | 149 | 149 | 0 | 32 | 21 | 4 |
| confirm (OptMATH-200) | round_aware | single_C | 149 | 149 | 0 | 32 | 23 | 9 |
| confirm (OptMATH-200) | round_aware | panel_base_2of3 | 149 | 149 | 0 | 32 | 16 | 2 |
