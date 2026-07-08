"""Push notifications for freshly ingested postings.

After each pipeline run, finds postings ingested in the lookback window that
match the alert filter and pushes a summary via ntfy.sh (free, no account:
subscribe to your topic in the ntfy mobile app to receive them).

Config via env (.env locally, repo secrets in CI):
  NTFY_TOPIC      — ntfy.sh topic to publish to (required to actually send)
  ALERT_SENIORITY — comma-separated levels to alert on (default: entry,mid)
  ALERT_HOURS     — lookback window in hours (default: 8)

Run:  python -m src.alerts
"""

import os
from datetime import datetime, timedelta

import requests
from dotenv import load_dotenv

from src.db import ROOT, Job, Session

load_dotenv(ROOT / ".env")

NTFY_TOPIC = os.getenv("NTFY_TOPIC")
ALERT_SENIORITY = [s.strip() for s in os.getenv("ALERT_SENIORITY", "entry,mid").split(",")]
ALERT_HOURS = int(os.getenv("ALERT_HOURS", "8"))
MAX_LISTED = 8


def find_new_matches(session):
    cutoff = datetime.utcnow() - timedelta(hours=ALERT_HOURS)
    return (
        session.query(Job)
        .filter(Job.ingested_at >= cutoff, Job.seniority.in_(ALERT_SENIORITY))
        .order_by(Job.ingested_at.desc())
        .all()
    )


def format_message(matches):
    lines = []
    for job in matches[:MAX_LISTED]:
        salary = f" · ${(job.salary_min + job.salary_max) / 2000:.0f}k" if job.salary_min and job.salary_max else ""
        where = job.location or ("remote" if job.remote else "")
        lines.append(f"• {job.title} — {job.company or '?'} ({where}){salary}")
    if len(matches) > MAX_LISTED:
        lines.append(f"…and {len(matches) - MAX_LISTED} more")
    return "\n".join(lines)


def send(title, message):
    resp = requests.post(
        f"https://ntfy.sh/{NTFY_TOPIC}",
        data=message.encode("utf-8"),
        headers={"Title": title, "Tags": "satellite", "Priority": "default"},
        timeout=30,
    )
    resp.raise_for_status()


def main():
    session = Session()
    matches = find_new_matches(session)
    session.close()

    print(f"{len(matches)} new {'/'.join(ALERT_SENIORITY)} postings in the last {ALERT_HOURS}h")
    if not matches:
        return
    if not NTFY_TOPIC:
        print("NTFY_TOPIC not set — printing instead of sending:\n")
        print(format_message(matches))
        return
    send(f"SkillRadar: {len(matches)} new opening{'s' if len(matches) > 1 else ''}", format_message(matches))
    print(f"pushed to ntfy.sh/{NTFY_TOPIC}")


if __name__ == "__main__":
    main()
