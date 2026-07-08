"""Database models and session setup for SkillRadar."""

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import Boolean, Column, Date, DateTime, Float, Integer, String, Text, create_engine, func
from sqlalchemy.orm import declarative_base, sessionmaker

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{ROOT / 'data' / 'skillradar.db'}")

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True)
    source = Column(String(32), nullable=False)          # adzuna | remotive | arbeitnow
    source_id = Column(String(128), nullable=False, unique=True)
    title = Column(String(512), nullable=False)
    company = Column(String(256))
    location = Column(String(256))
    remote = Column(Boolean)
    salary_min = Column(Float)
    salary_max = Column(Float)
    description = Column(Text)
    url = Column(String(1024))
    posted_at = Column(Date)
    ingested_at = Column(DateTime, server_default=func.now())
    extracted = Column(Boolean, default=False)           # set True after LLM skill extraction
    seniority = Column(String(32))                       # entry | mid | senior | staff+ (from extraction)


class JobSkill(Base):
    __tablename__ = "job_skills"

    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, nullable=False, index=True)
    skill = Column(String(128), nullable=False, index=True)   # canonical skill name
    method = Column(String(16), default="rules")              # rules | llm


def init_db():
    Base.metadata.create_all(engine)
