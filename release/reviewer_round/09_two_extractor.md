# Task 9. Two- and three-extractor agreement

Zero-token analysis of the extractions produced by Task 9.2.
Extractors: pilot `deepseek-v3.2` (stored), `claude-sonnet-4-6`, `gpt-5.4`.
scipy available: True.

## Spend

88 calls, 0 errors, 156,594 tokens (Claude 83,067; GPT 73,527). Every response returned its own model name.

## Case groups

| Group | n | score 33.3 | 33.4 | 33.5 | 33.6 |
|---|---:|---:|---:|---:|---:|
| wrong | 22 | 0 | 3 | 3 | 16 |
| control | 22 | 1 | 2 | 1 | 18 |

## E = 2 (pilot and Claude)

| Level | class (d) + label error: any disagreement | control: any disagreement | Fisher p (two-sided) |
|---|---|---|---|
| L1 | 22 / 22 | 21 / 22 | 1.0000 |
| L2 | 18 / 22 | 20 / 22 | 0.6640 |
| L3 | 18 / 22 | 20 / 22 | 0.6640 |
| L4 | 21 / 22 | 22 / 22 | 1.0000 |

## E = 3 (all three pairs)

| Level | class (d) + label error: any disagreement | control: any disagreement | Fisher p (two-sided) |
|---|---|---|---|
| L1 | 22 / 22 | 22 / 22 | 1.0000 |
| L2 | 18 / 22 | 21 / 22 | 0.3449 |
| L3 | 18 / 22 | 21 / 22 | 0.3449 |
| L4 | 22 / 22 | 22 / 22 | 1.0000 |

## The five truncated-precision cases, reported separately

| Level | any disagreement among the 5 (E = 3) |
|---|---|
| L1 | 5 / 5 |
| L2 | 1 / 5 |
| L3 | 1 / 5 |
| L4 | 5 / 5 |

## Values the problem text does not print, on which all three extractors agree

| Group | cases | total such values |
|---|---:|---:|
| wrong | 0 | 0 |
| control | 0 | 0 |

Three-way alignment (the pilot aligned at L2 with both other extractors), required for the statistic above: 5 of 44 cases.

## Exploratory decomposition, not a preregistered rule

Each pair's L2 outcome split into (a) parameters in one specification with no
shape-and-value match in the other, (b) shape-matched parameters whose values
conflict, and (c) shape-matched parameters whose values agree.

| Group | Pair | (a) unmatched | (b) shape match, value conflict | (c) agreeing |
|---|---|---:|---:|---:|
| class (d) | P-C | 41 | 13 | 56 |
| class (d) | P-G | 92 | 12 | 45 |
| class (d) | C-G | 111 | 13 | 45 |
| label error | P-C | 22 | 0 | 6 |
| label error | P-G | 23 | 0 | 6 |
| label error | C-G | 5 | 0 | 21 |
| control | P-C | 176 | 3 | 45 |
| control | P-G | 345 | 2 | 28 |
| control | C-G | 243 | 5 | 48 |

Totals per group:

| Group | (a) | (b) | (c) |
|---|---:|---:|---:|
| class (d) | 244 | 38 | 146 |
| label error | 50 | 0 | 33 |
| control | 764 | 10 | 121 |
| all groups | 1058 | 48 | 300 |

Cases in which an array parameter with at least 4 entries in one
specification has no value-matched counterpart in another:

| Group | cases |
|---|---:|
| class (d) | 10 |
| label error | 1 |
| control | 9 |

