from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils.database import init_db, get_all_jobs, update_job_status

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>RoleRadar</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg: #0D1117;
    --bg-card: #161B22;
    --bg-hover: #1C2128;
    --border: #30363D;
    --blue: #2F80ED;
    --blue-dim: #1a4a8a;
    --green: #3FB950;
    --yellow: #D29922;
    --red: #F85149;
    --text: #E6EDF3;
    --text-muted: #8B949E;
    --mono: 'JetBrains Mono', monospace;
    --sans: 'Inter', sans-serif;
  }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: var(--sans);
    min-height: 100vh;
  }

  header {
    border-bottom: 1px solid var(--border);
    padding: 20px 32px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: sticky;
    top: 0;
    background: var(--bg);
    z-index: 100;
  }

  .logo {
    font-family: var(--mono);
    font-size: 18px;
    font-weight: 600;
    color: var(--blue);
    letter-spacing: -0.5px;
  }

  .logo span { color: var(--text-muted); }

  .stats {
    display: flex;
    gap: 24px;
    font-family: var(--mono);
    font-size: 13px;
  }

  .stat { display: flex; align-items: center; gap: 8px; }
  .stat-dot { width: 8px; height: 8px; border-radius: 50%; }
  .dot-green { background: var(--green); }
  .dot-yellow { background: var(--yellow); }
  .dot-red { background: var(--red); }
  .stat-count { color: var(--text); font-weight: 600; }
  .stat-label { color: var(--text-muted); }

  .toolbar {
    padding: 20px 32px;
    display: flex;
    gap: 12px;
    align-items: center;
    flex-wrap: wrap;
  }

  .search-wrap {
    position: relative;
    flex: 1;
    min-width: 240px;
  }

  .search-icon {
    position: absolute;
    left: 12px;
    top: 50%;
    transform: translateY(-50%);
    color: var(--text-muted);
    font-size: 14px;
  }

  input[type="text"] {
    width: 100%;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 8px;
    color: var(--text);
    font-family: var(--sans);
    font-size: 14px;
    padding: 10px 12px 10px 36px;
    outline: none;
    transition: border-color 0.15s;
  }

  input[type="text"]:focus { border-color: var(--blue); }
  input[type="text"]::placeholder { color: var(--text-muted); }

  .filter-group { display: flex; gap: 6px; }

  .filter-btn {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 6px;
    color: var(--text-muted);
    cursor: pointer;
    font-family: var(--sans);
    font-size: 13px;
    font-weight: 500;
    padding: 8px 14px;
    transition: all 0.15s;
  }

  .filter-btn:hover { border-color: var(--blue); color: var(--text); }
  .filter-btn.active { background: var(--blue-dim); border-color: var(--blue); color: var(--text); }

  .source-group { display: flex; gap: 6px; }

  main { padding: 0 32px 48px; }

  .section-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 16px;
    margin-top: 28px;
  }

  .section-label {
    font-family: var(--mono);
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
  }

  .label-apply { color: var(--green); }
  .label-maybe { color: var(--yellow); }
  .label-skip { color: var(--text-muted); }
  .label-new { color: var(--blue); }

  .section-count {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    color: var(--text-muted);
    font-family: var(--mono);
    font-size: 11px;
    padding: 2px 8px;
  }

  .divider {
    flex: 1;
    height: 1px;
    background: var(--border);
  }

  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
    gap: 12px;
  }

  .card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 18px;
    transition: border-color 0.15s, background 0.15s;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .card:hover { border-color: var(--blue); background: var(--bg-hover); }

  .card-top {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 12px;
  }

  .card-title {
    font-size: 14px;
    font-weight: 600;
    color: var(--text);
    line-height: 1.4;
  }

  .score-badge {
    font-family: var(--mono);
    font-size: 13px;
    font-weight: 600;
    min-width: 36px;
    text-align: center;
    padding: 3px 8px;
    border-radius: 6px;
    flex-shrink: 0;
  }

  .score-apply { background: rgba(63,185,80,0.15); color: var(--green); }
  .score-maybe { background: rgba(210,153,34,0.15); color: var(--yellow); }
  .score-skip { background: rgba(139,148,158,0.1); color: var(--text-muted); }
  .score-new { background: rgba(47,128,237,0.15); color: var(--blue); }

  .card-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    font-size: 12px;
    color: var(--text-muted);
  }

  .meta-tag {
    background: rgba(48,54,61,0.6);
    border-radius: 4px;
    padding: 2px 7px;
    display: flex;
    align-items: center;
    gap: 4px;
  }

  .source-tag {
    border-radius: 4px;
    padding: 2px 7px;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .source-linkedin { background: rgba(10,102,194,0.2); color: #5aa3e0; }
  .source-greenhouse { background: rgba(63,185,80,0.15); color: #5db87a; }
  .source-lever { background: rgba(255,100,50,0.15); color: #e07a5a; }

  .card-reason {
    font-size: 12px;
    color: var(--text-muted);
    line-height: 1.5;
    font-style: italic;
  }

  .card-actions {
    display: flex;
    gap: 8px;
    margin-top: auto;
  }

  .btn-link {
    background: var(--blue);
    border: none;
    border-radius: 6px;
    color: white;
    cursor: pointer;
    font-family: var(--sans);
    font-size: 12px;
    font-weight: 500;
    padding: 7px 14px;
    text-decoration: none;
    display: inline-flex;
    align-items: center;
    gap: 5px;
    transition: opacity 0.15s;
  }

  .btn-link:hover { opacity: 0.85; }

  .btn-status {
    background: transparent;
    border: 1px solid var(--border);
    border-radius: 6px;
    color: var(--text-muted);
    cursor: pointer;
    font-family: var(--sans);
    font-size: 12px;
    padding: 7px 12px;
    transition: all 0.15s;
  }

  .btn-status:hover { border-color: var(--text-muted); color: var(--text); }
  .btn-status.applied { border-color: var(--green); color: var(--green); }
  .btn-status.interviewing { border-color: var(--yellow); color: var(--yellow); }
  .btn-status.rejected { border-color: var(--red); color: var(--red); }

  .empty {
    color: var(--text-muted);
    font-size: 13px;
    padding: 16px 0;
  }

  @media (max-width: 600px) {
    header { padding: 16px; }
    .toolbar { padding: 12px 16px; }
    main { padding: 0 16px 48px; }
    .stats { gap: 14px; }
  }
</style>
</head>
<body>

<header>
  <div class="logo">Role<span>Radar</span></div>
  <div class="stats" id="stats"></div>
</header>

<div class="toolbar">
  <div class="search-wrap">
    <span class="search-icon">⌕</span>
    <input type="text" id="search" placeholder="Search by title, company, or location...">
  </div>
  <div class="filter-group">
    <button class="filter-btn active" data-filter="all">All</button>
    <button class="filter-btn" data-filter="Apply">Apply</button>
    <button class="filter-btn" data-filter="Maybe">Maybe</button>
    <button class="filter-btn" data-filter="new">Unscored</button>
  </div>
  <div class="source-group">
    <button class="filter-btn active" data-source="all">All Sources</button>
    <button class="filter-btn" data-source="linkedin">LinkedIn</button>
    <button class="filter-btn" data-source="greenhouse">Greenhouse</button>
  </div>
</div>

<main id="main"></main>

<script>
let allJobs = [];
let activeFilter = 'all';
let activeSource = 'all';
let searchQuery = '';

async function loadJobs() {
  const res = await fetch('/api/jobs');
  allJobs = await res.json();
  render();
}

function render() {
  const q = searchQuery.toLowerCase();
  let jobs = allJobs.filter(j => {
    const matchSearch = !q || 
      j.title.toLowerCase().includes(q) || 
      j.company.toLowerCase().includes(q) || 
      (j.location || '').toLowerCase().includes(q);
    const matchFilter = activeFilter === 'all' || 
      (activeFilter === 'new' ? !j.recommendation : j.recommendation === activeFilter);
    const matchSource = activeSource === 'all' || j.source === activeSource;
    return matchSearch && matchFilter && matchSource;
  });

  // Stats
  const apply = allJobs.filter(j => j.recommendation === 'Apply').length;
  const maybe = allJobs.filter(j => j.recommendation === 'Maybe').length;
  const unscored = allJobs.filter(j => !j.recommendation).length;
  document.getElementById('stats').innerHTML = `
    <div class="stat"><div class="stat-dot dot-green"></div><span class="stat-count">${apply}</span><span class="stat-label">apply</span></div>
    <div class="stat"><div class="stat-dot dot-yellow"></div><span class="stat-count">${maybe}</span><span class="stat-label">maybe</span></div>
    <div class="stat"><div class="stat-dot" style="background:var(--blue)"></div><span class="stat-count">${unscored}</span><span class="stat-label">unscored</span></div>
  `;

  const main = document.getElementById('main');

  if (activeFilter === 'all' || activeFilter === 'new') {
    const sections = activeFilter === 'new'
      ? [{ key: 'new', label: 'Unscored', cls: 'label-new' }]
      : [
          { key: 'Apply', label: 'Apply', cls: 'label-apply' },
          { key: 'Maybe', label: 'Maybe', cls: 'label-maybe' },
          { key: 'new', label: 'Unscored', cls: 'label-new' },
        ];

    main.innerHTML = sections.map(s => {
      const sJobs = jobs.filter(j => s.key === 'new' ? !j.recommendation : j.recommendation === s.key);
      return `
        <div class="section-header">
          <span class="section-label ${s.cls}">${s.label}</span>
          <span class="section-count">${sJobs.length}</span>
          <div class="divider"></div>
        </div>
        <div class="grid">${sJobs.length ? sJobs.map(cardHTML).join('') : '<p class="empty">None</p>'}</div>
      `;
    }).join('');
  } else {
    main.innerHTML = `
      <div class="section-header">
        <span class="section-label">${activeFilter === 'Apply' ? '<span class="label-apply">Apply</span>' : '<span class="label-maybe">Maybe</span>'}</span>
        <span class="section-count">${jobs.length}</span>
        <div class="divider"></div>
      </div>
      <div class="grid">${jobs.length ? jobs.map(cardHTML).join('') : '<p class="empty">None</p>'}</div>
    `;
  }
}

function cardHTML(j) {
  const rec = j.recommendation || 'new';
  const scoreClass = rec === 'Apply' ? 'score-apply' : rec === 'Maybe' ? 'score-maybe' : rec === 'Skip' ? 'score-skip' : 'score-new';
  const scoreLabel = j.score != null ? j.score : '—';
  const srcClass = j.source === 'linkedin' ? 'source-linkedin' : j.source === 'greenhouse' ? 'source-greenhouse' : 'source-lever';
  const statusClass = j.status === 'applied' ? 'applied' : j.status === 'interviewing' ? 'interviewing' : j.status === 'rejected' ? 'rejected' : '';
  const statusLabel = j.status === 'applied' ? '✓ Applied' : j.status === 'interviewing' ? '◈ Interviewing' : j.status === 'rejected' ? '✕ Rejected' : 'Mark Applied';

  return `
    <div class="card" id="card-${j.id}">
      <div class="card-top">
        <div class="card-title">${j.title}</div>
        <div class="score-badge ${scoreClass}">${scoreLabel}</div>
      </div>
      <div class="card-meta">
        <span class="meta-tag">🏢 ${j.company}</span>
        ${j.location ? `<span class="meta-tag">📍 ${j.location}</span>` : ''}
        <span class="source-tag ${srcClass}">${j.source}</span>
        <span class="meta-tag">📅 ${j.date_found}</span>
      </div>
      ${j.reason ? `<div class="card-reason">${j.reason}</div>` : ''}
      <div class="card-actions">
        <a class="btn-link" href="${j.url}" target="_blank">View Job ↗</a>
        <button class="btn-status ${statusClass}" onclick="cycleStatus(${j.id}, '${j.status || 'new'}')">${statusLabel}</button>
      </div>
    </div>
  `;
}

async function cycleStatus(id, current) {
  const next = current === 'new' ? 'applied' : current === 'applied' ? 'interviewing' : current === 'interviewing' ? 'rejected' : 'new';
  await fetch('/api/status', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id, status: next })
  });
  const job = allJobs.find(j => j.id === id);
  if (job) job.status = next;
  render();
}

document.getElementById('search').addEventListener('input', e => {
  searchQuery = e.target.value;
  render();
});

document.querySelectorAll('.filter-btn[data-filter]').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.filter-btn[data-filter]').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    activeFilter = btn.dataset.filter;
    render();
  });
});

document.querySelectorAll('.filter-btn[data-source]').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.filter-btn[data-source]').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    activeSource = btn.dataset.source;
    render();
  });
});

loadJobs();
</script>
</body>
</html>
"""

class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML.encode())
        elif self.path == '/api/jobs':
            jobs = get_all_jobs()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(jobs).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == '/api/status':
            length = int(self.headers['Content-Length'])
            body = json.loads(self.rfile.read(length))
            update_job_status(body['id'], body['status'])
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"ok": true}')

if __name__ == '__main__':
    init_db()
    port = 8000
    print(f"\n RoleRadar Studio → http://localhost:{port}\n")
    HTTPServer(('', port), Handler).serve_forever()
