from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, urlencode
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import json, re, sqlite3, html, os, xml.etree.ElementTree as ET

ROOT = Path(__file__).parent
DB = ROOT / "jobradar.db"
HIMALAYAS_API = "https://himalayas.app/jobs/api/search"
WORK_WITH_INDIES_FEED = "https://www.workwithindies.com/careers/rss.xml"
SEARCH_TERMS = ["Unity Developer", "Gameplay Programmer", "Game Developer"]
PROFILE = {
    "roles": ["Unity Developer", "Gameplay Programmer", "Game Developer",
              "Game Programmer Intern", "Technical Artist"],
    "skills": ["unity", "c#", "c++", "gameplay", "rigidbody", "physics",
               "object pooling", "coroutines", "finite state machine",
               "charactercontroller", "event systems", "game development"],
    "junior": ["intern", "internship", "junior", "entry level", "graduate"],
    "senior": ["senior", "lead", "principal", "staff", "10+ years", "8+ years"]
}

def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    con.execute("""CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL,
        company TEXT DEFAULT '', location TEXT DEFAULT '', source TEXT DEFAULT 'Manual',
        url TEXT UNIQUE, description TEXT DEFAULT '', status TEXT DEFAULT 'New',
        created_at TEXT NOT NULL)""")
    # Empty URLs should not collide with each other under SQLite UNIQUE constraints.
    con.execute("UPDATE jobs SET url=NULL WHERE url=''")
    return con

def clean_text(value):
    value = re.sub(r"<[^>]+>", " ", value or "")
    return html.unescape(re.sub(r"\s+", " ", value)).strip()

def score(job):
    text = (job["title"] + " " + job["description"]).lower()
    hits = [s for s in PROFILE["skills"] if s in text]
    points = min(65, len(hits) * 13)
    if any(r.lower() in text for r in PROFILE["roles"]): points += 20
    if any(s in text for s in PROFILE["junior"]): points += 15
    if any(s in text for s in PROFILE["senior"]): points -= 35
    return max(0, min(100, points)), hits

def discover_himalayas():
    con = db()
    added, duplicates, errors = 0, 0, []
    seen = set()
    for term in SEARCH_TERMS:
        params = urlencode({"q": term, "country": "IN", "sort": "recent", "page": 1})
        req = Request(HIMALAYAS_API + "?" + params,
                      headers={"User-Agent": "JobRadar/0.2 (personal job discovery dashboard)",
                               "Accept": "application/json"})
        try:
            with urlopen(req, timeout=20) as response:
                payload = json.loads(response.read().decode("utf-8"))
            for item in payload.get("jobs", []):
                url = item.get("applicationLink") or ""
                if not url or url in seen:
                    continue
                seen.add(url)
                title = clean_text(item.get("title", ""))
                description = clean_text(item.get("description") or item.get("excerpt") or "")
                if not title:
                    continue
                restrictions = item.get("locationRestrictions") or []
                location = ", ".join(restrictions) if restrictions else "Worldwide / remote"
                company = clean_text(item.get("companyName", ""))
                cur = con.execute("""INSERT OR IGNORE INTO jobs
                    (title, company, location, source, url, description, status, created_at)
                    VALUES (?, ?, ?, 'Himalayas', ?, ?, 'New', ?)""",
                    (title, company, location, url, description,
                     datetime.now(timezone.utc).isoformat()))
                if cur.rowcount:
                    added += 1
                else:
                    duplicates += 1
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
            errors.append(term + ": " + str(exc))
    con.commit()
    con.close()
    return {"source": "Himalayas", "added": added, "duplicates": duplicates,
            "errors": errors, "searched_terms": SEARCH_TERMS}

def discover_work_with_indies():
    con = db()
    added, duplicates = 0, 0
    req = Request(WORK_WITH_INDIES_FEED, headers={
        'User-Agent': 'JobRadar/0.3 (personal job discovery dashboard)',
        'Accept': 'application/rss+xml, application/xml, text/xml'})
    with urlopen(req, timeout=20) as response:
        root = ET.fromstring(response.read())
    for item in root.findall('.//item'):
        title = clean_text(item.findtext('title', default=''))
        url = (item.findtext('link', default='') or '').strip()
        description = clean_text(item.findtext('description', default=''))
        if not title or not url:
            continue
        match = re.match(r'(.+?)\s+is hiring\b', title, re.I)
        company = clean_text(match.group(1)) if match else 'Work With Indies listing'
        cur = con.execute('''INSERT OR IGNORE INTO jobs
            (title, company, location, source, url, description, status, created_at)
            VALUES (?, ?, '', 'Work With Indies', ?, ?, 'New', ?)''',
            (title, company, url, description, datetime.now(timezone.utc).isoformat()))
        if cur.rowcount: added += 1
        else: duplicates += 1
    con.commit()
    con.close()
    return {'source': 'Work With Indies', 'added': added, 'duplicates': duplicates}

def discover_all():
    results, errors = [], []
    for discoverer in (discover_himalayas, discover_work_with_indies):
        try: results.append(discoverer())
        except Exception as exc: errors.append(discoverer.__name__ + ': ' + str(exc))
    return {'added': sum(x.get('added', 0) for x in results),
            'duplicates': sum(x.get('duplicates', 0) for x in results),
            'sources': results, 'errors': errors}

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT / "static"), **kwargs)

    def send_json(self, data, status=200):
        raw = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/jobs":
            con = db()
            rows = [dict(r) for r in con.execute("SELECT * FROM jobs ORDER BY id DESC")]
            con.close()
            for row in rows:
                row["match"], row["matched_skills"] = score(row)
            return self.send_json(rows)
        if path == "/api/stats":
            con = db()
            rows = con.execute("SELECT source, COUNT(*) AS count FROM jobs GROUP BY source ORDER BY count DESC, source ASC").fetchall()
            total = con.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
            con.close()
            counts = {row["source"] or "Unknown": row["count"] for row in rows}
            for source in ("Himalayas", "Work With Indies", "LinkedIn", "Indeed", "Naukri", "Internshala", "Hitmarker", "Manual"):
                counts.setdefault(source, 0)
            return self.send_json({"total": total, "sources": counts})
        if path == "/api/profile":
            return self.send_json(PROFILE)
        return super().do_GET()

    def do_POST(self):
        path = urlparse(self.path).path
        if path == "/api/discover":
            try:
                return self.send_json(discover_all())
            except Exception as exc:
                return self.send_json({"error": str(exc)}, 502)
        if path != "/api/jobs":
            return self.send_json({"error": "Not found"}, 404)
        try:
            data = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
            if not data.get("title"):
                return self.send_json({"error": "Job title is required"}, 400)
            con = db()
            con.execute("""INSERT OR IGNORE INTO jobs
                (title, company, location, source, url, description, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, 'New', ?)""",
                (data["title"], data.get("company", ""), data.get("location", ""),
                 data.get("source", "Manual"), data.get("url") or None,
                 data.get("description", ""), datetime.now(timezone.utc).isoformat()))
            con.commit()
            con.close()
            return self.send_json({"ok": True})
        except Exception as exc:
            return self.send_json({"error": str(exc)}, 400)

    def do_PATCH(self):
        match = re.fullmatch(r"/api/jobs/(\d+)", urlparse(self.path).path)
        if not match:
            return self.send_json({"error": "Not found"}, 404)
        data = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
        con = db()
        con.execute("UPDATE jobs SET status=? WHERE id=?",
                    (data.get("status", "New"), int(match.group(1))))
        con.commit()
        con.close()
        return self.send_json({"ok": True})

if __name__ == "__main__":
    db().close()
    print("JobRadar running at http://127.0.0.1:8000")
    port = int(os.environ.get("PORT", "8000"))
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
