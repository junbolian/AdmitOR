Table 7. Model calls and tokens by family and role. Certification: usage records of the certification runs (role extractor = the family A call with max_tokens 8192, generation = every other call; the records carry no problem id, so the stream certification rows cover all 300 problems including sample_1..5 and per-problem means divide by the problems of the set, ERROR verdicts included; the rows with two programs per family include the reruns of problems whose first attempt ended in an API error). Data verification: one request per problem and family (stream without sample_1..5; family B on the stream only for the problems that panel_base_2of3 certifies); per-problem means divide by the problems with a request. No prices.

| set | stage | family | role | calls | prompt_tokens | completion_tokens | reasoning_tokens | problems | calls_per_problem | prompt_tokens_per_problem | completion_tokens_per_problem |
|---|---|---|---|---|---|---|---|---|---|---|---|
| stream | certification | A | extractor | 301 | 499603 | 187523 | 0 | 300 | 1.00 | 1665 | 625 |
| stream | certification | A | generation | 368 | 693530 | 205650 | 0 | 300 | 1.23 | 2312 | 686 |
| stream | certification | B | generation | 355 | 7046827 | 450049 | 114308 | 300 | 1.18 | 23489 | 1500 |
| stream | certification | C | generation | 334 | 517051 | 221303 | 0 | 300 | 1.11 | 1724 | 738 |
| stream | certification | all | all | 1358 | 8757011 | 1064525 | 114308 | 300 | 4.53 | 29190 | 3548 |
| confirm | certification | A | extractor | 205 | 334844 | 136305 | 0 | 200 | 1.02 | 1674 | 682 |
| confirm | certification | A | generation | 251 | 475318 | 145772 | 0 | 200 | 1.25 | 2377 | 729 |
| confirm | certification | B | generation | 239 | 2342896 | 257609 | 47454 | 200 | 1.20 | 11714 | 1288 |
| confirm | certification | C | generation | 222 | 922504 | 140132 | 0 | 200 | 1.11 | 4613 | 701 |
| confirm | certification | all | all | 917 | 4075562 | 679818 | 47454 | 200 | 4.58 | 20378 | 3399 |
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
| stream, two programs per family | certification | A | extractor | 304 | 504116 | 196322 | 0 | 300 | 1.01 | 1680 | 654 |
| stream, two programs per family | certification | A | generation | 770 | 1455353 | 426471 | 0 | 300 | 2.57 | 4851 | 1422 |
| stream, two programs per family | certification | B | generation | 722 | 12110554 | 904746 | 217433 | 300 | 2.41 | 40369 | 3016 |
| stream, two programs per family | certification | C | generation | 700 | 1683744 | 473525 | 0 | 300 | 2.33 | 5612 | 1578 |
| stream, two programs per family | certification | all | all | 2496 | 15753767 | 2001064 | 217433 | 300 | 8.32 | 52513 | 6670 |
| heldout, two programs per family | certification | A | extractor | 99 | 144528 | 67034 | 0 | 95 | 1.04 | 1521 | 706 |
| heldout, two programs per family | certification | A | generation | 250 | 445379 | 185318 | 0 | 95 | 2.63 | 4688 | 1951 |
| heldout, two programs per family | certification | B | generation | 192 | 3755869 | 303155 | 93777 | 95 | 2.02 | 39535 | 3191 |
| heldout, two programs per family | certification | C | generation | 202 | 276648 | 176279 | 0 | 95 | 2.13 | 2912 | 1856 |
| heldout, two programs per family | certification | all | all | 743 | 4622424 | 731786 | 93777 | 95 | 7.82 | 48657 | 7703 |
| stream | data verification | A | verification | 295 | 537184 | 14580 | 0 | 295 | 1.00 | 1821 | 49 |
| stream | data verification | B | verification | 273 | 5400456 | 15707 | 5750 | 295 | 0.93 | 18307 | 53 |
| stream | data verification | C | verification | 297 | 484207 | 21568 | 0 | 295 | 1.01 | 1641 | 73 |
| stream | data verification | all | all | 865 | 6421847 | 51855 | 5750 | 295 | 2.93 | 21769 | 176 |
| confirm | data verification | A | verification | 200 | 362168 | 6583 | 0 | 200 | 1.00 | 1811 | 33 |
| confirm | data verification | B | verification | 200 | 641350 | 7904 | 1456 | 200 | 1.00 | 3207 | 40 |
| confirm | data verification | C | verification | 205 | 917618 | 15868 | 0 | 200 | 1.02 | 4588 | 79 |
| confirm | data verification | all | all | 605 | 1921136 | 30355 | 1456 | 200 | 3.02 | 9606 | 152 |
| calibration | data verification | A | verification | 150 | 245118 | 3997 | 0 | 150 | 1.00 | 1634 | 27 |
| calibration | data verification | B | verification | 150 | 2931087 | 6030 | 2553 | 150 | 1.00 | 19541 | 40 |
| calibration | data verification | C | verification | 153 | 221840 | 7188 | 0 | 150 | 1.02 | 1479 | 48 |
| calibration | data verification | all | all | 453 | 3398045 | 17215 | 2553 | 150 | 3.02 | 22654 | 115 |
| heldout | data verification | A | verification | 95 | 155739 | 1951 | 0 | 95 | 1.00 | 1639 | 21 |
| heldout | data verification | B | verification | 95 | 1856799 | 3289 | 1389 | 95 | 1.00 | 19545 | 35 |
| heldout | data verification | C | verification | 98 | 142133 | 5766 | 0 | 95 | 1.03 | 1496 | 61 |
| heldout | data verification | all | all | 288 | 2154671 | 11006 | 1389 | 95 | 3.03 | 22681 | 116 |

Table 7b. Wall time per problem. Certification: elapsed_s of the stored verdicts (stream without sample_1..5); the problems of a set ran in parallel, so the sum exceeds the elapsed wall time of the set.

| set | stage | problems | median_seconds | min_seconds | max_seconds |
|---|---|---|---|---|---|
| stream | certification | 295 | 88.5 | 42.5 | 429.2 |
| confirm | certification | 200 | 90.5 | 44.0 | 546.9 |
| calibration | certification | 150 | 97.5 | 42.4 | 775.8 |
| heldout | certification | 95 | 103.3 | 45.1 | 751.6 |
| stream, two programs per family | certification | 295 | 172.0 | 87.5 | 807.7 |
| heldout, two programs per family | certification | 95 | 210.3 | 78.9 | 1164.4 |
| stream | data verification (request seconds summed over the families of a problem) | 295 | 8.4 | 2.5 | 42.3 |
| confirm | data verification (request seconds summed over the families of a problem) | 200 | 6.5 | 4.7 | 76.7 |
| calibration | data verification (request seconds summed over the families of a problem) | 150 | 7.6 | 4.5 | 33.2 |
| heldout | data verification (request seconds summed over the families of a problem) | 95 | 7.6 | 4.6 | 37.9 |
