import sys
from agents.scraper import discover_and_scrape
from agents.evaluator import evaluate_all
from utils.database import init_db, insert_job, get_unscored_jobs, update_job_score, get_all_jobs

def run_search():
    from utils.database import is_duplicate
    print("\n=== RoleRadar: Searching for jobs ===\n")
    jobs = discover_and_scrape()
    saved = 0
    skipped = 0
    for job in jobs:
        if is_duplicate(job['title'], job['company']):
            skipped += 1
            continue
        insert_job(job)
        saved += 1
    print(f"\nSaved {saved} new jobs, skipped {skipped} duplicates.")

def run_score(limit=None):
    print("\n=== RoleRadar: Scoring jobs ===\n")
    jobs = get_unscored_jobs()
    if not jobs:
        print("No unscored jobs found.")
        return

    # Pre-filter by title before sending to OpenAI
    relevant_keywords = [
        'salesforce', 'apex', 'lwc', 'agentforce', 'flow',
        'architect', 'crm', 'platform', 'solution', 'technical'
    ]
    
    filtered = []
    skipped = []
    for job in jobs:
        title_lower = job['title'].lower()
        if any(kw in title_lower for kw in relevant_keywords):
            filtered.append(job)
        else:
            skipped.append(job)

    # Auto-skip irrelevant jobs without calling OpenAI
    for job in skipped:
        update_job_score(job['id'], 0, 'Skip')

    print(f"Pre-filter: {len(filtered)} relevant, {len(skipped)} auto-skipped\n")

    if limit:
        filtered = filtered[:limit]

    print(f"Scoring {len(filtered)} jobs with AI...\n")
    evaluated = evaluate_all(filtered)
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

def run_email():
    from agents.email_agent import run_email_agent
    print("\n=== RoleRadar: Building email digest ===\n")
    run_email_agent()
    
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
    elif '--email' in args:
        run_email()
    else:
        print("Usage:")
        print("  python run.py --search              # Find new jobs")
        print("  python run.py --score               # Score all unscored jobs")
        print("  python run.py --score --limit 10    # Score first 10 only")
        print("  python run.py --results             # View results")
        print("  python run.py --email               # Build email digest")