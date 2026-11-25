# Withdrawal rules on the data-verification flags, one scoring rule (round_aware)

## OptMATH-295

### Before and after each rule (flag_any; round_aware)

| Certified by | Rule (withdrawn when) | Certificates | Misses | Precision | Withdrawn (of which misses) | Certificates after | Misses after | Precision after |
|---|---|---:|---:|---:|---|---:|---:|---:|
| panel_base_3of3 | B or C (rule of the paper) | 242 | 35 | 0.8554 | 41 (21) | 201 | 14 | 0.9303 |
| panel_base_3of3 | B and C | 242 | 35 | 0.8554 | 26 (20) | 216 | 15 | 0.9306 |
| panel_base_3of3 | C | 242 | 35 | 0.8554 | 32 (20) | 210 | 15 | 0.9286 |
| panel_base_3of3 | B | 242 | 35 | 0.8554 | 35 (21) | 207 | 14 | 0.9324 |
| panel_base_3of3 | A | 242 | 35 | 0.8554 | 33 (19) | 209 | 16 | 0.9234 |
| panel_base_3of3 | at least two of A, B, C | 242 | 35 | 0.8554 | 30 (20) | 212 | 15 | 0.9292 |
| panel_base_2of3 | B or C (rule of the paper) | 272 | 45 | 0.8346 | 49 (26) | 223 | 19 | 0.9148 |
| panel_base_2of3 | B and C | 272 | 45 | 0.8346 | 31 (25) | 241 | 20 | 0.9170 |
| panel_base_2of3 | C | 272 | 45 | 0.8346 | 39 (25) | 233 | 20 | 0.9142 |
| panel_base_2of3 | B | 272 | 45 | 0.8346 | 41 (26) | 231 | 19 | 0.9177 |
| panel_base_2of3 | A | 272 | 45 | 0.8346 | 38 (23) | 234 | 22 | 0.9060 |
| panel_base_2of3 | at least two of A, B, C | 272 | 45 | 0.8346 | 36 (25) | 236 | 20 | 0.9153 |

### 2x2, flag_mismatch (flagged & match / flagged & miss / not flagged & match / not flagged & miss)

| Certified by | n | B or C | B and C | C | B | A | at least two of A, B, C |
|---|---:|---|---|---|---|---|---|
| panel_base_3of3 | 242 | 3 / 3 / 204 / 32 | 1 / 0 / 206 / 35 | 3 / 1 / 204 / 34 | 1 / 2 / 206 / 33 | 2 / 2 / 205 / 33 | 1 / 1 / 206 / 34 |
| panel_base_2of3 | 272 | 3 / 3 / 224 / 42 | 1 / 0 / 226 / 45 | 3 / 1 / 224 / 44 | 1 / 2 / 226 / 43 | 2 / 3 / 225 / 42 | 1 / 1 / 226 / 44 |

### 2x2, flag_not_stated (flagged & match / flagged & miss / not flagged & match / not flagged & miss)

| Certified by | n | B or C | B and C | C | B | A | at least two of A, B, C |
|---|---:|---|---|---|---|---|---|
| panel_base_3of3 | 242 | 18 / 20 / 189 / 15 | 4 / 20 / 203 / 15 | 9 / 20 / 198 / 15 | 13 / 20 / 194 / 15 | 12 / 19 / 195 / 16 | 8 / 20 / 199 / 15 |
| panel_base_2of3 | 272 | 21 / 25 / 206 / 20 | 4 / 25 / 223 / 20 | 11 / 25 / 216 / 20 | 14 / 25 / 213 / 20 | 13 / 22 / 214 / 23 | 9 / 25 / 218 / 20 |

### 2x2, flag_any (flagged & match / flagged & miss / not flagged & match / not flagged & miss)

| Certified by | n | B or C | B and C | C | B | A | at least two of A, B, C |
|---|---:|---|---|---|---|---|---|
| panel_base_3of3 | 242 | 20 / 21 / 187 / 14 | 6 / 20 / 201 / 15 | 12 / 20 / 195 / 15 | 14 / 21 / 193 / 14 | 14 / 19 / 193 / 16 | 10 / 20 / 197 / 15 |
| panel_base_2of3 | 272 | 23 / 26 / 204 / 19 | 6 / 25 / 221 / 20 | 14 / 25 / 213 / 20 | 15 / 26 / 212 / 19 | 15 / 23 / 212 / 22 | 11 / 25 / 216 / 20 |

Replies not ok (unparsed or API error) per family: C 2, A 0, B 0; replies per family: C 294, A 294, B 272.

## OptMATH-200

### Before and after each rule (flag_any; round_aware)

| Certified by | Rule (withdrawn when) | Certificates | Misses | Precision | Withdrawn (of which misses) | Certificates after | Misses after | Precision after |
|---|---|---:|---:|---:|---|---:|---:|---:|
| panel_base_3of3 | B or C (rule of the paper) | 163 | 18 | 0.8896 | 20 (6) | 143 | 12 | 0.9161 |
| panel_base_3of3 | B and C | 163 | 18 | 0.8896 | 10 (6) | 153 | 12 | 0.9216 |
| panel_base_3of3 | C | 163 | 18 | 0.8896 | 15 (6) | 148 | 12 | 0.9189 |
| panel_base_3of3 | B | 163 | 18 | 0.8896 | 15 (6) | 148 | 12 | 0.9189 |
| panel_base_3of3 | A | 163 | 18 | 0.8896 | 18 (6) | 145 | 12 | 0.9172 |
| panel_base_3of3 | at least two of A, B, C | 163 | 18 | 0.8896 | 13 (6) | 150 | 12 | 0.9200 |
| panel_base_2of3 | B or C (rule of the paper) | 180 | 21 | 0.8833 | 27 (9) | 153 | 12 | 0.9216 |
| panel_base_2of3 | B and C | 180 | 21 | 0.8833 | 12 (8) | 168 | 13 | 0.9226 |
| panel_base_2of3 | C | 180 | 21 | 0.8833 | 19 (8) | 161 | 13 | 0.9193 |
| panel_base_2of3 | B | 180 | 21 | 0.8833 | 20 (9) | 160 | 12 | 0.9250 |
| panel_base_2of3 | A | 180 | 21 | 0.8833 | 22 (8) | 158 | 13 | 0.9177 |
| panel_base_2of3 | at least two of A, B, C | 180 | 21 | 0.8833 | 17 (8) | 163 | 13 | 0.9202 |

### 2x2, flag_mismatch (flagged & match / flagged & miss / not flagged & match / not flagged & miss)

| Certified by | n | B or C | B and C | C | B | A | at least two of A, B, C |
|---|---:|---|---|---|---|---|---|
| panel_base_3of3 | 163 | 1 / 0 / 144 / 18 | 0 / 0 / 145 / 18 | 1 / 0 / 144 / 18 | 0 / 0 / 145 / 18 | 0 / 0 / 145 / 18 | 0 / 0 / 145 / 18 |
| panel_base_2of3 | 180 | 1 / 0 / 158 / 21 | 0 / 0 / 159 / 21 | 1 / 0 / 158 / 21 | 0 / 0 / 159 / 21 | 0 / 1 / 159 / 20 | 0 / 0 / 159 / 21 |

### 2x2, flag_not_stated (flagged & match / flagged & miss / not flagged & match / not flagged & miss)

| Certified by | n | B or C | B and C | C | B | A | at least two of A, B, C |
|---|---:|---|---|---|---|---|---|
| panel_base_3of3 | 163 | 13 / 6 / 132 / 12 | 4 / 6 / 141 / 12 | 8 / 6 / 137 / 12 | 9 / 6 / 136 / 12 | 12 / 6 / 133 / 12 | 7 / 6 / 138 / 12 |
| panel_base_2of3 | 180 | 17 / 9 / 142 / 12 | 4 / 8 / 155 / 13 | 10 / 8 / 149 / 13 | 11 / 9 / 148 / 12 | 14 / 8 / 145 / 13 | 9 / 8 / 150 / 13 |

### 2x2, flag_any (flagged & match / flagged & miss / not flagged & match / not flagged & miss)

| Certified by | n | B or C | B and C | C | B | A | at least two of A, B, C |
|---|---:|---|---|---|---|---|---|
| panel_base_3of3 | 163 | 14 / 6 / 131 / 12 | 4 / 6 / 141 / 12 | 9 / 6 / 136 / 12 | 9 / 6 / 136 / 12 | 12 / 6 / 133 / 12 | 7 / 6 / 138 / 12 |
| panel_base_2of3 | 180 | 18 / 9 / 141 / 12 | 4 / 8 / 155 / 13 | 11 / 8 / 148 / 13 | 11 / 9 / 148 / 12 | 14 / 8 / 145 / 13 | 9 / 8 / 150 / 13 |

Replies not ok (unparsed or API error) per family: C 3, A 0, B 0; replies per family: C 196, A 196, B 196.

