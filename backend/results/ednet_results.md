# Baseline check on real data (EdNet KT1)

14,460 randomly sampled students with at least 30 answers (first 300 kept). 80% train, 20% test: 2,892 students, 357,756 test answers. 189 concept tags.

| Method | AUC | Accuracy | Log loss | RMSE |
|---|---|---|---|---|
| Global average | 0.500 | 0.619 | 0.665 | 0.486 |
| Per-question accuracy | 0.721 | 0.688 | 0.590 | 0.450 |
| Learner's running accuracy | 0.598 | 0.615 | 0.657 | 0.482 |
| BKT (hand-set parameters) | 0.570 | 0.517 | 0.767 | 0.530 |
| BKT (fitted, all tags) | 0.627 | 0.625 | 0.645 | 0.476 |
| BKT (fitted, first tag only) | 0.641 | 0.647 | 0.633 | 0.470 |
