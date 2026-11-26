# Audit of the label misses on human-written texts

Three-family certificates (`panel_base_3of3`) that miss the label on IndustryOR and Mamo ComplexLP, original releases (`artifacts/v2/humanbench/`) and corrected releases of the OptiMind authors (`artifacts/v2/optimind/`). Expert status refers to the cleaned files of Xiao et al. (2025): `removed` means the problem is not in the cleaned file. *Withdrawn*: withdrawn by data verification (family B or C raises a flag).

Classes: D and E are data errors (decisive values not in the text; extraction differs from the text). B: the text is complete and our re-solve reproduces the certified value, so the label is not the optimum of the stated problem. T: the label is the optimum of an instance that differs from the text in a stated rule, value, or unit. *Integrality not stated*: the certificate is the optimum of a program with continuous quantities, the label is the optimum of the same program with integer quantities, and the text does not state integrality (class U of the paper). No miss is a shared modeling error (class M).

## Original releases (91 misses among 204 certificates)

| Problem | Expert status | Label | Certified | Class | Withdrawn | Evidence |
|---|---|---:|---:|---|---|---|
| `industryor_12` | removed | 734 | 715 | Other text defect (T, U) | no | Text incomplete, ambiguous, or label stated in another unit or quantity; the expert audit removes the problem. |
| `industryor_21` | kept | 43700 | 43200 | B | no | Text complete. Exact re-solve with substitution by larger containers gives 43,200 (certified); the label 43,700 is the cost of producing every container type without substitution. |
| `industryor_27` | removed | 16 | 18.9857 | Other text defect (T, U) | no | Text incomplete, ambiguous, or label stated in another unit or quantity; the expert audit removes the problem. |
| `industryor_30` | removed | 5004 | 115000 | B | no | The critical path alone costs more than the label 5,004. |
| `industryor_39` | removed | 146 | 153.333 | Other text defect (T, U) | no | Text incomplete, ambiguous, or label stated in another unit or quantity; the expert audit removes the problem. |
| `industryor_46` | kept | 8505 | 10750 | Integrality not stated | no | Same problem as industryor_85. Label 8,505 is the integer optimum without storage cost on the 150 units required at the end of the horizon. |
| `industryor_56` | removed | 1000 | 0 | D | yes | Data are stated symbolically (a_i, d_A); the extraction sets them to values that the text does not give. Withdrawn by verification. |
| `industryor_58` | label changed | 32.44 | 0.0324359 | T | no | Contents are given per gram and prices per kilogram. With the stated units the optimum is 0.0324 (certified); the label 32.44, kept with the value 32.436 by the expert audit, ignores the conversion. |
| `industryor_59` | kept | 1146.6 | 430.55 | E | yes | The table of the text has shifted columns; the extraction sets the full-load cost of machine B2 to 7,000. With the textbook alignment the optimum is 1,146.57, which is the label. Withdrawn by verification. |
| `industryor_64` | removed | 0 | 7 | B | yes | A label of zero containers is infeasible for the stated shipments. |
| `industryor_68` | kept | 9337440 | 1.035e+07 | B | no | Text complete. Exact re-solve gives the certified value (10,350,000; 10,349,920 with integer variables); no reading that we tried reproduces the label 9,337,440. |
| `industryor_74` | removed | 365 | 4000 | B | no | The stated demand alone costs at least 4,000; label 365. |
| `industryor_78` | removed | 0 | 1000 | B | no | The item values sum to an odd number of thousands, so a difference of zero (the label) is impossible. |
| `industryor_80` | removed | 7.1 | 14.1 | B | no | The first batch alone takes longer than the label 7.1 hours. |
| `industryor_82` | removed | 530 | 4240 | Other text defect (T, U) | no | Text incomplete, ambiguous, or label stated in another unit or quantity; the expert audit removes the problem. |
| `industryor_84` | removed | 4848 | 6515 | Other text defect (T, U) | yes | Text incomplete, ambiguous, or label stated in another unit or quantity; the expert audit removes the problem. |
| `industryor_85` | kept | 10755 | 10750 | Integrality not stated | no | Label 10,755 is the integer optimum of the certified program (10,750). The same problem appears as industryor_46 with another label. |
| `industryor_90` | removed | -1900 | 1500 | B | no | Producing nothing gives a profit of zero, above the label -1,900. |
| `industryor_93` | removed | 20 | 53 | B | no | The stated lengths require at least 51 rods; label 20. |
| `mamo_complex_1` | kept | 18 | 17.3977 | Integrality not stated | no | The label is the optimum of the same program with integer quantities; the text does not state integrality. |
| `mamo_complex_4` | kept | 15 | 14.5 | Integrality not stated | no | The label is the optimum of the same program with integer quantities; the text does not state integrality. |
| `mamo_complex_5` | removed | 165 | 237 | B | no | Enumeration of all tours over the extracted costs, which all occur in the text, gives the certified value; the label lies below every tour. |
| `mamo_complex_7` | kept | 30 | 28.9939 | Integrality not stated | no | The label is the optimum of the same program with integer quantities; the text does not state integrality. |
| `mamo_complex_9` | kept | 14 | 13.4133 | Integrality not stated | no | The label is the optimum of the same program with integer quantities; the text does not state integrality. |
| `mamo_complex_10` | removed | 138 | 153 | B | no | Enumeration of all tours over the extracted costs, which all occur in the text, gives the certified value; the label lies below every tour. |
| `mamo_complex_11` | removed | 18 | 16.4444 | Other text defect (T, U) | no | Text incomplete, ambiguous, or label stated in another unit or quantity; the expert audit removes the problem. |
| `mamo_complex_12` | removed | 9 | 11 | B | no | Shortest path computed by hand from the text gives 11 (certified); label 9. |
| `mamo_complex_20` | removed | 242 | 270 | B | no | Enumeration of all tours over the extracted costs, which all occur in the text, gives the certified value; the label lies below every tour. |
| `mamo_complex_22` | removed | 138 | 160 | B | yes | Enumeration of all tours over the extracted costs, which all occur in the text, gives the certified value; the label lies below every tour. |
| `mamo_complex_24` | removed | 142 | 165 | B | no | Enumeration of all tours over the extracted costs, which all occur in the text, gives the certified value; the label lies below every tour. |
| `mamo_complex_27` | kept | 22 | 19.7052 | Integrality not stated | no | The label is the optimum of the same program with integer quantities; the text does not state integrality. |
| `mamo_complex_31` | removed | 204 | 229 | B | no | Enumeration of all tours over the extracted costs, which all occur in the text, gives the certified value; the label lies below every tour. |
| `mamo_complex_34` | kept | 31 | 29.9829 | Integrality not stated | no | The label is the optimum of the same program with integer quantities; the text does not state integrality. |
| `mamo_complex_47` | kept | 18 | 17.2467 | Integrality not stated | no | The label is the optimum of the same program with integer quantities; the text does not state integrality. |
| `mamo_complex_49` | kept | 24 | 23.045 | Integrality not stated | no | The label is the optimum of the same program with integer quantities; the text does not state integrality. |
| `mamo_complex_53` | kept | 29 | 27.0292 | Integrality not stated | no | The label is the optimum of the same program with integer quantities; the text does not state integrality. |
| `mamo_complex_56` | kept | 47 | 45.5625 | Integrality not stated | no | The label is the optimum of the same program with integer quantities; the text does not state integrality. |
| `mamo_complex_57` | removed | 206 | 211 | B | no | Enumeration of all tours over the extracted costs, which all occur in the text, gives the certified value; the label lies below every tour. |
| `mamo_complex_58` | removed | 192 | 198 | B | yes | Enumeration of all tours over the extracted costs, which all occur in the text, gives the certified value; the label lies below every tour. |
| `mamo_complex_61` | removed | 148 | 249 | B | yes | Enumeration of all tours over the extracted costs, which all occur in the text, gives the certified value; the label lies below every tour. |
| `mamo_complex_66` | removed | 194 | 213 | B | no | Enumeration of all tours over the extracted costs, which all occur in the text, gives the certified value; the label lies below every tour. |
| `mamo_complex_73` | removed | 587428 | 580735 | D | yes | Values given by example and "and so on". Withdrawn by verification. |
| `mamo_complex_78` | removed | 242 | 269 | B | no | Enumeration of all tours over the extracted costs, which all occur in the text, gives the certified value; the label lies below every tour. |
| `mamo_complex_84` | removed | 206 | 232 | B | no | Enumeration of all tours over the extracted costs, which all occur in the text, gives the certified value; the label lies below every tour. |
| `mamo_complex_85` | kept | 14 | 13.1196 | Integrality not stated | no | The label is the optimum of the same program with integer quantities; the text does not state integrality. |
| `mamo_complex_87` | removed | 134 | 175 | B | no | Enumeration of all tours over the extracted costs, which all occur in the text, gives the certified value; the label lies below every tour. |
| `mamo_complex_88` | removed | 4.6 | 66.3661 | Other text defect (T, U) | yes | Text incomplete, ambiguous, or label stated in another unit or quantity; the expert audit removes the problem. |
| `mamo_complex_91` | removed | 22 | 21.2375 | Integrality not stated | no | The label is the optimum of the same program with integer quantities. |
| `mamo_complex_92` | removed | 8 | 10 | B | no | Shortest path computed by hand gives 10 (certified); label 8. |
| `mamo_complex_96` | removed | 5 | 7 | D | yes | The graph is described by a picture that is not part of the text. Withdrawn by verification. |
| `mamo_complex_97` | kept | 9 | 8.27273 | Integrality not stated | no | The label is the optimum of the same program with integer quantities; the text does not state integrality. |
| `mamo_complex_101` | kept | 57 | 53.8965 | Integrality not stated | no | The label is the optimum of the same program with integer quantities; the text does not state integrality. |
| `mamo_complex_102` | kept | 72 | 71.0714 | Integrality not stated | no | The label is the optimum of the same program with integer quantities; the text does not state integrality. |
| `mamo_complex_104` | kept | 26 | 24.0351 | Integrality not stated | no | The label is the optimum of the same program with integer quantities; the text does not state integrality. |
| `mamo_complex_105` | kept | 13 | 12.3333 | Integrality not stated | no | The label is the optimum of the same program with integer quantities; the text does not state integrality. |
| `mamo_complex_107` | kept | 49 | 48.1633 | Integrality not stated | no | The label is the optimum of the same program with integer quantities; the text does not state integrality. |
| `mamo_complex_108` | kept | 27 | 25.3565 | Integrality not stated | no | The label is the optimum of the same program with integer quantities; the text does not state integrality. |
| `mamo_complex_109` | kept | 14 | 12.9661 | Integrality not stated | no | The label is the optimum of the same program with integer quantities; the text does not state integrality. |
| `mamo_complex_112` | removed | 24 | 37.3052 | Other text defect (T, U) | no | Text incomplete, ambiguous, or label stated in another unit or quantity; the expert audit removes the problem. |
| `mamo_complex_113` | kept | 24 | 23.3249 | Integrality not stated | no | The label is the optimum of the same program with integer quantities; the text does not state integrality. |
| `mamo_complex_115` | kept | 31 | 30.2963 | Integrality not stated | no | The label is the optimum of the same program with integer quantities; the text does not state integrality. |
| `mamo_complex_116` | kept | 10 | 9.45 | Integrality not stated | no | The label is the optimum of the same program with integer quantities; the text does not state integrality. |
| `mamo_complex_117` | kept | 28 | 26.1176 | Integrality not stated | no | The label is the optimum of the same program with integer quantities; the text does not state integrality. |
| `mamo_complex_120` | kept | 44 | 42.7792 | Integrality not stated | no | The label is the optimum of the same program with integer quantities; the text does not state integrality. |
| `mamo_complex_121` | kept | 54 | 53.208 | Integrality not stated | no | The label is the optimum of the same program with integer quantities; the text does not state integrality. |
| `mamo_complex_122` | kept | 26 | 25.0092 | Integrality not stated | no | The label is the optimum of the same program with integer quantities; the text does not state integrality. |
| `mamo_complex_134` | removed | 213 | 245 | B | no | Enumeration of all tours over the extracted costs, which all occur in the text, gives the certified value; the label lies below every tour. |
| `mamo_complex_135` | kept | 50 | 127 | B | no | Four cities. Enumeration of the three tours gives 127 (certified); the label 50 is below every tour. |
| `mamo_complex_137` | removed | 228 | 233 | B | no | Enumeration of all tours over the extracted costs, which all occur in the text, gives the certified value; the label lies below every tour. |
| `mamo_complex_139` | removed | 158 | 175 | B | no | Enumeration of all tours over the extracted costs, which all occur in the text, gives the certified value; the label lies below every tour. |
| `mamo_complex_141` | removed | 140 | 159 | B | yes | Enumeration of all tours over the extracted costs, which all occur in the text, gives the certified value; the label lies below every tour. |
| `mamo_complex_142` | removed | 240 | 261 | B | no | Enumeration of all tours over the extracted costs, which all occur in the text, gives the certified value; the label lies below every tour. |
| `mamo_complex_143` | kept | 248 | 260 | B | no | Four cities. Enumeration gives 260 (certified); the label 248 is below every tour. |
| `mamo_complex_144` | removed | 241 | 251 | B | yes | Enumeration of all tours over the extracted costs, which all occur in the text, gives the certified value; the label lies below every tour. |
| `mamo_complex_145` | kept | 140 | 182 | B | no | Four cities. Enumeration gives 182 (certified); the label 140 is below every tour. |
| `mamo_complex_146` | kept | 138 | 145 | B | no | Four cities. Enumeration gives 145 (certified); the label 138 is below every tour. |
| `mamo_complex_147` | removed | 210 | 216 | B | yes | Enumeration of all tours over the extracted costs, which all occur in the text, gives the certified value; the label lies below every tour. |
| `mamo_complex_148` | removed | 252 | 284 | B | no | Enumeration of all tours over the extracted costs, which all occur in the text, gives the certified value; the label lies below every tour. |
| `mamo_complex_149` | removed | 275 | 299 | B | yes | Enumeration of all tours over the extracted costs, which all occur in the text, gives the certified value; the label lies below every tour. |
| `mamo_complex_150` | removed | 124 | 154 | B | no | Enumeration of all tours over the extracted costs, which all occur in the text, gives the certified value; the label lies below every tour. |
| `mamo_complex_151` | removed | 146 | 165 | B | no | Enumeration of all tours over the extracted costs, which all occur in the text, gives the certified value; the label lies below every tour. |
| `mamo_complex_152` | removed | 162 | 191 | B | no | Enumeration of all tours over the extracted costs, which all occur in the text, gives the certified value; the label lies below every tour. |
| `mamo_complex_153` | removed | 56 | 136 | B | no | Enumeration of all tours over the extracted costs, which all occur in the text, gives the certified value; the label lies below every tour. |
| `mamo_complex_154` | removed | 150 | 169 | B | no | Enumeration of all tours over the extracted costs, which all occur in the text, gives the certified value; the label lies below every tour. |
| `mamo_complex_176` | removed | 68 | 68000 | Other text defect (T, U) | yes | Text incomplete, ambiguous, or label stated in another unit or quantity; the expert audit removes the problem. |
| `mamo_complex_182` | removed | 437665 | 503072 | D | yes | Values given by example and "and so on". Withdrawn by verification. |
| `mamo_complex_183` | removed | 607479 | 611738 | D | yes | Values given by example and "and so on". Withdrawn by verification. |
| `mamo_complex_184` | removed | 485771 | 572084 | D | yes | Values given as a range. Withdrawn by verification. |
| `mamo_complex_188` | removed | 607479 | 153712 | D | yes | Values given by example and "and so on". Withdrawn by verification. |
| `mamo_complex_190` | removed | 608437 | 529513 | D | yes | Values given as a range. Withdrawn by verification. |
| `mamo_complex_194` | removed | 242000 | 21600 | Other text defect (T, U) | yes | Text incomplete, ambiguous, or label stated in another unit or quantity; the expert audit removes the problem. |

## Corrected releases (11 misses among 222 certificates)

| Problem | Answer | Certified | Class | Withdrawn | Evidence |
|---|---:|---:|---|---|---|
| `om_industryor_85` | 4170 | 4500 | E | yes | "The same total capacity" is read as half of it (30 instead of 60). Withdrawn. |
| `om_industryor_89` | 408 | 409.091 | Integrality not stated | no | The answer is the integer optimum of the certified program. |
| `om_mamo_27` | 22 | 19.2176 | Integrality not stated | no | Diet problem without the integrality sentence; the answer is the integer optimum. |
| `om_mamo_34` | 192 | 198 | B | no | Six cities; enumeration gives 198 (certified); the answer lies below every tour. |
| `om_mamo_77` | 749272 | 749132 | D | yes | Capacities given only as a range from 840 to 1,856. Withdrawn. |
| `om_mamo_103` | 567010 | 589621 | B | no | All data stated; exact re-solve gives the certified value. |
| `om_mamo_114` | 58895 | 588595 | B | no | All data stated; exact re-solve gives the certified value; the answer lacks one digit. |
| `om_mamo_131` | 178 | 148.611 | Integrality not stated | no | Grain in pounds; the answer is the optimum with integer pounds. |
| `om_mamo_194` | 66.39 | 66.3661 | B | no | Largest inscribed circle by linear programming; the area to four significant digits is 66.37. |
| `om_mamo_197` | 24 | 38 | T | yes | The text states the protein requirement twice (88 and 144); the answer reads the second as carbohydrates. Programs use integer quantities. Withdrawn. |
| `om_mamo_206` | 610975 | 580131 | B | no | All data stated; exact re-solve gives 580,131 (certified), below the answer. |

## Texts that state integrality

The corrected release of Mamo ComplexLP contains 44 diet problems. On the 37 whose text includes the sentence "You could only assign integral portions of each type of food.", three-family agreement certifies 36, and 35 match the answer; the miss is `om_mamo_197` above. The 26 diet problems of the original release whose certificates miss the label because of continuous quantities are all among the 37, and on each of them the corrected release yields a certificate that matches the answer.
