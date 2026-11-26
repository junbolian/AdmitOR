Table h5. Certificates against the expert audit of Xiao et al. (2025) (cleaned IndustryOR and Mamo ComplexLP of the LLM4OR portal, `expert/SOURCE.md`). A problem is matched to the cleaned file by question text after lowercasing and collapsing whitespace; a problem without an exact match counts as removed by the audit. Label comparison with `round_aware` of scripts/score_eval.py. `match_new_label`: for problems whose label the audit changed, certificates that match the new label.

| benchmark | rule | expert_status | certificates | match_original_label | miss_original_label | match_new_label |
|---|---|---|---|---|---|---|
| IndustryOR | panel_base_3of3 | removed | 15 | 2 | 13 |  |
| IndustryOR | panel_base_3of3 | kept, same label | 30 | 25 | 5 |  |
| IndustryOR | panel_base_3of3 | kept, label changed | 1 | 0 | 1 | 0 |
| IndustryOR | panel_base_3of3 + check (B or C) | removed | 11 | 1 | 10 |  |
| IndustryOR | panel_base_3of3 + check (B or C) | kept, same label | 28 | 24 | 4 |  |
| IndustryOR | panel_base_3of3 + check (B or C) | kept, label changed | 1 | 0 | 1 | 0 |
| Mamo ComplexLP | panel_base_3of3 | removed | 64 | 21 | 43 |  |
| Mamo ComplexLP | panel_base_3of3 | kept, same label | 97 | 67 | 30 |  |
| Mamo ComplexLP | panel_base_3of3 | kept, label changed | 0 | 0 | 0 | 0 |
| Mamo ComplexLP | panel_base_3of3 + check (B or C) | removed | 42 | 16 | 26 |  |
| Mamo ComplexLP | panel_base_3of3 + check (B or C) | kept, same label | 87 | 57 | 30 |  |
| Mamo ComplexLP | panel_base_3of3 + check (B or C) | kept, label changed | 0 | 0 | 0 | 0 |
| pooled | panel_base_3of3 | removed | 79 | 23 | 56 |  |
| pooled | panel_base_3of3 | kept, same label | 127 | 92 | 35 |  |
| pooled | panel_base_3of3 | kept, label changed | 1 | 0 | 1 | 0 |
| pooled | panel_base_3of3 + check (B or C) | removed | 53 | 17 | 36 |  |
| pooled | panel_base_3of3 + check (B or C) | kept, same label | 115 | 81 | 34 |  |
| pooled | panel_base_3of3 + check (B or C) | kept, label changed | 1 | 0 | 1 | 0 |

Expert status of all problems:

| benchmark | problems | removed | kept, same label | kept, label changed |
|---|---:|---:|---:|---:|
| IndustryOR | 100 | 58 | 41 | 1 |
| Mamo ComplexLP | 211 | 100 | 111 | 0 |
| pooled | 311 | 158 | 152 | 1 |

Problems whose label the audit changed:

| benchmark | problem | original label | expert label | panel_base_3of3 value |
|---|---|---:|---:|---:|
| IndustryOR | `industryor_58` | 32.44 | 32.436 | 0.032435897435897434 |

Problems without an exact match in the cleaned file (158; all counted as removed). Best word 5-gram Jaccard against any cleaned record: maximum 0.3526.

| benchmark | problem | best 5-gram Jaccard |
|---|---|---:|
| IndustryOR | `industryor_12` | 0.0130 |
| IndustryOR | `industryor_14` | 0.0000 |
| IndustryOR | `industryor_15` | 0.0136 |
| IndustryOR | `industryor_19` | 0.0000 |
| IndustryOR | `industryor_23` | 0.0090 |
| IndustryOR | `industryor_27` | 0.0000 |
| IndustryOR | `industryor_28` | 0.0651 |
| IndustryOR | `industryor_29` | 0.0103 |
| IndustryOR | `industryor_30` | 0.0110 |
| IndustryOR | `industryor_32` | 0.0061 |
| IndustryOR | `industryor_33` | 0.0053 |
| IndustryOR | `industryor_34` | 0.0000 |
| IndustryOR | `industryor_36` | 0.0023 |
| IndustryOR | `industryor_37` | 0.0124 |
| IndustryOR | `industryor_38` | 0.0037 |
| IndustryOR | `industryor_39` | 0.0000 |
| IndustryOR | `industryor_41` | 0.0115 |
| IndustryOR | `industryor_42` | 0.0471 |
| IndustryOR | `industryor_44` | 0.0470 |
| IndustryOR | `industryor_45` | 0.0000 |
| IndustryOR | `industryor_47` | 0.0162 |
| IndustryOR | `industryor_48` | 0.0233 |
| IndustryOR | `industryor_49` | 0.0060 |
| IndustryOR | `industryor_50` | 0.0000 |
| IndustryOR | `industryor_51` | 0.0027 |
| IndustryOR | `industryor_52` | 0.0023 |
| IndustryOR | `industryor_53` | 0.1082 |
| IndustryOR | `industryor_54` | 0.0000 |
| IndustryOR | `industryor_55` | 0.0000 |
| IndustryOR | `industryor_56` | 0.0214 |
| IndustryOR | `industryor_57` | 0.0056 |
| IndustryOR | `industryor_60` | 0.0047 |
| IndustryOR | `industryor_62` | 0.0160 |
| IndustryOR | `industryor_63` | 0.0113 |
| IndustryOR | `industryor_64` | 0.0064 |
| IndustryOR | `industryor_65` | 0.0219 |
| IndustryOR | `industryor_66` | 0.0000 |
| IndustryOR | `industryor_67` | 0.0000 |
| IndustryOR | `industryor_73` | 0.0763 |
| IndustryOR | `industryor_74` | 0.0680 |
| IndustryOR | `industryor_75` | 0.0283 |
| IndustryOR | `industryor_77` | 0.0114 |
| IndustryOR | `industryor_78` | 0.0000 |
| IndustryOR | `industryor_80` | 0.0000 |
| IndustryOR | `industryor_81` | 0.0079 |
| IndustryOR | `industryor_82` | 0.0753 |
| IndustryOR | `industryor_83` | 0.0073 |
| IndustryOR | `industryor_84` | 0.0034 |
| IndustryOR | `industryor_87` | 0.0035 |
| IndustryOR | `industryor_89` | 0.0043 |
| IndustryOR | `industryor_90` | 0.0108 |
| IndustryOR | `industryor_93` | 0.0120 |
| IndustryOR | `industryor_94` | 0.0179 |
| IndustryOR | `industryor_96` | 0.0168 |
| IndustryOR | `industryor_97` | 0.0279 |
| IndustryOR | `industryor_98` | 0.0233 |
| IndustryOR | `industryor_99` | 0.0035 |
| IndustryOR | `industryor_100` | 0.0149 |
| Mamo ComplexLP | `mamo_complex_2` | 0.0150 |
| Mamo ComplexLP | `mamo_complex_3` | 0.1985 |
| Mamo ComplexLP | `mamo_complex_5` | 0.0637 |
| Mamo ComplexLP | `mamo_complex_8` | 0.0023 |
| Mamo ComplexLP | `mamo_complex_10` | 0.1096 |
| Mamo ComplexLP | `mamo_complex_11` | 0.0303 |
| Mamo ComplexLP | `mamo_complex_12` | 0.0138 |
| Mamo ComplexLP | `mamo_complex_16` | 0.0147 |
| Mamo ComplexLP | `mamo_complex_18` | 0.1123 |
| Mamo ComplexLP | `mamo_complex_20` | 0.1282 |
| Mamo ComplexLP | `mamo_complex_21` | 0.0470 |
| Mamo ComplexLP | `mamo_complex_22` | 0.0425 |
| Mamo ComplexLP | `mamo_complex_24` | 0.0409 |
| Mamo ComplexLP | `mamo_complex_26` | 0.0457 |
| Mamo ComplexLP | `mamo_complex_29` | 0.0610 |
| Mamo ComplexLP | `mamo_complex_31` | 0.1069 |
| Mamo ComplexLP | `mamo_complex_35` | 0.0112 |
| Mamo ComplexLP | `mamo_complex_36` | 0.0319 |
| Mamo ComplexLP | `mamo_complex_38` | 0.0130 |
| Mamo ComplexLP | `mamo_complex_39` | 0.0196 |
| Mamo ComplexLP | `mamo_complex_45` | 0.0625 |
| Mamo ComplexLP | `mamo_complex_48` | 0.0151 |
| Mamo ComplexLP | `mamo_complex_50` | 0.0000 |
| Mamo ComplexLP | `mamo_complex_51` | 0.0194 |
| Mamo ComplexLP | `mamo_complex_52` | 0.0143 |
| Mamo ComplexLP | `mamo_complex_54` | 0.0644 |
| Mamo ComplexLP | `mamo_complex_57` | 0.1499 |
| Mamo ComplexLP | `mamo_complex_58` | 0.0453 |
| Mamo ComplexLP | `mamo_complex_60` | 0.0727 |
| Mamo ComplexLP | `mamo_complex_61` | 0.0805 |
| Mamo ComplexLP | `mamo_complex_63` | 0.0258 |
| Mamo ComplexLP | `mamo_complex_65` | 0.0000 |
| Mamo ComplexLP | `mamo_complex_66` | 0.0652 |
| Mamo ComplexLP | `mamo_complex_69` | 0.3526 |
| Mamo ComplexLP | `mamo_complex_71` | 0.0801 |
| Mamo ComplexLP | `mamo_complex_73` | 0.1981 |
| Mamo ComplexLP | `mamo_complex_74` | 0.0030 |
| Mamo ComplexLP | `mamo_complex_78` | 0.0230 |
| Mamo ComplexLP | `mamo_complex_79` | 0.0198 |
| Mamo ComplexLP | `mamo_complex_80` | 0.0414 |
| Mamo ComplexLP | `mamo_complex_82` | 0.0277 |
| Mamo ComplexLP | `mamo_complex_83` | 0.0568 |
| Mamo ComplexLP | `mamo_complex_84` | 0.0633 |
| Mamo ComplexLP | `mamo_complex_87` | 0.0377 |
| Mamo ComplexLP | `mamo_complex_88` | 0.0000 |
| Mamo ComplexLP | `mamo_complex_91` | 0.0384 |
| Mamo ComplexLP | `mamo_complex_92` | 0.0139 |
| Mamo ComplexLP | `mamo_complex_93` | 0.2799 |
| Mamo ComplexLP | `mamo_complex_94` | 0.0000 |
| Mamo ComplexLP | `mamo_complex_96` | 0.0026 |
| Mamo ComplexLP | `mamo_complex_106` | 0.0451 |
| Mamo ComplexLP | `mamo_complex_112` | 0.0304 |
| Mamo ComplexLP | `mamo_complex_119` | 0.0586 |
| Mamo ComplexLP | `mamo_complex_125` | 0.0351 |
| Mamo ComplexLP | `mamo_complex_126` | 0.0460 |
| Mamo ComplexLP | `mamo_complex_127` | 0.0142 |
| Mamo ComplexLP | `mamo_complex_131` | 0.0209 |
| Mamo ComplexLP | `mamo_complex_132` | 0.0187 |
| Mamo ComplexLP | `mamo_complex_133` | 0.0148 |
| Mamo ComplexLP | `mamo_complex_134` | 0.0344 |
| Mamo ComplexLP | `mamo_complex_137` | 0.0226 |
| Mamo ComplexLP | `mamo_complex_139` | 0.0845 |
| Mamo ComplexLP | `mamo_complex_140` | 0.0316 |
| Mamo ComplexLP | `mamo_complex_141` | 0.1082 |
| Mamo ComplexLP | `mamo_complex_142` | 0.1562 |
| Mamo ComplexLP | `mamo_complex_144` | 0.0748 |
| Mamo ComplexLP | `mamo_complex_147` | 0.0895 |
| Mamo ComplexLP | `mamo_complex_148` | 0.0443 |
| Mamo ComplexLP | `mamo_complex_149` | 0.0621 |
| Mamo ComplexLP | `mamo_complex_150` | 0.0496 |
| Mamo ComplexLP | `mamo_complex_151` | 0.0458 |
| Mamo ComplexLP | `mamo_complex_152` | 0.0957 |
| Mamo ComplexLP | `mamo_complex_153` | 0.1102 |
| Mamo ComplexLP | `mamo_complex_154` | 0.0945 |
| Mamo ComplexLP | `mamo_complex_157` | 0.0789 |
| Mamo ComplexLP | `mamo_complex_160` | 0.0700 |
| Mamo ComplexLP | `mamo_complex_161` | 0.0319 |
| Mamo ComplexLP | `mamo_complex_165` | 0.0255 |
| Mamo ComplexLP | `mamo_complex_166` | 0.1054 |
| Mamo ComplexLP | `mamo_complex_169` | 0.0408 |
| Mamo ComplexLP | `mamo_complex_171` | 0.0567 |
| Mamo ComplexLP | `mamo_complex_173` | 0.0379 |
| Mamo ComplexLP | `mamo_complex_174` | 0.0271 |
| Mamo ComplexLP | `mamo_complex_176` | 0.0198 |
| Mamo ComplexLP | `mamo_complex_182` | 0.1318 |
| Mamo ComplexLP | `mamo_complex_183` | 0.1469 |
| Mamo ComplexLP | `mamo_complex_184` | 0.1042 |
| Mamo ComplexLP | `mamo_complex_187` | 0.1577 |
| Mamo ComplexLP | `mamo_complex_188` | 0.0541 |
| Mamo ComplexLP | `mamo_complex_190` | 0.1298 |
| Mamo ComplexLP | `mamo_complex_194` | 0.0184 |
| Mamo ComplexLP | `mamo_complex_195` | 0.0143 |
| Mamo ComplexLP | `mamo_complex_196` | 0.0135 |
| Mamo ComplexLP | `mamo_complex_198` | 0.0625 |
| Mamo ComplexLP | `mamo_complex_199` | 0.0150 |
| Mamo ComplexLP | `mamo_complex_204` | 0.0026 |
| Mamo ComplexLP | `mamo_complex_205` | 0.0018 |
| Mamo ComplexLP | `mamo_complex_208` | 0.0000 |
| Mamo ComplexLP | `mamo_complex_210` | 0.0000 |
| Mamo ComplexLP | `mamo_complex_211` | 0.0000 |
