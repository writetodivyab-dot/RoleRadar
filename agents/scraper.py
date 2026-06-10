import yaml
import os
import time
import requests
from datetime import date
from playwright.sync_api import sync_playwright

def load_profile():
    path = os.path.join(os.path.dirname(__file__), '..', 'config', 'search_profile.yaml')
    with open(path) as f:
        return yaml.safe_load(f)

GREENHOUSE_COMPANIES = [
    'neuraflash', 'purestorage', 'neocol', 'litmos',
    'conga', 'pandadoc', 'gongio', 'axon', 'techholding',
    'nozominetworks', 'kunai', 'thevirtussolution', 'huntress', 'attainpartners',
    'natera', 'banyansoftware', 'formativgroup', 'cclfg'

]

def search_greenhouse(keywords: list[str]) -> list[dict]:
    jobs = []
    seen_urls = set()

    for company in GREENHOUSE_COMPANIES:
        try:
            print(f"  Greenhouse: checking {company}...")
            url = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs?content=true"
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                print(f"    Skipping {company} - status {response.status_code}")
                continue

            data = response.json()
            for job in data.get('jobs', []):
                title = job.get('title', '')
                job_url = job.get('absolute_url', '')
                location_text = job.get('location', {}).get('name', '')

                if not any(kw.lower() in title.lower() for kw in keywords):
                    continue

                location_lower = location_text.lower()
                is_remote = 'remote' in location_lower
                is_california = (
                    'san francisco' in location_lower or
                    'bay area' in location_lower or
                    'california' in location_lower or
                    ', ca' in location_lower or
                    'sf,' in location_lower
                )

                # Exclude Canada-only onsite roles
                is_canada_only = (
                    'canada' in location_lower and
                    not is_remote
                )

                if is_canada_only:
                    continue

                if not is_remote and not is_california:
                    continue

                if job_url not in seen_urls:
                    seen_urls.add(job_url)
                    jobs.append({
                        'title': title,
                        'company': company,
                        'location': location_text,
                        'url': job_url,
                        'description': job.get('content', '')[:500],
                        'source': 'greenhouse',
                        'date_found': str(date.today())
                    })

        except Exception as e:
            print(f"  Greenhouse error for {company}: {e}")
            continue

    return jobs


def search_linkedin(keywords: list[str], location: str) -> list[dict]:
    jobs = []
    seen_urls = set()

    exclude_titles = [
        'java', 'python', 'ruby', 'android', 'ios', 'data engineer',
        'data scientist', 'devops', 'backend', 'frontend', 'react',
        'angular', 'node', 'php', 'golang', '.net developer',
        'research scientist', 'phd', 'machine learning engineer',
        'research engineer', 'applied scientist'
    ]
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for keyword in keywords:
            try:
                url = f"https://www.linkedin.com/jobs/search/?keywords={keyword.replace(' ', '%20')}&location={location.replace(' ', '%20')}&f_TPR=r86400&f_JT=F"
                print(f"  LinkedIn: searching '{keyword}'...")
                page.goto(url, timeout=30000)
                time.sleep(3)

                for _ in range(3):
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(2)

                listings = page.query_selector_all('.job-search-card')
                for listing in listings:
                    try:
                        title_el = listing.query_selector('.base-search-card__title')
                        company_el = listing.query_selector('.base-search-card__subtitle')
                        location_el = listing.query_selector('.job-search-card__location')
                        link_el = listing.query_selector('a.base-card__full-link')

                        title = title_el.inner_text().strip() if title_el else ''
                        company = company_el.inner_text().strip() if company_el else ''
                        location_text = location_el.inner_text().strip() if location_el else ''
                        job_url = link_el.get_attribute('href') if link_el else ''

                        if not title or not job_url:
                            continue

                        if any(ex.lower() in title.lower() for ex in exclude_titles):
                            continue

                        location_lower = location_text.lower()
                        is_remote = 'remote' in location_lower
                        is_california = (
                            'san francisco' in location_lower or
                            'bay area' in location_lower or
                            'california' in location_lower or
                            ', ca' in location_lower or
                            'sf,' in location_lower or
                            'united states' in location_lower
                        )
                        is_canada_only = 'canada' in location_lower and not is_remote

                        if is_canada_only:
                            continue

                        if not is_remote and not is_california:
                            continue

                        if job_url not in seen_urls:
                            seen_urls.add(job_url)
                            jobs.append({
                                'title': title,
                                'company': company,
                                'location': location_text,
                                'url': job_url,
                                'description': '',
                                'source': 'linkedin',
                                'date_found': str(date.today())
                            })
                    except:
                        continue

            except Exception as e:
                print(f"  LinkedIn error for '{keyword}': {e}")
                continue

        browser.close()

    return jobs
    
def deduplicate(jobs: list[dict]) -> list[dict]:
    seen = set()
    unique = []
    for job in jobs:
        if job['url'] and job['url'] not in seen:
            seen.add(job['url'])
            unique.append(job)
    return unique

def discover_and_scrape() -> list[dict]:
    profile = load_profile()
    keywords = profile.get('target_roles', [])
    location = profile.get('location', {}).get('preferred', 'United States')

    all_jobs = []

    print("Searching LinkedIn...")
    linkedin_jobs = search_linkedin(keywords, location)
    print(f"  {len(linkedin_jobs)} jobs found on LinkedIn")
    all_jobs.extend(linkedin_jobs)

    print("Searching Greenhouse...")
    greenhouse_jobs = search_greenhouse(keywords)
    print(f"  {len(greenhouse_jobs)} jobs found on Greenhouse")
    all_jobs.extend(greenhouse_jobs)

    all_jobs = deduplicate(all_jobs)
    print(f"\nTotal unique jobs found: {len(all_jobs)}")
    return all_jobs