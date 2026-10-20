# Salary analysis: does mentioning Machine Learning go with higher pay?

These scripts read `data/skillradar.db` without modifying it. The data is observational,
so every result below is an **association**, not a causal effect.

| Script | What it does |
|---|---|
| `salary_hypothesis.py` | Welch t-test, permutation test, bootstrap CI, Mann-Whitney U, Cohen's d, and the median gap within each seniority level. The resampling tests are written in NumPy and cross-checked against SciPy. |
| `salary_regression.R` | `lm(log(salary) ~ mentions_ml + seniority)` in base R, plus a Welch t-test to cross-check the Python script |

## Results (database snapshot of 2026-10-12)

The sample is 9,702 postings with a salary midpoint between $30k and $500k (the same
filter as `src/train_salary.py`). 2,668 of them mention Machine Learning.

| Check | Result |
|---|---|
| Median salary, with ML vs without | $178,012 vs $132,525 |
| Welch t-test | t = 27.95, p < 1e-150 (NumPy and SciPy agree) |
| Permutation test, 10,000 shuffles | mean gap $36,330, p ≈ 0.0001 (the smallest p-value 10,000 shuffles can give) |
| Bootstrap 95% CI, median gap | $41,767 to $47,087 |
| Cohen's d | 0.64 (medium effect) |
| Gap within each seniority level | +$26k to +$41k at entry, mid, senior, and staff+ |
| **R regression, adjusted for seniority** | **ML mention associated with 21.2% higher salary (95% CI 19.3% to 23.2%)**, R² = 0.171 |

## Caveats

- Almost all salary data comes from Adzuna, whose API truncates descriptions. Some
  postings that do ask for ML will be labeled "without", which tends to shrink the gap.
- Every posting with salary data has `remote = 0`, so remote status can't be adjusted for.
- Other confounders, such as metro, industry, and company size, are not controlled for.

## Run

```bash
python analysis/salary_hypothesis.py
Rscript analysis/salary_regression.R
```

The R script needs only base R and the `sqlite3` command-line tool.
