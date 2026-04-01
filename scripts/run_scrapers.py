"""
Runner script — orchestrates all scrapers and writes combined output.

Can also be imported into an Airflow / Prefect DAG to call each
extract_* function individually.

Usage:
    python run_scrapers.py
"""

import json
from extract_fuzu import scrape_fuzu
from extract_opened_career import run_opened_scraper
from extract_summit import run_summit_scraper
from extract_brighter_monday import scrape_brighter_monday

BUCKET = "raw"

def run_all(output_path: str = "jobs_output.json") -> list[dict]:
    """
    refactor this func to run the scripts individually
    """
    #all_jobs = []
    """
    print("Scraping Fuzu …")
    fuzu_jobs = scrape_fuzu(page=1)
    print(f"  → {len(fuzu_jobs)} jobs")
    all_jobs.extend(fuzu_jobs)
    """

    """print("Scraping Opened Career internships …")
    oc_intern = scrape_internships(page=1)
    print(f"  → {len(oc_intern)} internships")
    all_jobs.extend(oc_intern)

    print("Scraping Opened Career data/AI/ML search …")
    oc_search = scrape_search()
    print(f"  → {len(oc_search)} jobs")
    all_jobs.extend(oc_search)"""
    #run_opened_scraper()

    """print("Scraping Summit Recruitment (DS/ML/AI) …")
    summit_jobs = scrape_summit()
    print(f"  → {len(summit_jobs)} jobs")
    all_jobs.extend(summit_jobs)"""

    # run the summit scraper
    run_summit_scraper()

    """print("Scraping Brighter Monday (IT & Telecoms) …")
    bm_jobs = scrape_brighter_monday(page=1)
    print(f"  → {len(bm_jobs)} jobs")
    all_jobs.extend(bm_jobs)"""

    """with open(output_path, "w") as f:
        json.dump(all_jobs, f, indent=2, ensure_ascii=False)

    print(f"\nTotal: {len(all_jobs)} jobs saved to {output_path}")
    return all_jobs"""

if __name__ == "__main__":
    jobs = run_all()
    # Quick preview
    """for job in jobs[:3]:
        print(json.dumps(job, indent=2, ensure_ascii=False))"""