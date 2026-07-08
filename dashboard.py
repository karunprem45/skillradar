"""SkillRadar dashboard.  Run:  streamlit run dashboard.py"""

import json

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.db import ROOT, engine

# monochrome black & white theme — lightness carries order, outlines carry the mark
INK = "#ffffff"
INK_MUTED = "#b3b2ab"
GRID = "#2e2e2c"
LINE = "#ffffff"                       # bar outline
FILL = "rgba(255,255,255,0.12)"        # bar fill behind the outline
ORDINAL_FILLS = [                      # entry -> staff+ (opacity steps = ordinal ramp)
    "rgba(255,255,255,0.06)",
    "rgba(255,255,255,0.22)",
    "rgba(255,255,255,0.48)",
    "rgba(255,255,255,0.85)",
]
FONT = '"Inter", system-ui, sans-serif'

METROS = {
    "Boston": ["Boston", "Suffolk County"],
    "New York": ["New York", "Manhattan", "Brooklyn", "Queens"],
    "San Francisco": ["San Francisco"],
    "Seattle": ["Seattle", "King County", "Bellevue"],
    "Austin": ["Austin", "Travis County"],
}
SENIORITY_ORDER = ["entry", "mid", "senior", "staff+"]

# short names for the narrow segment mini-charts
SHORT = {
    "Machine Learning": "ML",
    "Deep Learning": "DL",
    "Generative AI": "GenAI",
    "Experimentation": "Experiments",
    "Statistics": "Stats",
    "Data Visualization": "DataViz",
    "Data Governance": "Governance",
    "Data Warehousing": "Warehousing",
    "Data Modeling": "Modeling",
    "Computer Vision": "CV",
    "Prompt Engineering": "Prompting",
    "Feature Engineering": "Feat. Eng.",
    "GitHub Actions": "GH Actions",
    "Vector Databases": "Vector DBs",
    "Model Monitoring": "Monitoring",
    "REST APIs": "REST",
}

st.set_page_config(page_title="SkillRadar", page_icon="📡", layout="wide")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Inter:wght@400;500;600&display=swap');

    html, body, [class*="st-"], p, span, label {
        font-family: 'Inter', system-ui, sans-serif;
    }
    /* keep Streamlit's icon glyphs on their icon font (else they render as raw text) */
    span[data-testid="stIconMaterial"], [class*="material-symbols"] {
        font-family: 'Material Symbols Rounded' !important;
    }
    h1, h2, h3, div[data-testid="stMetricValue"], button[data-baseweb="tab"] {
        font-family: 'Space Grotesk', system-ui, sans-serif !important;
        letter-spacing: -0.01em;
    }

    @keyframes rise {
        from { opacity: 0; transform: translateY(16px); }
        to   { opacity: 1; transform: none; }
    }
    div[data-testid="stMetric"], div.stPlotlyChart, div[data-testid="stExpander"],
    div[data-testid="stVerticalBlockBorderWrapper"], h1, h2, h3 {
        animation: rise 0.7s cubic-bezier(0.2, 0.7, 0.3, 1) both;
    }
    div[data-testid="stColumn"]:nth-of-type(2) > div { animation-delay: 0.10s; }
    div[data-testid="stColumn"]:nth-of-type(3) > div { animation-delay: 0.20s; }
    div[data-testid="stColumn"]:nth-of-type(4) > div { animation-delay: 0.30s; }
    div[data-testid="stColumn"]:nth-of-type(5) > div { animation-delay: 0.40s; }

    div[data-testid="stMetric"] {
        background: #141413;
        border: 1px solid #3d3d3a;
        border-radius: 12px;
        padding: 14px 16px;
        transition: border-color 0.25s ease, transform 0.25s ease;
    }
    div[data-testid="stMetric"]:hover {
        border-color: #ffffff;
        transform: translateY(-2px);
    }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: #141413;
        border: 1px solid #3d3d3a;
        border-radius: 12px;
        transition: border-color 0.25s ease;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        border-color: #6a6a66;
    }

    button[data-baseweb="tab"] { font-size: 1.05rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=3600)
def load_data():
    jobs = pd.read_sql(
        "SELECT id, source, title, location, remote, salary_min, salary_max, seniority, ingested_at FROM jobs",
        engine,
    )
    skills = pd.read_sql("SELECT job_id, skill FROM job_skills", engine)
    return jobs, skills


def style(fig, height=420, left=0, right=70):
    fig.update_layout(
        height=height,
        margin=dict(l=left, r=right, t=8, b=0),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT, color=INK_MUTED, size=13),
        showlegend=False,
        bargap=0.35,
        hoverlabel=dict(bgcolor="#141413", bordercolor=LINE, font=dict(color=INK)),
    )
    fig.update_xaxes(gridcolor=GRID, zeroline=False, linecolor=GRID)
    fig.update_yaxes(gridcolor="rgba(0,0,0,0)", zeroline=False)
    return fig


def hbar(labels, values, text=None, compact=False):
    fig = go.Figure(
        go.Bar(
            x=values, y=labels, orientation="h",
            marker=dict(color=FILL, cornerradius=4, line=dict(color=LINE, width=1.5)),
            text=text, textposition="outside", textfont=dict(color=INK),
            cliponaxis=False,
            hovertemplate="%{y}: %{x}<extra></extra>",
        )
    )
    fig.update_yaxes(autorange="reversed", automargin=True)
    if compact:
        # narrow-column mode: label lives inside the bar, no axes at all
        fig.update_traces(
            text=[f"{lbl}  ·  {txt}" for lbl, txt in zip(labels, text)],
            textposition="auto", insidetextanchor="start",
            textfont=dict(color=INK, size=12),
        )
        fig.update_xaxes(visible=False)
        fig.update_yaxes(showticklabels=False)
    return fig


def median_mid(df):
    with_salary = df.dropna(subset=["salary_min", "salary_max"])
    if not len(with_salary):
        return None
    return ((with_salary.salary_min + with_salary.salary_max) / 2).median()


jobs, skills = load_data()

full_text = jobs[jobs.source != "adzuna"]
skills_ft = skills[skills.job_id.isin(full_text.id)]

st.title("📡 SkillRadar")
st.caption(
    "Live intelligence on the data-careers job market — postings ingested daily, "
    "skills extracted automatically. github.com/karunprem45/skillradar"
)

tab_overview, tab_segments, tab_ml = st.tabs(["Market overview", "Segment analysis", "ML lab"])

# ================= DIVISION 1: MARKET OVERVIEW =================
with tab_overview:
    llm_pct = skills_ft[skills_ft.skill.isin(["LLMs", "Generative AI", "RAG"])].job_id.nunique() / len(full_text) * 100
    salaries = jobs.dropna(subset=["salary_min", "salary_max"])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Job postings tracked", f"{len(jobs):,}")
    c2.metric("With salary data", f"{len(salaries):,}")
    c3.metric("LLM/GenAI demand", f"{llm_pct:.0f}%")
    c4.metric("Median salary (US)", f"${median_mid(jobs) / 1000:.0f}k")

    st.write("")

    left, right = st.columns(2)

    with left, st.container(border=True):
        st.subheader("Most in-demand skills")
        st.caption(f"Share of {len(full_text)} full-description postings mentioning each skill")
        top = skills_ft.skill.value_counts().head(15)
        pct = (top / len(full_text) * 100).round(0)
        st.plotly_chart(
            style(hbar(top.index, top.values, text=[f"{p:.0f}%" for p in pct])),
            use_container_width=True,
        )

    with right, st.container(border=True):
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

    left, right = st.columns(2)

    with left, st.container(border=True):
        st.subheader("Postings by metro area")
        st.caption("US postings (Adzuna), median salary labeled")
        rows = []
        for metro, needles in METROS.items():
            mask = jobs.location.fillna("").str.contains("|".join(needles), case=False)
            metro_jobs = jobs[mask]
            med = median_mid(metro_jobs)
            if med:
                rows.append({"metro": metro, "n": len(metro_jobs.dropna(subset=["salary_min"])), "median": med})
        metros = pd.DataFrame(rows).sort_values("n", ascending=False)
        st.plotly_chart(
            style(hbar(metros.metro, metros.n, text=[f"${m / 1000:.0f}k" for m in metros["median"]])),
            use_container_width=True,
        )

    with right, st.container(border=True):
        st.subheader("Seniority mix")
        st.caption("Inferred from titles across all postings")
        sen = jobs.seniority.value_counts().reindex(SENIORITY_ORDER).fillna(0)
        fig = go.Figure(
            go.Bar(
                x=SENIORITY_ORDER, y=sen.values,
                marker=dict(color=ORDINAL_FILLS, cornerradius=4, line=dict(color=LINE, width=1.5)),
                text=[f"{int(v):,}" for v in sen.values], textposition="outside",
                textfont=dict(color=INK), cliponaxis=False,
                hovertemplate="%{x}: %{y}<extra></extra>",
            )
        )
        st.plotly_chart(style(fig), use_container_width=True)

# ================= DIVISION 2: SEGMENT ANALYSIS =================
with tab_segments:
    st.caption("Slice the market by a dimension — each segment gets its own profile")

    dim = st.selectbox(
        "Segment by",
        ["Seniority", "Metro area", "Source", "Remote vs onsite"],
        label_visibility="collapsed",
    )

    segments = []
    if dim == "Seniority":
        for level in SENIORITY_ORDER:
            segments.append((level.title(), jobs[jobs.seniority == level]))
    elif dim == "Metro area":
        for metro, needles in METROS.items():
            mask = jobs.location.fillna("").str.contains("|".join(needles), case=False)
            segments.append((metro, jobs[mask]))
    elif dim == "Source":
        for source in jobs.source.value_counts().index:
            segments.append((source.title(), jobs[jobs.source == source]))
    else:
        segments = [
            ("Remote", jobs[jobs.remote == True]),  # noqa: E712
            ("Onsite / unspecified", jobs[jobs.remote != True]),  # noqa: E712
        ]

    segments = [(name, seg) for name, seg in segments if len(seg) >= 5]

    for start in range(0, len(segments), 4):
        cols = st.columns(min(4, len(segments) - start))
        for col, (name, seg) in zip(cols, segments[start:start + 4]):
            with col, st.container(border=True):
                med = median_mid(seg)
                st.metric(
                    f"{name} · postings", f"{len(seg):,}",
                    f"${med / 1000:.0f}k median" if med else "no salary data",
                    delta_color="off",
                )
                seg_skills = skills[skills.job_id.isin(seg.id)]
                top_seg = seg_skills.skill.value_counts().head(6)
                if len(top_seg):
                    n_with_skills = seg_skills.job_id.nunique()
                    seg_pct = top_seg / n_with_skills * 100
                    st.plotly_chart(
                        style(hbar(
                            [SHORT.get(s, s) for s in seg_pct.index], seg_pct.values,
                            text=[f"{p:.0f}%" for p in seg_pct.values],
                            compact=True,
                        ), height=230, left=0, right=8),
                        use_container_width=True,
                        key=f"seg-{dim}-{name}",
                    )
                else:
                    st.caption("not enough skill data")

    st.divider()

    with st.expander("Data notes & sources"):
        st.markdown(
            """
- **Sources:** Adzuna (US, salaries), Remotive, Jobicy, The Muse, Arbeitnow — ingested daily at 11:00 UTC via GitHub Actions.
- **Skill extraction** is rule-based (curated ~90-skill vocabulary, word-boundary regex) — free and reproducible.
- Adzuna's free API truncates descriptions, so **skill percentages use only full-description sources**; Adzuna powers salary and metro stats.
- Segment skill percentages are within postings that have at least one extracted skill.
- Seniority is inferred from job titles (entry / mid / senior / staff+).
            """
        )
        st.dataframe(
            skills_ft.skill.value_counts().reset_index().rename(columns={"skill": "Skill", "count": "Postings"}),
            use_container_width=True, height=300,
        )

# ================= DIVISION 3: ML LAB =================
with tab_ml:
    st.caption("Models trained on the collected postings — retrained daily by the pipeline")

    def load_json(name):
        path = ROOT / "data" / name
        return json.loads(path.read_text()) if path.exists() else None

    model = load_json("model_artifacts.json")
    eval_metrics = load_json("eval_metrics.json")
    clusters = load_json("role_clusters.json")

    if model and eval_metrics:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Extraction F1", f"{eval_metrics['f1']:.3f}",
                  f"{eval_metrics['n_postings']}-posting gold set", delta_color="off")
        c2.metric("Salary model MAE", f"${model['mae'] / 1000:.0f}k",
                  f"-{model['mae_improvement_pct']:.0f}% vs baseline", delta_color="inverse")
        c3.metric("Salary model R²", f"{model['r2']:.2f}",
                  f"{model['n_postings']} postings", delta_color="off")
        c4.metric("Role archetypes", f"{clusters['k']}" if clusters else "—",
                  "KMeans on titles+skills", delta_color="off")

    st.write("")
    left, right = st.columns(2)

    with left, st.container(border=True):
        st.subheader("Skill salary premiums")
        st.caption("Ridge coefficients: salary shift when a posting demands the skill, all else fixed")
        if model:
            prem = pd.DataFrame(model["premiums"])
            fig = go.Figure(
                go.Bar(
                    x=prem.delta, y=prem.skill, orientation="h",
                    marker=dict(color=FILL, cornerradius=4, line=dict(color=LINE, width=1.5)),
                    text=[f"{d / 1000:+,.1f}k" for d in prem.delta],
                    textposition="outside", textfont=dict(color=INK), cliponaxis=False,
                    hovertemplate="%{y}: %{x:+,.0f}<extra></extra>",
                )
            )
            fig.update_yaxes(autorange="reversed", automargin=True)
            st.plotly_chart(style(fig, height=440), use_container_width=True)

    with right, st.container(border=True):
        st.subheader("Data growth")
        st.caption("Cumulative postings collected by the daily pipeline")
        growth = jobs.copy()
        growth["day"] = pd.to_datetime(growth.ingested_at).dt.date
        daily = growth.groupby("day").size().cumsum()
        fig = go.Figure(
            go.Scatter(
                x=list(daily.index), y=daily.values, mode="lines+markers",
                line=dict(color=LINE, width=2),
                marker=dict(size=8, color="#0a0a0a", line=dict(color=LINE, width=1.5)),
                hovertemplate="%{x}: %{y} postings<extra></extra>",
            )
        )
        fig.update_yaxes(rangemode="tozero", tickformat=",d")
        st.plotly_chart(style(fig, height=440, right=20), use_container_width=True)

    if clusters:
        st.subheader("Role archetypes")
        st.caption("KMeans clusters over TF-IDF of job titles + extracted skills")
        cl = clusters["clusters"]
        for start in range(0, len(cl), 3):
            cols = st.columns(min(3, len(cl) - start))
            for idx, (col, cluster) in enumerate(zip(cols, cl[start:start + 3])):
                with col, st.container(border=True):
                    st.metric(
                        cluster["label"], f"{cluster['size']:,} postings",
                        f"${cluster['median_salary'] / 1000:.0f}k median" if cluster["median_salary"] else "no salary data",
                        delta_color="off",
                    )
                    top = cluster["top_skills"]
                    st.plotly_chart(
                        style(hbar(
                            [SHORT.get(t["skill"], t["skill"]) for t in top],
                            [t["share"] for t in top],
                            text=[f"{t['share']}%" for t in top],
                            compact=True,
                        ), height=210, left=0, right=8),
                        use_container_width=True,
                        key=f"cluster-{start + idx}",
                    )

    with st.expander("Model notes"):
        st.markdown(
            """
- **Salary model:** HistGradientBoosting on skills (multi-hot), seniority, metro, remote flag → salary midpoint;
  80/20 train/test split. Ridge regression provides the interpretable per-skill premiums.
- **R² is modest by design honesty:** most salary postings come from Adzuna, whose API truncates descriptions,
  leaving sparse skill features. It improves as full-text sources accumulate.
- **Extraction quality** measured against a hand-labeled gold set (`data/gold_set.json`, `python -m src.evaluate`).
- **Clusters:** KMeans (k=6) on TF-IDF of title + skill names; labels are the two most frequent title words.
- Everything retrains daily in CI on the fresh data: `train_salary` + `cluster_roles` run after ingestion.
            """
        )
