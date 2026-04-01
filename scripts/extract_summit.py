import sys
import json
import requests
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from auth import client
from bs4 import BeautifulSoup
from datetime import date
from utils.helpers import HEADERS, parse_salary

BUCKET = 'raw'

def scrape_summit() -> list[dict]:
    url = (
        "https://summitrecruitment-search.com/jobs/job-category/"
        "data-science-machine-learning-artificial-intelligence/"
    )
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
 
    jobs = []
    for article in soup.select("article.latest-news-post"):
        title_el = article.select_one(".entry-title a")
        if not title_el:
            continue
 
        title = title_el.get_text(strip=True)
        application_url = title_el.get("href", "")
 
        # meta data extraction
        # Structure inside .jobs-meta p:
        #   <b>Salary:</b>\nMonthly Gross...<br>
        #   <b>Location:</b>\nNairobi, Kenya<br>
        #   ...
        #
        # BUG IN ORIGINAL: breaking on <br> means we grab nothing,
        # because the value text comes AFTER the <br> that immediately
        # follows the <b>. Fix: collect ALL text siblings until the
        # next <b> tag, skipping <br> elements silently.
        meta = {}
        meta_p = article.select_one(".jobs-meta p")
        if meta_p:
            b_tags = meta_p.find_all("b")
            for i, b in enumerate(b_tags):
                key = b.get_text(strip=True).rstrip(":")
                # Collect every NavigableString between this <b> and
                # the next <b> (or end of parent)
                value_parts = []
                node = b.next_sibling
                next_b = b_tags[i + 1] if i + 1 < len(b_tags) else None
                while node is not None and node != next_b:
                    if hasattr(node, "name"):
                        if node.name == "br":
                            pass  # skip line breaks, keep going
                        else:
                            value_parts.append(node.get_text(" ", strip=True))
                    else:
                        # NavigableString
                        text = str(node).strip()
                        if text:
                            value_parts.append(text)
                    node = node.next_sibling
                meta[key] = " ".join(value_parts).strip()
 
        salary_raw = meta.get("Salary") or None
        salary_currency, salary_min, salary_max = parse_salary(salary_raw)
 
        jobs.append({
            "source": "summit_recruitment",
            "title": title,
            "company": None,
            "description": None,
            "salary_min": salary_min,
            "salary_max": salary_max,
            "salary_currency": salary_currency,
            "salary_raw": salary_raw,
            "career_level": meta.get("Career Level") or None,
            "job_type": meta.get("Job Type") or None,
            "location": meta.get("Location") or None,
            "deadline": meta.get("Deadline for applications") or None,
            "application_url": application_url,
            "posted_at": None,
        })
 
    return jobs

def save_to_storage(jobs):
    """create folder first on supabase"""
    today = date.today()
    file = f"extracted_{today}.json"
    path = f"summit/{file}"
    payload = json.dumps(jobs, indent=4).encode("utf-8")

    client.storage.from_(BUCKET).upload(
        path=path,
        file=payload,
        file_options={
            "content-type": "application/json",
            "upsert": "true"
        }
    )

    print(f"Saved {len(jobs)} to {path}")

def run_summit_scraper():
    """run summit funcs as a scraper"""
    jobs = scrape_summit()
    print(f"Scraped {len(jobs)}")
    print(f"Saving to storage...")
    save_to_storage(jobs)
    print("Scraping complete!")