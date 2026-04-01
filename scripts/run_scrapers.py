"""
Runner script, orchestrates all scrapers and writes combined output.

Can also be imported into an Airflow DAGs to call each
extract_* function individually.
"""
from extract_fuzu import run_fuzu_scraper
from extract_opened_career import run_opened_scraper
from extract_summit import run_summit_scraper
from extract_brighter_monday import run_brighter_scraper

BUCKET = "raw"

def run_all():
    """
    refactor this func to run the scripts individually
    """
    print("Running Opened Career scraper")
    run_opened_scraper()

    # run the summit scraper
    print("Running Summit scraper...")
    run_summit_scraper()

    # run the fuzu crawler
    #run_fuzu_scraper()

    # run the brighter monday scraper
    print("Running Brighter Monday scraper...")
    run_brighter_scraper()

if __name__ == "__main__":
    try:
        run_all()
        print("Scraping done.")
    except Exception as e:
        print(f"Error: {e}")

