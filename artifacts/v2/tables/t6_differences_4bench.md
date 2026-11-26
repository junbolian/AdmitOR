# Differences in overall accuracy, four benchmarks (1,082 items)

Overall accuracy = mean over the passes of the accuracy on the 1,082 items (one pass where there is one).

| Configuration | Overall accuracy (%) |
|---|---:|
| host without learned library | 63.22 |
| panel_base_3of3 | 59.70 |
| panel_base_2of3 | 59.64 |
| vote | 58.81 |
| runsok | 58.04 |
| gt | 59.33 |
| released library (host); build data as described in the host README, no build record | 63.03 |

Largest difference between two of the five libraries: 1.66 points (panel_base_3of3 against runsok).
Library minus host without a learned library: smallest -5.18 points (runsok), largest -3.51 points (panel_base_3of3).
