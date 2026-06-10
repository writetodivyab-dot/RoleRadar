import os
import json
from datetime import date
from utils.database import get_connection

def get_new_jobs():
    """Get jobs found today that are unscored."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, title, company, location, url, source, date_found
        FROM jobs
        WHERE date_found = ? AND score IS NULL
        ORDER BY source, company
    ''', (str(date.today()),))
    jobs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jobs

def build_email_body(jobs: list[dict]) -> str:
    if not jobs:
        return None

    linkedin = [j for j in jobs if j['source'] == 'linkedin']
    greenhouse = [j for j in jobs if j['source'] == 'greenhouse']
    other = [j for j in jobs if j['source'] not in ['linkedin', 'greenhouse']]

    def job_block(job):
        return f"""
🔹 {job['title']}
   Company:  {job['company']}
   Location: {job['location'] or 'Not specified'}
   Posted:   {job['date_found']}
   Link:     {job['url']}
"""

    sections = []

    if linkedin:
        sections.append(f"── LinkedIn ({len(linkedin)} jobs) ──\n")
        sections.extend([job_block(j) for j in linkedin])

    if greenhouse:
        sections.append(f"\n── Greenhouse ({len(greenhouse)} jobs) ──\n")
        sections.extend([job_block(j) for j in greenhouse])

    if other:
        sections.append(f"\n── Other ({len(other)} jobs) ──\n")
        sections.extend([job_block(j) for j in other])

    body = f"""RoleRadar found {len(jobs)} new Salesforce jobs today ({date.today()}).

Review below and decide which ones to score locally:
  python run.py --score --limit 20

{''.join(sections)}
──────────────────────────────
RoleRadar · Running automatically 3x daily
"""
    return body

def send_email_via_mcp(subject: str, body: str):
    """
    Write job digest to a local file for Gmail MCP to pick up.
    The GitHub Actions step reads this and sends via Gmail MCP.
    """
    digest = {
        "subject": subject,
        "body": body
    }
    path = os.path.join(os.path.dirname(__file__), '..', 'data', 'email_digest.json')
    with open(path, 'w') as f:
        json.dump(digest, f, indent=2)
    print(f"Email digest written to data/email_digest.json")

def run_email_agent():
    jobs = get_new_jobs()
    if not jobs:
        print("No new jobs today — skipping email.")
        return

    body = build_email_body(jobs)
    subject = f"RoleRadar: {len(jobs)} new Salesforce jobs — {date.today()}"
    send_email_via_mcp(subject, body)
    print(f"Digest ready: {len(jobs)} jobs, subject: {subject}")