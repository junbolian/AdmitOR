Table 7. Model calls and tokens by family and role. Certification: usage records of the certification runs (role extractor = the family A call with max_tokens 8192, generation = every other call; the records carry no problem id, so the stream certification rows cover all 300 problems including sample_1..5 and per-problem means divide by the problems of the set, ERROR verdicts included; the rows with two programs per family include the reruns of problems whose first attempt ended in an API error). Data verification: one request per problem and family (stream without sample_1..5; family B on the stream only for the problems that panel_base_2of3 certifies); per-problem means divide by the problems with a request. No prices.

| set | stage | family | role | calls | prompt_tokens | completion_tokens | reasoning_tokens | problems | calls_per_problem | prompt_tokens_per_problem | completion_tokens_per_problem |
|---|---|---|---|---|---|---|---|---|---|---|---|
| stream | certification | A | extractor | 300 | 497736 | 187110 | 0 | 300 | 1.00 | 1659 | 624 |
| stream | certification | A | generation | 367 | 691633 | 205348 | 0 | 300 | 1.22 | 2305 | 684 |
| stream | certification | B | generation | 354 | 7027000 | 449116 | 114007 | 300 | 1.18 | 23423 | 1497 |
| stream | certification | C | generation | 333 | 512805 | 220916 | 0 | 300 | 1.11 | 1709 | 736 |
| stream | certification | all | all | 1354 | 8729174 | 1062490 | 114007 | 300 | 4.51 | 29097 | 3542 |
| confirm | certification | A | extractor | 200 | 325526 | 132762 | 0 | 200 | 1.00 | 1628 | 664 |
| confirm | certification | A | generation | 247 | 467578 | 143225 | 0 | 200 | 1.24 | 2338 | 716 |
| confirm | certification | B | generation | 235 | 2263373 | 252225 | 46295 | 200 | 1.18 | 11317 | 1261 |
| confirm | certification | C | generation | 218 | 902987 | 137165 | 0 | 200 | 1.09 | 4515 | 686 |
| confirm | certification | all | all | 900 | 3959464 | 665377 | 46295 | 200 | 4.50 | 19797 | 3327 |
| calibration | certification | A | extractor | 150 | 217351 | 96733 | 0 | 150 | 1.00 | 1449 | 645 |
| calibration | certification | A | generation | 194 | 342041 | 133986 | 0 | 150 | 1.29 | 2280 | 893 |
| calibration | certification | B | generation | 154 | 3011269 | 246763 | 79967 | 150 | 1.03 | 20075 | 1645 |
| calibration | certification | C | generation | 157 | 203473 | 130098 | 0 | 150 | 1.05 | 1356 | 867 |
| calibration | certification | all | all | 655 | 3774134 | 607580 | 79967 | 150 | 4.37 | 25161 | 4051 |
| heldout | certification | A | extractor | 95 | 139399 | 57841 | 0 | 95 | 1.00 | 1467 | 609 |
| heldout | certification | A | generation | 131 | 236194 | 89604 | 0 | 95 | 1.38 | 2486 | 943 |
| heldout | certification | B | generation | 99 | 1935678 | 156104 | 48000 | 95 | 1.04 | 20376 | 1643 |
| heldout | certification | C | generation | 101 | 129866 | 84487 | 0 | 95 | 1.06 | 1367 | 889 |
| heldout | certification | all | all | 426 | 2441137 | 388036 | 48000 | 95 | 4.48 | 25696 | 4085 |
| stream, two programs per family | certification | A | extractor | 303 | 501717 | 195505 | 0 | 300 | 1.01 | 1672 | 652 |
| stream, two programs per family | certification | A | generation | 766 | 1444339 | 424322 | 0 | 300 | 2.55 | 4814 | 1414 |
| stream, two programs per family | certification | B | generation | 718 | 12027015 | 899733 | 216314 | 300 | 2.39 | 40090 | 2999 |
| stream, two programs per family | certification | C | generation | 696 | 1663553 | 470559 | 0 | 300 | 2.32 | 5545 | 1569 |
| stream, two programs per family | certification | all | all | 2483 | 15636624 | 1990119 | 216314 | 300 | 8.28 | 52122 | 6634 |
| heldout, two programs per family | certification | A | extractor | 99 | 144528 | 67034 | 0 | 95 | 1.04 | 1521 | 706 |
| heldout, two programs per family | certification | A | generation | 250 | 445379 | 185318 | 0 | 95 | 2.63 | 4688 | 1951 |
| heldout, two programs per family | certification | B | generation | 192 | 3755869 | 303155 | 93777 | 95 | 2.02 | 39535 | 3191 |
| heldout, two programs per family | certification | C | generation | 202 | 276648 | 176279 | 0 | 95 | 2.13 | 2912 | 1856 |
| heldout, two programs per family | certification | all | all | 743 | 4622424 | 731786 | 93777 | 95 | 7.82 | 48657 | 7703 |
| stream | data verification | A | verification | 294 | 535217 | 14566 | 0 | 294 | 1.00 | 1820 | 50 |
| stream | data verification | B | verification | 272 | 5380591 | 15677 | 5736 | 294 | 0.93 | 18301 | 53 |
| stream | data verification | C | verification | 294 | 473160 | 21160 | 0 | 294 | 1.00 | 1609 | 72 |
| stream | data verification | all | all | 860 | 6388968 | 51403 | 5736 | 294 | 2.93 | 21731 | 175 |
| confirm | data verification | A | verification | 196 | 354277 | 6527 | 0 | 196 | 1.00 | 1808 | 33 |
| confirm | data verification | B | verification | 196 | 561796 | 7795 | 1411 | 196 | 1.00 | 2866 | 40 |
| confirm | data verification | C | verification | 196 | 867641 | 15416 | 0 | 196 | 1.00 | 4427 | 79 |
| confirm | data verification | all | all | 588 | 1783714 | 29738 | 1411 | 196 | 3.00 | 9101 | 152 |
| calibration | data verification | A | verification | 150 | 245118 | 3997 | 0 | 150 | 1.00 | 1634 | 27 |
| calibration | data verification | B | verification | 150 | 2931087 | 6030 | 2553 | 150 | 1.00 | 19541 | 40 |
| calibration | data verification | C | verification | 150 | 209009 | 6808 | 0 | 150 | 1.00 | 1393 | 45 |
| calibration | data verification | all | all | 450 | 3385214 | 16835 | 2553 | 150 | 3.00 | 22568 | 112 |
| heldout | data verification | A | verification | 95 | 155739 | 1951 | 0 | 95 | 1.00 | 1639 | 21 |
| heldout | data verification | B | verification | 95 | 1856799 | 3289 | 1389 | 95 | 1.00 | 19545 | 35 |
| heldout | data verification | C | verification | 95 | 132812 | 5423 | 0 | 95 | 1.00 | 1398 | 57 |
| heldout | data verification | all | all | 285 | 2145350 | 10663 | 1389 | 95 | 3.00 | 22583 | 112 |

Table 7b. Wall time per problem. Certification: elapsed_s of the stored verdicts (stream without sample_1..5); the problems of a set ran in parallel, so the sum exceeds the elapsed wall time of the set.

| set | stage | problems | median_seconds | min_seconds | max_seconds |
|---|---|---|---|---|---|
| stream | certification | 295 | 88.5 | 3.3 | 429.2 |
| confirm | certification | 200 | 90.3 | 4.9 | 546.9 |
| calibration | certification | 150 | 97.5 | 42.4 | 775.8 |
| heldout | certification | 95 | 103.3 | 45.1 | 751.6 |
| stream, two programs per family | certification | 295 | 171.9 | 18.4 | 807.7 |
| heldout, two programs per family | certification | 95 | 210.3 | 78.9 | 1164.4 |
| stream | data verification (request seconds summed over the families of a problem) | 294 | 8.4 | 2.5 | 42.3 |
| confirm | data verification (request seconds summed over the families of a problem) | 196 | 6.4 | 4.7 | 76.7 |
| calibration | data verification (request seconds summed over the families of a problem) | 150 | 7.6 | 4.5 | 33.2 |
| heldout | data verification (request seconds summed over the families of a problem) | 95 | 7.6 | 4.6 | 37.9 |
