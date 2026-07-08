"""SkillRadar dashboard.  Run:  streamlit run dashboard.py"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.db import engine

# reference palette (validated) — single hue for magnitude, ordinal ramp for seniority
BLUE = "#2a78d6"
ORDINAL = ["#86b6ef", "#5598e7", "#2a78d6", "#1c5cab"]  # entry -> staff+
INK_MUTED = "#898781"
GRID = "#e1e0d9"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'

METROS = {
    "Boston": ["Boston", "Suffolk County"],
    "New York": ["New York", "Manhattan", "Brooklyn", "Queens"],
    "San Francisco": ["San Francisco"],
    "Seattle": ["Seattle", "King County", "Bellevue"],
    "Austin": ["Austin", "Travis County"],
}

st.set_page_config(page_title="SkillRadar", page_icon="📡", layout="wide")


@st.cache_data(ttl=3600)
def load_data():
    jobs = pd.read_sql(
        "SELECT id, source, title, location, salary_min, salary_max, seniority, ingested_at FROM jobs",
        engine,
    )
    skills = pd.read_sql("SELECT job_id, skill FROM job_skills", engine)
    return jobs, skills


def style(fig, height=420):
    fig.update_layout(
        height=height,
        margin=dict(l=0, r=70, t=8, b=0),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT, color=INK_MUTED, size=13),
        showlegend=False,
        bargap=0.35,
    )
    fig.update_xaxes(gridcolor=GRID, zeroline=False, linecolor=GRID)
    fig.update_yaxes(gridcolor="rgba(0,0,0,0)", zeroline=False)
    return fig


def hbar(labels, values, text=None, color=BLUE):
    fig = go.Figure(
        go.Bar(
            x=values, y=labels, orientation="h",
            marker=dict(color=color, cornerradius=4),
            text=text, textposition="outside", textfont=dict(color=INK_MUTED),
            cliponaxis=False,
            hovertemplate="%{y}: %{x}<extra></extra>",
        )
    )
    fig.update_yaxes(autorange="reversed")
    return fig


jobs, skills = load_data()

full_text = jobs[jobs.source != "adzuna"]
skills_ft = skills[skills.job_id.isin(full_text.id)]

st.title("📡 SkillRadar")
st.caption(
    "Live intelligence on the data-careers job market — postings ingested daily, "
    "skills extracted automatically. github.com/karunprem45/skillradar"
)

# ---- headline tiles ----
llm_pct = skills_ft[skills_ft.skill.isin(["LLMs", "Generative AI", "RAG"])].job_id.nunique() / len(full_text) * 100
salaries = jobs.dropna(subset=["salary_min", "salary_max"])
median_salary = ((salaries.salary_min + salaries.salary_max) / 2).median()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Job postings tracked", f"{len(jobs):,}")
c2.metric("With salary data", f"{len(salaries):,}")
c3.metric("Ask for LLM/GenAI skills", f"{llm_pct:.0f}%")
c4.metric("Median salary (US)", f"${median_salary:,.0f}")

st.divider()

# ---- top skills + salary by skill ----
left, right = st.columns(2)

with left:
    st.subheader("Most in-demand skills")
    st.caption(f"Share of {len(full_text)} full-description postings mentioning each skill")
    top = skills_ft.skill.value_counts().head(15)
    pct = (top / len(full_text) * 100).round(0)
    st.plotly_chart(
        style(hbar(top.index, top.values, text=[f"{p:.0f}%" for p in pct])),
        use_container_width=True,
    )

with right:
    st.subheader("Median salary by skill")
    st.caption("US postings with salary data (Adzuna); skills with 15+ postings")
    sal = skills.merge(salaries, left_on="job_id", right_on="id")
    sal["mid"] = (sal.salary_min + sal.salary_max) / 2
    by_skill = sal.groupby("skill")["mid"].agg(["median", "count"])
    by_skill = by_skill[by_skill["count"] >= 15].sort_values("median", ascending=False).head(15)
    st.plotly_chart(
        style(hbar(by_skill.index, by_skill["median"], text=[f"${v / 1000:.0f}k" for v in by_skill["median"]])),
        use_container_width=True,
    )

st.divider()

# ---- metros + seniority ----
left, right = st.columns(2)

with left:
    st.subheader("Postings by metro area")
    st.caption("US postings (Adzuna), median salary labeled")
    rows = []
    for metro, needles in METROS.items():
        mask = jobs.location.fillna("").str.contains("|".join(needles), case=False)
        metro_jobs = jobs[mask].dropna(subset=["salary_min", "salary_max"])
        if len(metro_jobs):
            rows.append({
                "metro": metro,
                "n": len(metro_jobs),
                "median": ((metro_jobs.salary_min + metro_jobs.salary_max) / 2).median(),
            })
    metros = pd.DataFrame(rows).sort_values("n", ascending=False)
    st.plotly_chart(
        style(hbar(metros.metro, metros.n, text=[f"${m / 1000:.0f}k" for m in metros["median"]])),
        use_container_width=True,
    )

with right:
    st.subheader("Seniority mix")
    st.caption("Inferred from titles across all postings")
    order = ["entry", "mid", "senior", "staff+"]
    sen = jobs.seniority.value_counts().reindex(order).fillna(0)
    fig = go.Figure(
        go.Bar(
            x=order, y=sen.values,
            marker=dict(color=ORDINAL, cornerradius=4),
            text=[f"{int(v):,}" for v in sen.values], textposition="outside",
            textfont=dict(color=INK_MUTED), cliponaxis=False,
            hovertemplate="%{x}: %{y}<extra></extra>",
        )
    )
    st.plotly_chart(style(fig), use_container_width=True)

st.divider()

with st.expander("Data notes & sources"):
    st.markdown(
        """
- **Sources:** Adzuna (US, salaries), Remotive, Jobicy, The Muse, Arbeitnow — ingested daily at 11:00 UTC via GitHub Actions.
- **Skill extraction** is rule-based (curated ~90-skill vocabulary, word-boundary regex) — free and reproducible.
- Adzuna's free API truncates descriptions, so **skill percentages use only full-description sources**; Adzuna powers salary and metro stats.
- Seniority is inferred from job titles (entry / mid / senior / staff+).
        """
    )
    st.dataframe(
        skills_ft.skill.value_counts().reset_index().rename(columns={"skill": "Skill", "count": "Postings"}),
        use_container_width=True, height=300,
    )
