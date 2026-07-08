# SkillRadar

Real-time job market intelligence for data careers. Ingests live data science / ML
job postings daily, extracts the skills each posting demands with an LLM, and tracks
and forecasts which skills are rising or falling.

## Status

- [x] **Phase 1 — Ingestion**: pull postings from 5 sources (Adzuna, Remotive, Arbeitnow, Jobicy, The Muse)
- [x] **Phase 2a — Rule-based skill extraction** (free baseline): curated vocabulary + regex matching, plus seniority inference (`python -m src.extract_rules`)
- [ ] Phase 2b — LLM skill extraction to benchmark against the baseline (code ready in `src/extract.py`; needs an API key with credits, or swap to Groq free tier)
- [ ] Phase 3 — Daily automated pipeline (Prefect / GitHub Actions cron)
- [ ] Phase 4 — Trend forecasting + role clustering, tracked in MLflow
- [ ] Phase 5 — FastAPI + Streamlit dashboard
- [ ] Phase 6 — Docker, CI/CD, monitoring, public deployment

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in your keys (optional for Phase 1)
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
