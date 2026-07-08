# SkillRadar

Real-time job market intelligence for data careers. Ingests live data science / ML
job postings daily, extracts the skills each posting demands with an LLM, and tracks
and forecasts which skills are rising or falling.

## Status

- [x] **Phase 1 — Ingestion**: pull postings from 5 sources (Adzuna, Remotive, Arbeitnow, Jobicy, The Muse)
- [x] **Phase 2a — Rule-based skill extraction** (free baseline): curated vocabulary + regex matching, plus seniority inference (`python -m src.extract_rules`)
- [x] **Phase 2b — Measured extraction quality**: hand-labeled gold set + error analysis (`python -m src.evaluate`) — **F1 0.995** (0.96 before error-analysis fixes)
- [x] **Phase 3 — Daily automated pipeline**: GitHub Actions cron runs the full loop daily at 11:00 UTC — ingest → extract → evaluate → retrain — and commits data + model artifacts
- [x] **Phase 4a — ML models**: salary prediction (HistGradientBoosting, **14% MAE improvement over median baseline**; Ridge for interpretable skill premiums) + role clustering (KMeans over TF-IDF of titles+skills) — `python -m src.train_salary`, `python -m src.cluster_roles`; optional MLflow logging
- [ ] Phase 4b — Skill-demand trend forecasting (needs a few weeks of daily history — accumulating now)
- [ ] Phase 4c — LLM extraction benchmark vs the rule baseline (code ready in `src/extract.py`; Groq free tier planned)
- [x] **Phase 5 — Streamlit dashboard**: `streamlit run dashboard.py` — market overview, segment analysis, and ML lab tabs
- [ ] Phase 6 — Public deployment on Streamlit Community Cloud

## Model card (auto-refreshed daily)

| Component | Method | Result |
|---|---|---|
| Skill extraction | ~90-skill vocabulary, word-boundary regex | F1 0.995 / precision 0.99 / recall 1.00 on a 15-posting, 103-label gold set |
| Salary prediction | HistGradientBoosting on skills + seniority + metro + remote | MAE ≈ $38k vs $44k median baseline (−14%), R² ≈ 0.25 on 20% held-out test |
| Skill premiums | Ridge coefficients | e.g. ETL +$21k, ML +$17k, Experimentation +$16k |
| Role archetypes | KMeans (k=6), TF-IDF of title + skills | analyst ($110k median) → ML-heavy ($187k median) spread |

R² is modest and honestly reported: most salary postings come from Adzuna, whose free API truncates
descriptions, so skill features are sparse there. Improves as full-text sources accumulate daily.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Optionally create a `.env` file in the repo root (gitignored) for API keys:

```bash
# Adzuna (developer.adzuna.com — free tier): US postings with salary data.
# Without these, ingestion uses only the keyless sources.
ADZUNA_APP_ID=your_app_id
ADZUNA_APP_KEY=your_app_key

# Database override (defaults to SQLite at <repo>/data/skillradar.db):
# DATABASE_URL=postgresql://user:pass@host/skillradar
```

## Run

```bash
python -m src.ingest   # pull postings (re-run safe, dedupes on source_id)
python -m src.stats    # sanity-check what's in the DB
```

Without any API keys this uses the keyless sources (Remotive, Arbeitnow).
Add Adzuna keys to `.env` for US city-level postings with salary data.

The database is SQLite (`data/skillradar.db`) by default; set `DATABASE_URL`
in `.env` to point at Postgres/Neon when scaling up.

## Data-quality notes

- Adzuna's free search API returns **truncated ~500-char description snippets**,
  so its postings are used for salary/location/title analytics but excluded from
  skill-frequency stats. Full-text sources (Remotive, Jobicy, The Muse, Arbeitnow)
  drive the skill analysis and grow with every daily run.
