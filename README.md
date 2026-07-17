# SkillRadar 📡

**A self-updating intelligence platform that tracks what the US data-science job market actually demands — and what it pays.**

[![Live Dashboard](https://img.shields.io/badge/Live-Streamlit_Dashboard-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)]([FILL: your streamlit.app URL])
[![Pipeline](https://img.shields.io/badge/Pipeline-GitHub_Actions-2088FF?style=flat-square&logo=github-actions&logoColor=white)](#-how-it-works)
![Python](https://img.shields.io/badge/Python-3670A0?style=flat-square&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## The problem

Job seekers have no live, data-backed view of which data-science skills the US market actually demands or what they pay — they rely on anecdotes, outdated salary reports, and gut feeling. Postings change weekly; static reports are stale the day they're published.

**SkillRadar** answers that with live data: it continuously ingests real job postings, extracts the skills inside them, models the salaries, and surfaces the trends — all automatically, with no manual step.

---

## What it does

- 📥 **Ingests 1,300+ US postings** from **4 job-board APIs** on an automated **6-hour cron** (GitHub Actions)
- 🏷️ **Extracts skills** with a rule-based engine validated against a hand-labeled gold set — **F1 = 0.995**
- 💰 **Predicts salaries** with an interpretable model — **14% MAE reduction** over baseline — exposing per-skill premiums (e.g. ETL +$21K, ML +$17K)
- 🧭 **Clusters roles** into archetypes (KMeans), revealing a **$77K analyst-to-ML pay gap**
- 📊 **Surfaces market signals** — e.g. **42% of US data postings now demand LLM/GenAI skills**
- 🔄 **Retrains daily** and serves everything through a deployed **4-tab Streamlit dashboard**

---

## 🔧 How it works

```
                    ┌─────────────────────────────────────────────┐
                    │   GitHub Actions cron  (every 6 hours)       │
                    └───────────────────────┬─────────────────────┘
                                             │
   4 Job-Board APIs ──▶  Ingestion  ──▶  Cleaning &  ──▶  Skill Extraction
                         layer            dedup           (rule-based, F1 0.995)
                                             │                    │
                                             ▼                    ▼
                                      ┌──────────────┐    ┌────────────────────┐
                                      │  Data store  │───▶│ Salary model (daily │
                                      │ (SQLAlchemy) │    │ retrain, -14% MAE)  │
                                      └──────────────┘    │ + KMeans archetypes │
                                             │            └─────────┬──────────┘
                                             ▼                      ▼
                                      ┌──────────────────────────────────────┐
                                      │   Streamlit dashboard (4 tabs, live)  │
                                      └──────────────────────────────────────┘
```

**Pipeline stages**
1. **Ingestion** — pulls postings from 4 APIs, normalizes into a common schema
2. **Cleaning & dedup** — deduplicates and standardizes fields (title, location, salary, description)
3. **Skill extraction** — rule-based matcher over posting text, validated against a hand-labeled gold set (**F1 0.995**)
4. **Modeling** — salary-prediction model with per-skill premium interpretation + KMeans role archetypes
5. **Serving** — Streamlit dashboard, refreshed via daily automated retraining

---

## 📊 Key findings

| Insight | Value |
|---|---|
| Skill-extraction accuracy (vs. gold set) | **F1 0.995** |
| Salary-model improvement over baseline | **14% MAE reduction** |
| ETL skill premium | **+$21K** |
| ML skill premium | **+$17K** |
| Analyst → ML role pay gap | **$77K** |
| US postings demanding LLM/GenAI | **42%** |

---

## 🛠️ Tech stack

**Language** · Python
**ML** · scikit-learn, XGBoost, KMeans
**Data / MLOps** · pandas, NumPy, SQLAlchemy, GitHub Actions (CI/CD)
**App / Viz** · Streamlit, Plotly, Matplotlib

---

## 🚀 Run it locally

```bash
# 1. Clone
git clone https://github.com/karunprem45/skillradar.git
cd skillradar

# 2. Environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Configure API keys
cp .env.example .env
# add your job-board API keys to .env

# 4. Run the pipeline once
python [FILL: e.g. src/pipeline.py]

# 5. Launch the dashboard
streamlit run [FILL: e.g. app.py]
```

> The automated 6-hour refresh runs via GitHub Actions — see [`.github/workflows/[FILL].yml`](.github/workflows/).

---

## 📁 Repository structure

```
skillradar/
├── [FILL: src/            # ingestion, extraction, modeling — match your actual folders]
├── [FILL: app.py          # Streamlit dashboard]
├── [FILL: data/           # gold set, cached postings]
├── .github/workflows/     # the 6-hour cron pipeline
├── requirements.txt
└── README.md
```

---

## 🗺️ Roadmap

- [ ] Replace rule-based extraction with a fine-tuned model, benchmarked against the gold set
- [ ] Expand beyond data-science roles to adjacent fields
- [ ] Resume-to-market skill-gap matching (SkillRadar Copilot)

---

## 👤 Author

**Karuniya Premnath** — MS Data Science @ Northeastern University
[LinkedIn](https://linkedin.com/in/karuniya-premnath) · [Portfolio](https://karunprem45.github.io/portfolio/) · premnath.k@northeastern.edu

---

*Built to answer a question I had myself: what should I actually be learning, and what is it worth?*
