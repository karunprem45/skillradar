"""Phase 1 ingester: pull data/ML job postings into the jobs table.

US-only scope. Sources:
  - Adzuna (US, all job types)          — needs ADZUNA_APP_ID / ADZUNA_APP_KEY in .env
  - Remotive (US-eligible remote jobs)  — no key needed
  - Jobicy (US-eligible remote jobs)    — no key needed
  - The Muse (US city-level jobs)       — no key needed

Run:  python -m src.ingest
Re-running is safe: postings are deduped on source_id.
"""

import os
import re
from datetime import datetime

import requests
from dotenv import load_dotenv

from src.db import Job, Session, init_db

load_dotenv()

SEARCH_TERMS = ["data scientist", "machine learning engineer", "data engineer", "data analyst"]
ADZUNA_CITIES = ["Boston", "New York", "San Francisco", "Seattle", "Austin"]
# full-text sources are keyless/unmetered, so search them more broadly
FULLTEXT_TERMS = SEARCH_TERMS + [
    "machine learning", "ai engineer", "analytics engineer", "mlops",
    "business intelligence", "research scientist", "deep learning",
]

# crude filter so keyless generic boards only contribute relevant postings
RELEVANT = re.compile(
    r"data scien|machine learning|\bml\b|data engineer|data analy|mlops|\bai\b|artificial intelligence",
    re.IGNORECASE,
)

# US-only scope: remote postings must be open to US applicants...
US_ELIGIBLE = re.compile(
    r"usa|united states|u\.s\.|north america|americas|worldwide|anywhere", re.IGNORECASE
)
# ...and on-site postings must carry a US state code (e.g. "New York, NY")
US_STATE = re.compile(
    r",\s*(?:AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|"
    r"MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY|DC)\b"
)


def is_us_location(location):
    loc = location or ""
    return bool(US_ELIGIBLE.search(loc) or US_STATE.search(loc) or "Flexible / Remote" in loc)


def strip_html(text):
    return re.sub(r"<[^>]+>", " ", text or "").strip()


def parse_date(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date()
    except ValueError:
        return None


def fetch_adzuna():
    app_id = os.getenv("ADZUNA_APP_ID")
    app_key = os.getenv("ADZUNA_APP_KEY")
    if not app_id or not app_key:
        print("Adzuna: no API key set, skipping (add ADZUNA_APP_ID/ADZUNA_APP_KEY to .env)")
        return

    for term in SEARCH_TERMS:
        for city in ADZUNA_CITIES:
            resp = requests.get(
                "https://api.adzuna.com/v1/api/jobs/us/search/1",
                params={
                    "app_id": app_id,
                    "app_key": app_key,
                    "what": term,
                    "where": city,
                    "results_per_page": 50,
                    "content-type": "application/json",
                },
                timeout=30,
            )
            resp.raise_for_status()
            for item in resp.json().get("results", []):
                yield {
                    "source": "adzuna",
                    "source_id": f"adzuna:{item['id']}",
                    "title": item.get("title", ""),
                    "company": (item.get("company") or {}).get("display_name"),
                    "location": (item.get("location") or {}).get("display_name"),
                    "remote": None,
                    "salary_min": item.get("salary_min"),
                    "salary_max": item.get("salary_max"),
                    "description": item.get("description"),
                    "url": item.get("redirect_url"),
                    "posted_at": parse_date(item.get("created")),
                }


def fetch_remotive():
    for term in FULLTEXT_TERMS:
        resp = requests.get(
            "https://remotive.com/api/remote-jobs",
            params={"search": term, "limit": 100},
            timeout=30,
        )
        resp.raise_for_status()
        for item in resp.json().get("jobs", []):
            if not RELEVANT.search(item.get("title", "")):
                continue
            if not is_us_location(item.get("candidate_required_location")):
                continue
            yield {
                "source": "remotive",
                "source_id": f"remotive:{item['id']}",
                "title": item.get("title", ""),
                "company": item.get("company_name"),
                "location": item.get("candidate_required_location"),
                "remote": True,
                "salary_min": None,
                "salary_max": None,
                "description": strip_html(item.get("description")),
                "url": item.get("url"),
                "posted_at": parse_date(item.get("publication_date")),
            }


def fetch_jobicy():
    for industry in ("data-science", "engineering"):
        resp = requests.get(
            "https://jobicy.com/api/v2/remote-jobs",
            params={"count": 100, "industry": industry},
            timeout=30,
        )
        resp.raise_for_status()
        for item in resp.json().get("jobs", []):
            if not RELEVANT.search(item.get("jobTitle", "")):
                continue
            if not is_us_location(item.get("jobGeo")):
                continue
            yield {
                "source": "jobicy",
                "source_id": f"jobicy:{item['id']}",
                "title": item.get("jobTitle", ""),
                "company": item.get("companyName"),
                "location": item.get("jobGeo"),
                "remote": True,
                "salary_min": item.get("annualSalaryMin"),
                "salary_max": item.get("annualSalaryMax"),
                "description": strip_html(item.get("jobDescription")),
                "url": item.get("url"),
                "posted_at": parse_date(item.get("pubDate")),
            }


def fetch_themuse():
    for page in range(1, 21):
        resp = requests.get(
            "https://www.themuse.com/api/public/jobs",
            params={"category": "Data and Analytics", "page": page},
            timeout=30,
        )
        resp.raise_for_status()
        for item in resp.json().get("results", []):
            if not RELEVANT.search(item.get("name", "")):
                continue
            locations = ", ".join(loc["name"] for loc in item.get("locations", []))
            if not is_us_location(locations):
                continue
            yield {
                "source": "themuse",
                "source_id": f"themuse:{item['id']}",
                "title": item.get("name", ""),
                "company": (item.get("company") or {}).get("name"),
                "location": locations,
                "remote": "Flexible / Remote" in locations or None,
                "salary_min": None,
                "salary_max": None,
                "description": strip_html(item.get("contents")),
                "url": (item.get("refs") or {}).get("landing_page"),
                "posted_at": parse_date(item.get("publication_date")),
            }


def ingest():
    init_db()
    session = Session()
    existing = {sid for (sid,) in session.query(Job.source_id).all()}
    new_count, skipped = 0, 0

    for fetch in (fetch_adzuna, fetch_remotive, fetch_jobicy, fetch_themuse):
        source_new = 0
        try:
            for row in fetch():
                if row["source_id"] in existing or not row["description"]:
                    skipped += 1
                    continue
                session.add(Job(**row))
                existing.add(row["source_id"])
                source_new += 1
        except requests.RequestException as e:
            print(f"{fetch.__name__}: request failed ({e}), continuing with other sources")
        session.commit()
        print(f"{fetch.__name__}: +{source_new} new postings")
        new_count += source_new

    total = session.query(Job).count()
    print(f"\nDone. {new_count} new, {skipped} duplicates/empty skipped. Total in DB: {total}")
    session.close()


if __name__ == "__main__":
    ingest()
