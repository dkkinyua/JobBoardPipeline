import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import json
import time
import requests
from auth import client
from datetime import date

HIMALAYAS_URL = "https://himalayas.app/jobs/api/search"
BUCKET = "raw"
CATEGORIES = [
    "data engineer",
    "data scientist",
    "data analyst",
    "software engineer",
    "machine learning",
    "ai",
]

def fetch_category(category: str) -> list[dict]:
    jobs = []
    offset = 0
    limit = 20

    while True:
        response = requests.get(
            HIMALAYAS_URL,
            params={"q": category, "limit": limit, "offset": offset},
        )

        if response.status_code != 200:
            print(f"Error fetching '{category}' at offset {offset}: {response.status_code}")
            break

        batch = response.json().get("jobs", [])

        if not batch:
            break

        jobs.extend(batch)

        if len(batch) < limit:
            break

        offset += limit
        time.sleep(0.5)

    return jobs


def fetch_all_jobs(categories: list[str]) -> list[dict]:
    all_jobs = []

    for category in categories:
        jobs = fetch_category(category)
        print(f"  {category}: {len(jobs)} jobs fetched")
        all_jobs.extend(jobs)

    return all_jobs  # was missing


def save_to_storage(jobs: list[dict]) -> str:
    date_today = date.today().isoformat()
    filename = f"extracted_{date_today}.json"
    path = f"himalayas/{filename}"

    payload = json.dumps(jobs, indent=2).encode("utf-8")

    client.storage.from_(BUCKET).upload(
        path=path,
        file=payload,
        file_options={"content-type": "application/json", "upsert": "true"},
    )

    print(f"Saved {len(jobs)} jobs to {BUCKET}/{path}")
    return path

if __name__ == "__main__":
    jobs = fetch_all_jobs(CATEGORIES)
    print(f"\nTotal: {len(jobs)} jobs fetched")
    save_to_storage(jobs)