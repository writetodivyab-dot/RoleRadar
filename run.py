import sys
from agents.scraper import discover_and_scrape
from agents.evaluator import evaluate_all
from utils.database import init_db, insert_job, get_unscored_jobs, update_job_score, get_all_jobs

def run_search():
    print("\n=== RoleRadar: Searching for jobs ===\n")
    jobs = discover_and_scrape()
    for job in jobs:
        insert_job(job)
    print(f"\nSaved {len(jobs)} jobs to database.")

def run_score(limit=None):
    print("\n=== RoleRadar: Scoring jobs ===\n")
    jobs = get_unscored_jobs()
    if not jobs:
        print("No unscored jobs found.")
        return
    if limit:
        jobs = jobs[:limit]
    print(f"Scoring {len(jobs)} jobs...\n")
    evaluated = evaluate_all(jobs)
    for job in evaluated:
        update_job_score(job['id'], job['score'], job['recommendation'])
    print(f"\nDone. Scored {len(evaluated)} jobs.")

def print_results():
    jobs = get_all_jobs()
    if not jobs:
        print("No jobs in database yet.")
        return

    apply = [j for j in jobs if j['recommendation'] == 'Apply']
    maybe = [j for j in jobs if j['recommendation'] == 'Maybe']
    skip = [j for j in jobs if j['recommendation'] == 'Skip']

    print(f"\n=== RoleRadar Results ===")
    print(f"Apply: {len(apply)} | Maybe: {len(maybe)} | Skip: {len(skip)}\n")

    print("--- APPLY ---")
    for job in apply:
        print(f"  [{job['score']}] {job['title']} at {job['company']} | {job['location']}")
        print(f"       {job['url']}")

    print("\n--- MAYBE ---")
    for job in maybe:
        print(f"  [{job['score']}] {job['title']} at {job['company']} | {job['location']}")
        print(f"       {job['url']}")

if __name__ == "__main__":
    init_db()

    args = sys.argv[1:]

    if '--search' in args:
        run_search()
    elif '--score' in args:
        limit = None
        if '--limit' in args:
            idx = args.index('--limit')
            limit = int(args[idx + 1])
        run_score(limit)
    elif '--results' in args:
        print_results()
    else:
        print("Usage:")
        print("  python run.py --search              # Find new jobs")
        print("  python run.py --score               # Score all unscored jobs")
        print("  python run.py --score --limit 10    # Score first 10 only")
        print("  python run.py --results             # View results")