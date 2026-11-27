from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from datetime import datetime, timezone
import json, re, sqlite3

ROOT = Path(__file__).parent
DB = ROOT / "jobradar.db"

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
        url TEXT DEFAULT '', description TEXT DEFAULT '', status TEXT DEFAULT 'New',
        created_at TEXT NOT NULL, UNIQUE(url))""")
    return con

def score(job):
    text = (job["title"] + " " + job["description"]).lower()
    hits = [s for s in PROFILE["skills"] if s in text]
    points = min(65, len(hits) * 13)
    if any(r.lower() in text for r in PROFILE["roles"]): points += 20
    if any(s in text for s in PROFILE["junior"]): points += 15
    if any(s in text for s in PROFILE["senior"]): points -= 35
    return max(0, min(100, points)), hits

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT / "static"), **kwargs)

    def send_json(self, data, status=200):
        raw = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
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
        if path == "/api/profile":
            return self.send_json(PROFILE)
        return super().do_GET()

    def do_POST(self):
        if urlparse(self.path).path != "/api/jobs":
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
                 data.get("source", "Manual"), data.get("url", ""),
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
    ThreadingHTTPServer(("127.0.0.1", 8000), Handler).serve_forever()
