"""Quick sanity-check stats for the jobs table.  Run:  python -m src.stats"""

from sqlalchemy import func, select

from src.db import Job, JobSkill, Session


def main():
    session = Session()
    total = session.query(Job).count()
    print(f"Total postings: {total}\n")

    print("By source:")
    for source, n in session.query(Job.source, func.count()).group_by(Job.source):
        print(f"  {source:12} {n}")

    print("\nTop 10 job titles:")
    top = (
        session.query(Job.title, func.count().label("n"))
        .group_by(Job.title)
        .order_by(func.count().desc())
        .limit(10)
    )
    for title, n in top:
        print(f"  {n:3}  {title[:70]}")

    full_text = select(Job.id).where(Job.source != "adzuna")
    n_full = session.query(Job).filter(Job.source != "adzuna").count()
    print(f"\nTop 25 skills (from {n_full} full-description postings; "
          f"Adzuna excluded — its API truncates descriptions):")
    top_skills = (
        session.query(JobSkill.skill, func.count().label("n"))
        .filter(JobSkill.job_id.in_(full_text))
        .group_by(JobSkill.skill)
        .order_by(func.count().desc())
        .limit(25)
    )
    for skill, n in top_skills:
        print(f"  {n:4}  ({n / n_full * 100:4.1f}%)  {skill}")

    print("\nSeniority mix:")
    for level, n in session.query(Job.seniority, func.count()).group_by(Job.seniority).order_by(func.count().desc()):
        print(f"  {level or 'unknown':8} {n}")

    session.close()


if __name__ == "__main__":
    main()
