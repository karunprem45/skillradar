"""Do postings that mention Machine Learning list higher salaries?

Observational data, so every result here is an association, not a causal effect.
Postings mentioning ML may also be more senior, in pricier metros, and so on.
salary_regression.R adjusts for seniority.

Methods (resampling tests written with NumPy, cross-checked against SciPy):
  - Welch's t-test on mean salary midpoint
  - Permutation test on the difference in means (10,000 shuffles)
  - Bootstrap 95% CI for the difference in medians (10,000 resamples)
  - Mann-Whitney U as a rank-based check
  - Cohen's d for effect size
  - The same median gap within each seniority level

Run from the repo root:  python analysis/salary_hypothesis.py
"""

import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "skillradar.db"
SEED = 42
N_RESAMPLES = 10_000
SALARY_RANGE = (30_000, 500_000)  # same filter as src/train_salary.py
SKILL = "Machine Learning"

QUERY = """
SELECT j.id, j.seniority, j.remote,
       (j.salary_min + j.salary_max) / 2.0 AS salary,
       MAX(CASE WHEN s.skill = ? THEN 1 ELSE 0 END) AS has_skill
FROM jobs j
LEFT JOIN job_skills s ON s.job_id = j.id
WHERE j.salary_min IS NOT NULL AND j.salary_max IS NOT NULL
GROUP BY j.id
"""


def load():
    with sqlite3.connect(DB) as conn:
        df = pd.read_sql(QUERY, conn, params=(SKILL,))
    return df[df.salary.between(*SALARY_RANGE)].reset_index(drop=True)


def welch_t(a, b):
    """Welch's t statistic and Welch-Satterthwaite degrees of freedom."""
    va, vb = a.var(ddof=1) / len(a), b.var(ddof=1) / len(b)
    t = (a.mean() - b.mean()) / np.sqrt(va + vb)
    df = (va + vb) ** 2 / (va ** 2 / (len(a) - 1) + vb ** 2 / (len(b) - 1))
    p = 2 * stats.t.sf(abs(t), df)
    return t, df, p


def permutation_test(a, b, rng):
    """Two-sided p-value for the difference in means under random relabeling."""
    observed = a.mean() - b.mean()
    pooled = np.concatenate([a, b])
    n_a = len(a)
    hits = 0
    for _ in range(N_RESAMPLES):
        rng.shuffle(pooled)
        if abs(pooled[:n_a].mean() - pooled[n_a:].mean()) >= abs(observed):
            hits += 1
    # +1 so the p-value is never exactly 0 with a finite number of shuffles
    return observed, (hits + 1) / (N_RESAMPLES + 1)


def bootstrap_median_diff(a, b, rng):
    """Percentile bootstrap 95% CI for median(a) - median(b)."""
    diffs = np.empty(N_RESAMPLES)
    for i in range(N_RESAMPLES):
        diffs[i] = np.median(rng.choice(a, len(a))) - np.median(rng.choice(b, len(b)))
    return np.median(a) - np.median(b), np.percentile(diffs, [2.5, 97.5])


def cohens_d(a, b):
    pooled_sd = np.sqrt(((len(a) - 1) * a.var(ddof=1) + (len(b) - 1) * b.var(ddof=1)) / (len(a) + len(b) - 2))
    return (a.mean() - b.mean()) / pooled_sd


def main():
    df = load()
    a = df.loc[df.has_skill == 1, "salary"].to_numpy()
    b = df.loc[df.has_skill == 0, "salary"].to_numpy()
    rng = np.random.default_rng(SEED)

    print(f"{len(df):,} postings with salary in range; {len(a):,} mention {SKILL}, {len(b):,} do not\n")
    print(f"Mean     with ${a.mean():>9,.0f}   without ${b.mean():>9,.0f}")
    print(f"Median   with ${np.median(a):>9,.0f}   without ${np.median(b):>9,.0f}\n")

    t, dof, p = welch_t(a, b)
    t_sp, p_sp = stats.ttest_ind(a, b, equal_var=False)
    print(f"Welch t-test:       t = {t:.2f}, df = {dof:.0f}, p = {p:.2e}   (SciPy: t = {t_sp:.2f}, p = {p_sp:.2e})")

    diff, p_perm = permutation_test(a.copy(), b.copy(), rng)
    print(f"Permutation test:   mean diff ${diff:,.0f}, p = {p_perm:.4f} ({N_RESAMPLES:,} shuffles)")

    med_diff, ci = bootstrap_median_diff(a, b, rng)
    print(f"Bootstrap:          median diff ${med_diff:,.0f}, 95% CI [${ci[0]:,.0f}, ${ci[1]:,.0f}]")

    u, p_u = stats.mannwhitneyu(a, b, alternative="two-sided")
    print(f"Mann-Whitney U:     p = {p_u:.2e}")
    print(f"Cohen's d:          {cohens_d(a, b):.2f}\n")

    print("Median gap within each seniority level (checks whether seniority explains the gap):")
    for level, g in df.groupby(df.seniority.fillna("unknown")):
        ga, gb = g.loc[g.has_skill == 1, "salary"], g.loc[g.has_skill == 0, "salary"]
        if len(ga) >= 30 and len(gb) >= 30:
            print(f"  {level:8} n={len(g):5,}  with ${ga.median():>9,.0f}  without ${gb.median():>9,.0f}  "
                  f"gap ${ga.median() - gb.median():>+8,.0f}")


if __name__ == "__main__":
    main()
