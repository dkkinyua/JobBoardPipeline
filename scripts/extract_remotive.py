import json
import requests
import sys
import time
from pathlib import Path
from datetime import date

sys.path.insert(0, str(Path(__file__).parent.parent))
from auth import client

"""
get jobs per category
get all jobs, create an empty list, extend jobs to that list, return all jobs
save all jobs to supabase bucket
"""

BUCKET = "raw"
categories = ["software-development", 'ai-ml', 'data']

def get_jobs_per_category(category):
    URL = "https://remotive.com/api/remote-jobs?category=software-dev"
    headers = {
        "Content-Type": "applcation/json"
    }
    params = {
        "category": category,
    }

    response = requests.get(url=URL, params=params, headers=headers)
    if response.status_code != 200:
        return response.status_code, response.text
    
    data = response.json().get("jobs", []) # return content in the jobs list, else return an empty list

    return data

def get_all_jobs(categories):
    """get all jobs in all categories"""
    all_jobs = []
    for category in categories:
        jobs = get_jobs_per_category(category)
        print(f"Jobs fetched: {len(jobs)} for {category}")
        all_jobs.extend(jobs)

        time.sleep(0.5) # respectful of the api

    return all_jobs

def save_jobs(jobs):
    date_today = date.today().isoformat()
    filename = f"extracted_{date_today}.json"
    path = f"remotive/{filename}"

    payload = json.dumps(jobs, indent=2).encode("utf-8")

    client.storage.from_(BUCKET).upload(
        path=path,
        file=payload,
        file_options={"content-type": "application/json", "upsert": "true"},
    )

    print(f"Saved {len(jobs)} jobs to {BUCKET}/{path}")
    return path

if __name__ == "__main__":
    jobs = get_all_jobs(categories)
    save_jobs(jobs)
#print(get_remotive())
