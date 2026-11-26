# Withdrawal rules on the data-verification flags, one scoring rule (round_aware)

## OptMATH-295

### Before and after each rule (flag_any; round_aware)

| Certified by | Rule (withdrawn when) | Certificates | Misses | Precision | Withdrawn (of which misses) | Certificates after | Misses after | Precision after |
|---|---|---:|---:|---:|---|---:|---:|---:|
| panel_base_3of3 | B or C (rule of the paper) | 243 | 35 | 0.8560 | 42 (21) | 201 | 14 | 0.9303 |
| panel_base_3of3 | B and C | 243 | 35 | 0.8560 | 26 (20) | 217 | 15 | 0.9309 |
| panel_base_3of3 | C | 243 | 35 | 0.8560 | 33 (20) | 210 | 15 | 0.9286 |
| panel_base_3of3 | B | 243 | 35 | 0.8560 | 35 (21) | 208 | 14 | 0.9327 |
| panel_base_3of3 | A | 243 | 35 | 0.8560 | 33 (19) | 210 | 16 | 0.9238 |
| panel_base_3of3 | at least two of A, B, C | 243 | 35 | 0.8560 | 30 (20) | 213 | 15 | 0.9296 |
| panel_base_2of3 | B or C (rule of the paper) | 273 | 45 | 0.8352 | 50 (26) | 223 | 19 | 0.9148 |
| panel_base_2of3 | B and C | 273 | 45 | 0.8352 | 31 (25) | 242 | 20 | 0.9174 |
| panel_base_2of3 | C | 273 | 45 | 0.8352 | 40 (25) | 233 | 20 | 0.9142 |
| panel_base_2of3 | B | 273 | 45 | 0.8352 | 41 (26) | 232 | 19 | 0.9181 |
| panel_base_2of3 | A | 273 | 45 | 0.8352 | 38 (23) | 235 | 22 | 0.9064 |
| panel_base_2of3 | at least two of A, B, C | 273 | 45 | 0.8352 | 36 (25) | 237 | 20 | 0.9156 |

### 2x2, flag_mismatch (flagged & match / flagged & miss / not flagged & match / not flagged & miss)

| Certified by | n | B or C | B and C | C | B | A | at least two of A, B, C |
|---|---:|---|---|---|---|---|---|
| panel_base_3of3 | 243 | 4 / 3 / 204 / 32 | 1 / 0 / 207 / 35 | 4 / 1 / 204 / 34 | 1 / 2 / 207 / 33 | 2 / 2 / 206 / 33 | 1 / 1 / 207 / 34 |
| panel_base_2of3 | 273 | 4 / 3 / 224 / 42 | 1 / 0 / 227 / 45 | 4 / 1 / 224 / 44 | 1 / 2 / 227 / 43 | 2 / 3 / 226 / 42 | 1 / 1 / 227 / 44 |

### 2x2, flag_not_stated (flagged & match / flagged & miss / not flagged & match / not flagged & miss)

| Certified by | n | B or C | B and C | C | B | A | at least two of A, B, C |
|---|---:|---|---|---|---|---|---|
| panel_base_3of3 | 243 | 18 / 20 / 190 / 15 | 4 / 20 / 204 / 15 | 9 / 20 / 199 / 15 | 13 / 20 / 195 / 15 | 12 / 19 / 196 / 16 | 8 / 20 / 200 / 15 |
| panel_base_2of3 | 273 | 21 / 25 / 207 / 20 | 4 / 25 / 224 / 20 | 11 / 25 / 217 / 20 | 14 / 25 / 214 / 20 | 13 / 22 / 215 / 23 | 9 / 25 / 219 / 20 |

### 2x2, flag_any (flagged & match / flagged & miss / not flagged & match / not flagged & miss)

| Certified by | n | B or C | B and C | C | B | A | at least two of A, B, C |
|---|---:|---|---|---|---|---|---|
| panel_base_3of3 | 243 | 21 / 21 / 187 / 14 | 6 / 20 / 202 / 15 | 13 / 20 / 195 / 15 | 14 / 21 / 194 / 14 | 14 / 19 / 194 / 16 | 10 / 20 / 198 / 15 |
| panel_base_2of3 | 273 | 24 / 26 / 204 / 19 | 6 / 25 / 222 / 20 | 15 / 25 / 213 / 20 | 15 / 26 / 213 / 19 | 15 / 23 / 213 / 22 | 11 / 25 / 217 / 20 |

Replies not ok (unparsed or API error) per family: C 0, A 0, B 0; replies per family: C 295, A 295, B 273.

## OptMATH-200

### Before and after each rule (flag_any; round_aware)

| Certified by | Rule (withdrawn when) | Certificates | Misses | Precision | Withdrawn (of which misses) | Certificates after | Misses after | Precision after |
|---|---|---:|---:|---:|---|---:|---:|---:|
| panel_base_3of3 | B or C (rule of the paper) | 168 | 19 | 0.8869 | 22 (8) | 146 | 11 | 0.9247 |
| panel_base_3of3 | B and C | 168 | 19 | 0.8869 | 11 (7) | 157 | 12 | 0.9236 |
| panel_base_3of3 | C | 168 | 19 | 0.8869 | 17 (8) | 151 | 11 | 0.9272 |
| panel_base_3of3 | B | 168 | 19 | 0.8869 | 16 (7) | 152 | 12 | 0.9211 |
| panel_base_3of3 | A | 168 | 19 | 0.8869 | 19 (7) | 149 | 12 | 0.9195 |
| panel_base_3of3 | at least two of A, B, C | 168 | 19 | 0.8869 | 14 (7) | 154 | 12 | 0.9221 |
| panel_base_2of3 | B or C (rule of the paper) | 184 | 21 | 0.8859 | 28 (10) | 156 | 11 | 0.9295 |
| panel_base_2of3 | B and C | 184 | 21 | 0.8859 | 12 (8) | 172 | 13 | 0.9244 |
| panel_base_2of3 | C | 184 | 21 | 0.8859 | 20 (9) | 164 | 12 | 0.9268 |
| panel_base_2of3 | B | 184 | 21 | 0.8859 | 20 (9) | 164 | 12 | 0.9268 |
| panel_base_2of3 | A | 184 | 21 | 0.8859 | 22 (8) | 162 | 13 | 0.9198 |
| panel_base_2of3 | at least two of A, B, C | 184 | 21 | 0.8859 | 17 (8) | 167 | 13 | 0.9222 |

### 2x2, flag_mismatch (flagged & match / flagged & miss / not flagged & match / not flagged & miss)

| Certified by | n | B or C | B and C | C | B | A | at least two of A, B, C |
|---|---:|---|---|---|---|---|---|
| panel_base_3of3 | 168 | 1 / 1 / 148 / 18 | 0 / 0 / 149 / 19 | 1 / 1 / 148 / 18 | 0 / 0 / 149 / 19 | 0 / 1 / 149 / 18 | 0 / 0 / 149 / 19 |
| panel_base_2of3 | 184 | 1 / 1 / 162 / 20 | 0 / 0 / 163 / 21 | 1 / 1 / 162 / 20 | 0 / 0 / 163 / 21 | 0 / 1 / 163 / 20 | 0 / 0 / 163 / 21 |

### 2x2, flag_not_stated (flagged & match / flagged & miss / not flagged & match / not flagged & miss)

| Certified by | n | B or C | B and C | C | B | A | at least two of A, B, C |
|---|---:|---|---|---|---|---|---|
| panel_base_3of3 | 168 | 13 / 7 / 136 / 12 | 4 / 7 / 145 / 12 | 8 / 7 / 141 / 12 | 9 / 7 / 140 / 12 | 12 / 7 / 137 / 12 | 7 / 7 / 142 / 12 |
| panel_base_2of3 | 184 | 17 / 9 / 146 / 12 | 4 / 8 / 159 / 13 | 10 / 8 / 153 / 13 | 11 / 9 / 152 / 12 | 14 / 8 / 149 / 13 | 9 / 8 / 154 / 13 |

### 2x2, flag_any (flagged & match / flagged & miss / not flagged & match / not flagged & miss)

| Certified by | n | B or C | B and C | C | B | A | at least two of A, B, C |
|---|---:|---|---|---|---|---|---|
| panel_base_3of3 | 168 | 14 / 8 / 135 / 11 | 4 / 7 / 145 / 12 | 9 / 8 / 140 / 11 | 9 / 7 / 140 / 12 | 12 / 7 / 137 / 12 | 7 / 7 / 142 / 12 |
| panel_base_2of3 | 184 | 18 / 10 / 145 / 11 | 4 / 8 / 159 / 13 | 11 / 9 / 152 / 12 | 11 / 9 / 152 / 12 | 14 / 8 / 149 / 13 | 9 / 8 / 154 / 13 |

Replies not ok (unparsed or API error) per family: C 0, A 0, B 0; replies per family: C 200, A 200, B 200.

