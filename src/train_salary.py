"""Train a salary prediction model on postings with salary data.

Features: extracted skills (multi-hot), seniority, metro, remote flag.
Target:   salary midpoint (mean of posted min/max).

Two models:
  - HistGradientBoosting — the accuracy model (metrics reported on a held-out test set)
  - Ridge regression     — the interpretation model (coefficients = per-skill salary premium)

Artifacts land in data/model_artifacts.json for the dashboard. If MLflow is
installed, the run is also logged there.

Run:  python -m src.train_salary
"""

import json

import numpy as np
import pandas as pd
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

from src.db import ROOT, engine

SEED = 42
MIN_SKILL_COUNT = 10       # skills rarer than this in the salary set are dropped
SALARY_RANGE = (30_000, 500_000)  # drop hourly rates and absurd outliers

METROS = {
    "Boston": ["Boston", "Suffolk County"],
    "New York": ["New York", "Manhattan", "Brooklyn", "Queens"],
    "San Francisco": ["San Francisco"],
    "Seattle": ["Seattle", "King County", "Bellevue"],
    "Austin": ["Austin", "Travis County"],
}


def build_features():
    jobs = pd.read_sql(
        "SELECT id, location, remote, salary_min, salary_max, seniority FROM jobs "
        "WHERE salary_min IS NOT NULL AND salary_max IS NOT NULL",
        engine,
    )
    jobs["salary"] = (jobs.salary_min + jobs.salary_max) / 2
    jobs = jobs[(jobs.salary >= SALARY_RANGE[0]) & (jobs.salary <= SALARY_RANGE[1])]

    skills = pd.read_sql("SELECT job_id, skill FROM job_skills", engine)
    skills = skills[skills.job_id.isin(jobs.id)]
    keep = skills.skill.value_counts()
    keep = keep[keep >= MIN_SKILL_COUNT].index
    skills = skills[skills.skill.isin(keep)]

    skill_matrix = pd.crosstab(skills.job_id, skills.skill).clip(upper=1)
    skill_matrix.columns = [f"skill: {c}" for c in skill_matrix.columns]

    jobs["metro"] = "Other"
    for metro, needles in METROS.items():
        mask = jobs.location.fillna("").str.contains("|".join(needles), case=False)
        jobs.loc[mask, "metro"] = metro

    X = pd.get_dummies(jobs.set_index("id")[["seniority", "metro"]], prefix_sep=": ")
    X["remote"] = jobs.set_index("id").remote.fillna(False).astype(int)
    X = X.join(skill_matrix).fillna(0).astype(float)
    y = jobs.set_index("id").salary.loc[X.index]
    return X, y


def main():
    X, y = build_features()
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=SEED)
    print(f"{len(X)} postings with salary, {X.shape[1]} features "
          f"({len(X_train)} train / {len(X_test)} test)")

    baseline = DummyRegressor(strategy="median").fit(X_train, y_train)
    baseline_mae = mean_absolute_error(y_test, baseline.predict(X_test))

    model = HistGradientBoostingRegressor(random_state=SEED, max_depth=4, learning_rate=0.08)
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, pred)
    r2 = r2_score(y_test, pred)

    # interpretation model: ridge coefficient = holding all else fixed, how much
    # does mentioning this skill shift the posted salary midpoint
    ridge = Ridge(alpha=10.0).fit(X_train, y_train)
    coefs = pd.Series(ridge.coef_, index=X.columns)
    skill_premiums = (
        coefs[coefs.index.str.startswith("skill: ")]
        .rename(lambda s: s.removeprefix("skill: "))
        .sort_values(ascending=False)
    )

    print(f"\nBaseline (predict median): MAE ${baseline_mae:,.0f}")
    print(f"Gradient boosting:         MAE ${mae:,.0f}  R² {r2:.3f}")
    print(f"\nTop skill premiums (Ridge): ")
    for skill, delta in skill_premiums.head(8).items():
        print(f"  {skill:20} {delta:+,.0f}")

    artifacts = {
        "n_postings": len(X),
        "n_features": X.shape[1],
        "n_test": len(X_test),
        "baseline_mae": round(baseline_mae),
        "mae": round(mae),
        "r2": round(r2, 3),
        "mae_improvement_pct": round((1 - mae / baseline_mae) * 100, 1),
        "premiums": [
            {"skill": s, "delta": round(d)}
            for s, d in pd.concat([skill_premiums.head(10), skill_premiums.tail(4)]).items()
        ],
    }
    (ROOT / "data" / "model_artifacts.json").write_text(json.dumps(artifacts, indent=2))
    print("\nartifacts -> data/model_artifacts.json")

    try:  # optional experiment tracking
        import mlflow

        mlflow.set_experiment("skillradar-salary")
        with mlflow.start_run():
            mlflow.log_params({"model": "HistGradientBoosting", "max_depth": 4, "lr": 0.08,
                               "n_features": X.shape[1], "n_train": len(X_train)})
            mlflow.log_metrics({"mae": mae, "r2": r2, "baseline_mae": baseline_mae})
        print("logged to MLflow")
    except ImportError:
        pass


if __name__ == "__main__":
    main()
