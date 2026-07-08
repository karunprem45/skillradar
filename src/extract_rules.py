"""Free rule-based skill extraction (no API, no cost).

Matches a curated skill vocabulary against job descriptions with word-boundary
regexes. Serves as the baseline extractor; LLM extraction (src.extract) can be
layered on later and benchmarked against this.

Run:  python -m src.extract_rules
"""

import re

from src.db import Job, JobSkill, Session

# canonical skill -> surface forms to match (case-insensitive unless noted)
VOCAB = {
    "Python": ["python"],
    "SQL": ["sql"],
    "R": [],  # handled by custom pattern below (too many false positives otherwise)
    "Java": ["java(?!script)"],
    "Scala": ["scala(?!bility|ble)"],
    "C++": [r"c\+\+"],
    "JavaScript": ["javascript"],
    "TypeScript": ["typescript"],
    "Rust": ["rust(?!y)"],
    "SAS": ["sas"],
    "MATLAB": ["matlab"],
    "Machine Learning": ["machine learning", r"\bml\b"],
    "Deep Learning": ["deep learning"],
    "NLP": ["nlp", "natural language processing"],
    "Computer Vision": ["computer vision"],
    "LLMs": ["llms?", "large language models?"],
    "Generative AI": ["generative ai", "genai", "gen ai"],
    "RAG": ["rag", "retrieval[- ]augmented generation"],
    "Prompt Engineering": ["prompt engineering"],
    "Reinforcement Learning": ["reinforcement learning"],
    "Time Series": ["time[- ]series"],
    "Causal Inference": ["causal inference"],
    "A/B Testing": ["a/b test", "ab test", "a/b experiment"],
    "Statistics": ["statistics", "statistical (?:analysis|modeling|methods)"],
    "Experimentation": ["experimentation"],
    "Feature Engineering": ["feature engineering"],
    "scikit-learn": ["scikit[- ]?learn", "sklearn"],
    "TensorFlow": ["tensorflow"],
    "PyTorch": ["pytorch"],
    "Keras": ["keras"],
    "XGBoost": ["xgboost"],
    "Hugging Face": ["hugging ?face"],
    "LangChain": ["langchain"],
    "Transformers": ["transformers"],
    "pandas": ["pandas"],
    "NumPy": ["numpy"],
    "Spark": ["spark", "pyspark"],
    "Hadoop": ["hadoop"],
    "Kafka": ["kafka"],
    "Airflow": ["airflow"],
    "dbt": ["dbt"],
    "Dagster": ["dagster"],
    "Prefect": ["prefect"],
    "ETL": ["etl", "elt"],
    "Data Modeling": ["data model(?:ing|ling)"],
    "Data Warehousing": ["data warehous"],
    "Data Governance": ["data governance"],
    "Snowflake": ["snowflake"],
    "Databricks": ["databricks"],
    "BigQuery": ["bigquery"],
    "Redshift": ["redshift"],
    "PostgreSQL": ["postgres(?:ql)?"],
    "MySQL": ["mysql"],
    "SQL Server": ["sql server", "mssql"],
    "MongoDB": ["mongodb", "mongo"],
    "Redis": ["redis"],
    "Elasticsearch": ["elasticsearch", "elastic search"],
    "NoSQL": ["nosql"],
    "AWS": ["aws", "amazon web services"],
    "GCP": ["gcp", "google cloud"],
    "Azure": ["azure"],
    "SageMaker": ["sagemaker"],
    "Vertex AI": ["vertex ai"],
    "Docker": ["docker"],
    "Kubernetes": ["kubernetes", "k8s"],
    "Terraform": ["terraform"],
    "CI/CD": ["ci/cd", "cicd", "continuous integration"],
    "GitHub Actions": ["github actions"],
    "Jenkins": ["jenkins"],
    "Git": ["git(?!hub actions|lab)"],
    "Linux": ["linux"],
    "MLOps": ["mlops", "ml ops"],
    "MLflow": ["mlflow"],
    "Kubeflow": ["kubeflow"],
    "Model Monitoring": ["model monitoring", "model drift", "data drift"],
    "FastAPI": ["fastapi"],
    "Flask": ["flask"],
    "Django": ["django"],
    "REST APIs": ["rest(?:ful)? apis?"],
    "GraphQL": ["graphql"],
    "Streamlit": ["streamlit"],
    "Tableau": ["tableau"],
    "Power BI": ["power ?bi"],
    "Looker": ["looker"],
    "Excel": ["excel(?!lent|lence|led|s)"],
    "Matplotlib": ["matplotlib"],
    "Seaborn": ["seaborn"],
    "Plotly": ["plotly"],
    "Data Visualization": ["data visuali[sz]ation"],
    "Vector Databases": ["vector (?:database|db|store)", "pinecone", "weaviate", "chromadb", "faiss"],
    "Jupyter": ["jupyter"],
}

PATTERNS = {
    skill: re.compile(r"\b(?:" + "|".join(forms) + r")\b", re.IGNORECASE)
    for skill, forms in VOCAB.items()
    if forms
}
# "R" needs word-boundary + context to avoid matching initials/abbreviations
PATTERNS["R"] = re.compile(r"(?:\bR programming\b|[,/(]\s*R\s*[,/)]|\bin R\b)")

SENIORITY_RULES = [
    (re.compile(r"\b(?:staff|principal|lead|director|head of)\b", re.I), "staff+"),
    (re.compile(r"\bsenior|\bsr\.?\b", re.I), "senior"),
    (re.compile(r"\b(?:intern(?:ship)?|junior|jr\.?|entry[- ]level|graduate|working student|praktikum)\b", re.I), "entry"),
]


def extract_skills(text):
    return sorted(skill for skill, pattern in PATTERNS.items() if pattern.search(text))


def infer_seniority(title):
    for pattern, level in SENIORITY_RULES:
        if pattern.search(title):
            return level
    return "mid"


def main():
    session = Session()
    jobs = session.query(Job).all()
    print(f"Extracting skills from {len(jobs)} postings (rule-based, free)...")

    skill_rows = 0
    for job in jobs:
        session.query(JobSkill).filter(JobSkill.job_id == job.id, JobSkill.method == "rules").delete()
        text = f"{job.title}\n{job.description or ''}"
        for skill in extract_skills(text):
            session.add(JobSkill(job_id=job.id, skill=skill, method="rules"))
            skill_rows += 1
        if not job.seniority:
            job.seniority = infer_seniority(job.title)

    session.commit()
    print(f"Done. {skill_rows} skill rows across {len(jobs)} postings "
          f"(avg {skill_rows / max(len(jobs), 1):.1f} skills/posting).")
    session.close()


if __name__ == "__main__":
    main()
