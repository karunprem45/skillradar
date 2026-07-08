"""Evaluate the rule-based skill extractor against a hand-labeled gold set.

Gold labels live in data/gold_set.json and cover title + first 4200 chars of
each posting (the window the labels were curated from).

Run:  python -m src.evaluate
"""

import json

from src.db import ROOT, Job, Session
from src.extract_rules import extract_skills

GOLD_PATH = ROOT / "data" / "gold_set.json"
METRICS_PATH = ROOT / "data" / "eval_metrics.json"


def main():
    gold = {k: set(v) for k, v in json.loads(GOLD_PATH.read_text()).items() if not k.startswith("_")}

    session = Session()
    jobs = {j.source_id: j for j in session.query(Job).filter(Job.source_id.in_(gold)).all()}

    tp = fp = fn = 0
    rows = []
    for source_id, truth in gold.items():
        job = jobs.get(source_id)
        if not job:
            print(f"  WARNING: {source_id} not in DB, skipping")
            continue
        text = f"{job.title}\n{' '.join((job.description or '').split())[:4200]}"
        predicted = set(extract_skills(text))
        tp += len(predicted & truth)
        fp += len(predicted - truth)
        fn += len(truth - predicted)
        rows.append({
            "source_id": source_id,
            "title": job.title,
            "false_positives": sorted(predicted - truth),
            "false_negatives": sorted(truth - predicted),
        })
    session.close()

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0

    metrics = {
        "n_postings": len(rows),
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
    }
    METRICS_PATH.write_text(json.dumps(metrics, indent=2))

    print(f"Gold set: {len(rows)} postings, {tp + fn} gold skill labels")
    print(f"Precision: {precision:.1%}   Recall: {recall:.1%}   F1: {f1:.3f}")
    print("\nErrors by posting:")
    for r in rows:
        if r["false_positives"] or r["false_negatives"]:
            print(f"  {r['title'][:50]}")
            if r["false_positives"]:
                print(f"    spurious: {', '.join(r['false_positives'])}")
            if r["false_negatives"]:
                print(f"    missed:   {', '.join(r['false_negatives'])}")


if __name__ == "__main__":
    main()
