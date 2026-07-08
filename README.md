# SkillRadar

Real-time job market intelligence for data careers. Ingests live data science / ML
job postings daily, extracts the skills each posting demands with an LLM, and tracks
and forecasts which skills are rising or falling.

## Status

- [x] **Phase 1 — Ingestion**: pull postings from Adzuna / Remotive / Arbeitnow into a database
- [ ] Phase 2 — LLM skill extraction (Claude, structured JSON output)
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
