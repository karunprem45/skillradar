"""Quick sanity-check stats for the jobs table.  Run:  python -m src.stats"""

from sqlalchemy import func

from src.db import Job, Session


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

    session.close()


if __name__ == "__main__":
    main()
