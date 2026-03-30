import os
import sys
import json
import time
import requests
from pathlib import Path
from datetime import date
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))
from auth import client

load_dotenv()

APP_ID = os.getenv("ADZUNA_APP_ID")
APP_KEY = os.getenv("ADZUNA_API_KEY")
BUCKET = "raw"

KEYWORDS = [
    "data engineer",
    "data scientist",
    "software engineer",
    "machine learning",
    "AI engineer",
]

def fetch_keyword(keyword: str) -> list[dict]:
    jobs = []
    page = 1

    while True:
        response = requests.get(
            f"https://api.adzuna.com/v1/api/jobs/gb/search/{page}",
            params={
                "app_id": APP_ID,
                "app_key": APP_KEY,
                "what": keyword,           # correct param — not "category"
                "results_per_page": 50,    # max allowed
                "max_days_old": 30,
                "content-type": "application/json",
            },
            headers={"Accept": "application/json"},
        )

        if response.status_code != 200:
            print(f"  Error '{keyword}' page {page}: {response.status_code}")
            break

        data = response.json()
        batch = data.get("results", [])  # note: Adzuna uses "results" not "jobs"

        if not batch:
            break

        # tag each job with source metadata
        for job in batch:
            job["_keyword"] = keyword

        jobs.extend(batch)

        # Adzuna returns total count — stop when we have everything
        total = data.get("count", 0)
        if len(jobs) >= total or len(batch) < 50:
            break

        page += 1
        time.sleep(0.5)

    return jobs


def fetch_all_jobs() -> list[dict]:
    all_jobs = []

    for keyword in KEYWORDS:
        jobs = fetch_keyword(keyword)
        print(f"'{keyword}': {len(jobs)} jobs")
        all_jobs.extend(jobs)
        time.sleep(0.3)

    return all_jobs


def save_to_storage(jobs: list[dict]):
    date_today = date.today().isoformat()
    filename = f"extracted_{date_today}.json"
    path = f"adzuna/{filename}"

    payload = json.dumps(jobs, indent=2).encode("utf-8")

    client.storage.from_(BUCKET).upload(
        path=path,
        file=payload,
        file_options={"content-type": "application/json", "upsert": "true"},
    )

    print(f"\nSaved {len(jobs)} jobs to {BUCKET}/{path}")


if __name__ == "__main__":
    jobs = fetch_all_jobs()
    print(f"\nTotal: {len(jobs)} jobs fetched")
    save_to_storage(jobs)