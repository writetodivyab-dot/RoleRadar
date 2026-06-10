import os
import yaml
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def load_criteria():
    path = os.path.join(os.path.dirname(__file__), '..', 'config', 'scoring_criteria.yaml')
    with open(path) as f:
        return yaml.safe_load(f)

def load_profile():
    path = os.path.join(os.path.dirname(__file__), '..', 'config', 'search_profile.yaml')
    with open(path) as f:
        return yaml.safe_load(f)

def evaluate_job(job: dict) -> dict:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    criteria = load_criteria()
    profile = load_profile()

    prompt = f"""
You are a job fit evaluator. Score this job for the candidate based on the criteria below.

CANDIDATE PROFILE:
- Target roles: {profile['target_roles']}
- Location preference: {profile['location']}
- Minimum salary: {profile['salary']['minimum']}
- Keywords: {profile['keywords']}
- Visa sponsorship required: {profile['visa_sponsorship_required']}

SCORING WEIGHTS:
{yaml.dump(criteria['weights'])}

DEALBREAKERS (score 0 immediately if any found):
{criteria['dealbreakers']}

STRONG POSITIVE SIGNALS:
{criteria['strong_signals']}

MINIMUM SCORE TO RECOMMEND: {criteria['minimum_score']}

JOB TO EVALUATE:
Title: {job['title']}
Company: {job['company']}
Location: {job['location']}
Description: {job['description']}
URL: {job['url']}

Respond ONLY in this exact format:
SCORE: <number 0-100>
RECOMMENDATION: <Apply|Maybe|Skip>
REASON: <one sentence>
SPONSORSHIP_FLAG: <Yes|No|Unknown>
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    text = response.choices[0].message.content.strip()

    result = {
        'score': 0,
        'recommendation': 'Skip',
        'reason': '',
        'sponsorship_flag': 'Unknown'
    }

    for line in text.split('\n'):
        if line.startswith('SCORE:'):
            try:
                result['score'] = int(line.split(':')[1].strip())
            except:
                pass
        elif line.startswith('RECOMMENDATION:'):
            result['recommendation'] = line.split(':')[1].strip()
        elif line.startswith('REASON:'):
            result['reason'] = line.split(':', 1)[1].strip()
        elif line.startswith('SPONSORSHIP_FLAG:'):
            result['sponsorship_flag'] = line.split(':')[1].strip()

    return result

def evaluate_all(jobs: list[dict]) -> list[dict]:
    evaluated = []
    for i, job in enumerate(jobs):
        print(f"  Evaluating {i+1}/{len(jobs)}: {job['title']} at {job['company']}")
        result = evaluate_job(job)
        job.update(result)
        evaluated.append(job)
    return evaluated