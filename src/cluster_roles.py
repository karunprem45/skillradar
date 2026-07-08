"""Cluster postings into role archetypes from their titles + extracted skills.

TF-IDF over (title tokens + skill names) -> KMeans. Each cluster gets a profile:
size, top skills, top title words, median salary. Artifacts land in
data/role_clusters.json for the dashboard.

Run:  python -m src.cluster_roles
"""

import json
import re
from collections import Counter

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer

from src.db import ROOT, engine

SEED = 42
K = 6
TITLE_STOPWORDS = {
    "senior", "junior", "staff", "principal", "lead", "sr", "jr", "mid", "level",
    "i", "ii", "iii", "remote", "m", "f", "d", "w", "x", "all", "genders",
    "and", "of", "for", "the", "a", "an", "in", "at", "with", "to",
}


def main():
    jobs = pd.read_sql("SELECT id, title, salary_min, salary_max FROM jobs", engine)
    skills = pd.read_sql("SELECT job_id, skill FROM job_skills", engine)

    skill_lists = skills.groupby("job_id").skill.apply(list)
    jobs = jobs[jobs.id.isin(skill_lists.index)].copy()
    docs = [
        f"{title} {' '.join(skill_lists[jid])}"
        for jid, title in zip(jobs.id, jobs.title)
    ]
    print(f"Clustering {len(docs)} postings (those with >=1 extracted skill) into {K} archetypes")

    tfidf = TfidfVectorizer(lowercase=True, token_pattern=r"[A-Za-z][A-Za-z+/#.-]+", min_df=5)
    X = tfidf.fit_transform(docs)
    km = KMeans(n_clusters=K, random_state=SEED, n_init=10)
    jobs["cluster"] = km.fit_predict(X)

    clusters = []
    for c in range(K):
        members = jobs[jobs.cluster == c]
        member_skills = skills[skills.job_id.isin(members.id)]
        top_skills = member_skills.skill.value_counts().head(6)

        words = Counter()
        for title in members.title:
            for w in re.findall(r"[a-z]+", title.lower()):
                if w not in TITLE_STOPWORDS and len(w) > 1:
                    words[w] += 1
        label = " ".join(w.title() for w, _ in words.most_common(2))
        # same two title words can top multiple clusters — disambiguate with the
        # strongest skill that isn't already part of the label
        if any(c["label"].startswith(label) for c in clusters):
            extra = next((s for s in top_skills.index if s.lower() not in label.lower()), "misc")
            label = f"{label} · {extra}"

        with_salary = members.dropna(subset=["salary_min", "salary_max"])
        median = ((with_salary.salary_min + with_salary.salary_max) / 2).median() if len(with_salary) else None

        clusters.append({
            "label": label,
            "size": len(members),
            "median_salary": round(median) if median else None,
            "top_skills": [
                {"skill": s, "share": round(n / len(members) * 100)}
                for s, n in top_skills.items()
            ],
        })
        print(f"  [{c}] {label:30} n={len(members):4}  "
              f"median={'$' + format(median, ',.0f') if median else 'n/a'}")

    clusters.sort(key=lambda c: -c["size"])
    (ROOT / "data" / "role_clusters.json").write_text(json.dumps({"k": K, "clusters": clusters}, indent=2))
    print("artifacts -> data/role_clusters.json")


if __name__ == "__main__":
    main()
