"""Phase 2: LLM skill extraction.

Sends each unprocessed job description to Claude Haiku and stores the
structured result (skills + seniority) in the database.

Run:  python -m src.extract              # process all unextracted jobs
      python -m src.extract --limit 50   # process a sample first
"""

import argparse
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

import anthropic
from dotenv import load_dotenv

from src.db import Job, JobSkill, Session
from src.normalize import normalize

load_dotenv()

MODEL = "claude-haiku-4-5-20251001"
MAX_DESC_CHARS = 6000
WORKERS = 8

PROMPT = """Extract structured data from this job posting.

Title: {title}
Description: {description}

Return ONLY a JSON object, no other text:
{{"skills": [...], "seniority": "..."}}

Rules:
- "skills": every concrete technical skill, tool, framework, platform, or method the posting
  asks for (e.g. "Python", "Docker", "A/B Testing", "LLMs"). Use short canonical names.
  Exclude soft skills (communication, teamwork) and generic words (software, technology).
- "seniority": one of "entry", "mid", "senior", "staff+". Infer from title and requirements
  (0-2 yrs = entry, 2-5 = mid, 5-8 or Senior title = senior, Staff/Principal/Lead = staff+)."""

client = anthropic.Anthropic()


def extract_one(job_id, title, description):
    resp = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": PROMPT.format(title=title, description=description[:MAX_DESC_CHARS]),
        }],
    )
    text = resp.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```")[1].removeprefix("json").strip()
    data = json.loads(text)
    skills = sorted({normalize(s) for s in data.get("skills", []) if s and len(s) < 80})
    seniority = data.get("seniority")
    return job_id, skills, seniority if seniority in ("entry", "mid", "senior", "staff+") else None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    session = Session()
    query = session.query(Job.id, Job.title, Job.description).filter(Job.extracted.is_(False))
    if args.limit:
        query = query.limit(args.limit)
    jobs = query.all()
    print(f"Extracting skills from {len(jobs)} postings with {MODEL}...")

    done, failed = 0, 0
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = [pool.submit(extract_one, *job) for job in jobs]
        for future in as_completed(futures):
            try:
                job_id, skills, seniority = future.result()
            except Exception as e:
                failed += 1
                print(f"  extraction failed: {e}")
                continue
            # writes happen only on this main thread
            session.query(JobSkill).filter(JobSkill.job_id == job_id).delete()
            for skill in skills:
                session.add(JobSkill(job_id=job_id, skill=skill))
            session.query(Job).filter(Job.id == job_id).update(
                {"extracted": True, "seniority": seniority}
            )
            done += 1
            if done % 50 == 0:
                session.commit()
                print(f"  {done}/{len(jobs)} done")

    session.commit()
    total_skills = session.query(JobSkill).count()
    print(f"\nDone. {done} extracted, {failed} failed. {total_skills} skill rows total.")
    session.close()


if __name__ == "__main__":
    main()
