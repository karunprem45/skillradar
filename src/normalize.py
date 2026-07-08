"""Skill name normalization: map the many spellings of a skill to one canonical name."""

ALIASES = {
    # languages
    "python3": "Python", "python 3": "Python",
    "golang": "Go",
    "js": "JavaScript", "javascript": "JavaScript", "typescript": "TypeScript",
    "postgres": "PostgreSQL", "postgresql": "PostgreSQL",
    "ms sql": "SQL Server", "mssql": "SQL Server", "sql server": "SQL Server",
    # ML / DS
    "sklearn": "scikit-learn", "scikit learn": "scikit-learn", "scikitlearn": "scikit-learn",
    "tf": "TensorFlow", "tensorflow": "TensorFlow", "pytorch": "PyTorch", "torch": "PyTorch",
    "xgb": "XGBoost", "xgboost": "XGBoost",
    "hugging face": "Hugging Face", "huggingface": "Hugging Face",
    "llms": "LLMs", "llm": "LLMs", "large language models": "LLMs",
    "genai": "Generative AI", "gen ai": "Generative AI", "generative ai": "Generative AI",
    "nlp": "NLP", "natural language processing": "NLP",
    "cv": "Computer Vision", "computer vision": "Computer Vision",
    "rag": "RAG", "retrieval augmented generation": "RAG", "retrieval-augmented generation": "RAG",
    # data eng
    "aws": "AWS", "amazon web services": "AWS",
    "gcp": "GCP", "google cloud": "GCP", "google cloud platform": "GCP",
    "azure": "Azure", "microsoft azure": "Azure",
    "k8s": "Kubernetes", "kubernetes": "Kubernetes",
    "airflow": "Airflow", "apache airflow": "Airflow",
    "spark": "Spark", "apache spark": "Spark", "pyspark": "Spark",
    "kafka": "Kafka", "apache kafka": "Kafka",
    "dbt": "dbt",
    "databricks": "Databricks", "snowflake": "Snowflake", "bigquery": "BigQuery",
    "redshift": "Redshift",
    "ci/cd": "CI/CD", "cicd": "CI/CD", "ci cd": "CI/CD",
    "github actions": "GitHub Actions",
    "power bi": "Power BI", "powerbi": "Power BI", "tableau": "Tableau",
    "looker": "Looker",
    "excel": "Excel", "microsoft excel": "Excel",
    "etl": "ETL", "elt": "ETL",
    "docker": "Docker", "terraform": "Terraform",
    "mlflow": "MLflow", "mlops": "MLOps",
    "langchain": "LangChain",
    "fastapi": "FastAPI", "flask": "Flask", "django": "Django",
    "pandas": "pandas", "numpy": "NumPy",
    "a/b testing": "A/B Testing", "ab testing": "A/B Testing",
    "statistics": "Statistics", "statistical analysis": "Statistics",
    "machine learning": "Machine Learning", "ml": "Machine Learning",
    "deep learning": "Deep Learning", "dl": "Deep Learning",
    "data visualization": "Data Visualization", "dataviz": "Data Visualization",
    "sql": "SQL", "nosql": "NoSQL", "mongodb": "MongoDB", "redis": "Redis",
    "git": "Git", "linux": "Linux",
    "rest api": "REST APIs", "rest apis": "REST APIs", "restful apis": "REST APIs",
}


def normalize(skill):
    """Return the canonical name for a raw skill string."""
    cleaned = skill.strip().rstrip(".,;")
    return ALIASES.get(cleaned.lower(), cleaned)
