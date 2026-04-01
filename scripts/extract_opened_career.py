"""
Opened Career scrapers — Internships & Data/AI/ML search (Kenya).
Usage:
    from extract_opened_career import scrape_internships, scrape_search
    internships = scrape_internships(page=1)
    search_jobs = scrape_search(query="data, ai, machine learning", page=1)
"""
import re
import sys
import json
import requests
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from auth import client
from bs4 import BeautifulSoup
from datetime import date
from utils.helpers import HEADERS

BUCKET = "raw"

def _parse_page(url: str):
    """
    Fetches and extracts structured data from a single job page.
    """
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception:
        return f"Error: {resp.status_code}, {resp.text}"

    soup = BeautifulSoup(resp.text, "html.parser")

    content = soup.select_one(".entry-content")
    if not content:
        return {}

    text = content.get_text("\n", strip=True)

    salary_min = salary_max = 0
    salary_currency = ""
    salary_raw = ""
    location = deadline = job_type = career_level = None

    # --- Extract structured fields ---
    for line in text.splitlines():
        clean = line.strip().lower()

        if "location" in clean:
            location = line.split(":", 1)[-1].strip()

        elif "application deadline" in clean:
            deadline = line.split(":", 1)[-1].strip()

        elif "employment type" in clean:
            job_type = line.split(":", 1)[-1].strip()

        elif "education level" in clean:
            career_level = line.split(":", 1)[-1].strip()

        elif "ksh" in clean or "kes" in clean:
            salary_raw = line.strip()

            nums = re.findall(r"\d[\d,]*", line)
            if len(nums) >= 2:
                salary_min = int(nums[0].replace(",", ""))
                salary_max = int(nums[1].replace(",", ""))
            elif len(nums) == 1:
                salary_min = int(nums[0].replace(",", ""))

            salary_currency = "KES"

    return {
        "description": text[:2000],  # limit size
        "salary_min": salary_min,
        "salary_max": salary_max,
        "salary_currency": salary_currency,
        "salary_raw": salary_raw,
        "location": location,
        "deadline": deadline,
        "career_level": career_level,
        "job_type": job_type,
    }
    

def _parse_card(article, source: str) -> dict | None:
    link_tag = article.select_one("a[href]")
    if not link_tag:
        return None

    app_url = link_tag.get("href")

    title_tag = article.select_one("h5")
    title = title_tag.get_text(strip=True) if title_tag else None
    print(f"Length of titles: {len(title)}")

    # extract company from title
    company = None
    if title and " at " in title.lower():
        company = title.split(" at ")[-1].strip()

    # call parse page function
    details = _parse_page(app_url)

    return {
        "source": source,
        "title": title,
        "company": company,
        "description": details.get("description"),
        "salary_min": details.get("salary_min", 0),
        "salary_max": details.get("salary_max", 0),
        "salary_currency": details.get("salary_currency", ""),
        "salary_raw": details.get("salary_raw", ""),
        "career_level": details.get("career_level"),
        "job_type": details.get("job_type"),
        "location": details.get("location"),
        "deadline": details.get("deadline"),
        "application_url": app_url,
        "posted_at": None,
    }

def scrape_internships(page: int = 1) -> list[dict]:
    """
    Scrapes the Opened Career internships category page.

    Args:
        page: Pagination index (1-based).

    Returns:
        List of normalised internship job dicts.
    """
    url = (
        "https://openedcareer.com/category/internships/"
        if page == 1
        else f"https://openedcareer.com/category/internships/page/{page}/"
    )

    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    articles = soup.select("article")
    #print(f"Code: {resp.status_code}")
    #print(f"{soup.title}")
    #print(f"Articles scraped: {len(articles)}")
    #print(f"{resp.text[2000:]}")
    #print(resp.headers.get("Content-Encoding"))

    jobs = []
    for article in articles:
        job = _parse_card(article, source="opened_career_internships")
        if job:
            jobs.append(job)
    return jobs


def scrape_search(query: str = "data, ai, machine learning", page: int = 1) -> list[dict]:
    """
    Scrapes Opened Career search results for the given query.
    Also extracts structured fields (employment type, career level,
    application deadline) from the description bullet list where present.

    Args:
        query: Search string to pass to the WordPress ?s= param.
        page:  Pagination index (1-based).

    Returns:
        List of normalised job dicts (includes a bonus `deadline` field).
    """
    params = {"s": query}
    if page > 1:
        params["paged"] = page

    resp = requests.get("https://openedcareer.com/", headers=HEADERS, params=params, timeout=15)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    articles = soup.select("article")

    jobs = []
    for article in articles:
        base = _parse_card(article, source="opened_career_search")
        if not base:
            continue

        # Extract structured fields from the description bullet list
        career_level = job_type_field = deadline = None
        desc_tag = article.select_one(".pg")
        if desc_tag:
            for line in desc_tag.get_text("\n", strip=True).splitlines():
                line = line.strip().lstrip("•").strip()
                low = line.lower()
                if low.startswith("employment type"):
                    job_type_field = line.split(":", 1)[-1].strip()
                elif low.startswith("education level"):
                    career_level = line.split(":", 1)[-1].strip()
                elif low.startswith("application deadline"):
                    deadline = line.split(":", 1)[-1].strip()

        base.update({
            "career_level": career_level,
            "job_type": job_type_field or base["job_type"],
            "deadline": deadline,
        })
        jobs.append(base)

    return jobs

def save_to_storage(jobs):
    """create folder on supabase"""
    today = date.today()
    filename = f"extracted_{today}.json"
    path = f"/opened_career_jobs/{filename}"
    payload = json.dumps(jobs, indent=4).encode("utf-8")

    # send file to supabase client
    client.storage.from_(BUCKET).upload(
        path=path,
        file=payload,
        file_options={
            "content-type": "application/json",
            "upsert": "true"
        }   
    )

    print(f"Saved {len(jobs)} to {path}")

def save_internships_to_storage(jobs):
    """create folder on supabase"""
    today = date.today()
    filename = f"extracted_{today}.json"
    path = f"/opened_career_internships/{filename}"
    payload = json.dumps(jobs, indent=4).encode("utf-8")

    # send file to supabase client
    client.storage.from_(BUCKET).upload(
        path=path,
        file=payload,
        file_options={
            "content-type": "application/json",
            "upsert": "true"
        }   
    )

    print(f"Saved {len(jobs)} to {path}")

def run_opened_scraper():
    """runs the opened internships functions first, then run the search one next, saves to supabase"""
    print("Scraping Opened Career internships …")
    oc_intern = scrape_internships(page=1)
    print(f"Scraped {len(oc_intern)} internships")

    print("Scraping Opened Career data/AI/ML search …")
    oc_search = scrape_search()
    print(f"Scraped {len(oc_search)} jobs")

    print("Saving to storage...")
    save_to_storage(oc_search)
    save_to_storage(oc_intern)
    print("Saved to storage")



