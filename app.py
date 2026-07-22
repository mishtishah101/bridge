import anthropic
import os
import psycopg2
import secrets
import bcrypt
import urllib.parse
import json
import io
from http.server import HTTPServer, BaseHTTPRequestHandler
from pypdf import PdfReader

SESSIONS = {}

def get_db_connection():
    db_url = os.environ.get("DATABASE_URL")
    conn = psycopg2.connect(db_url)
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS mentors (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            name TEXT,
            role TEXT,
            experience TEXT,
            advise TEXT,
            career_path TEXT,
            style TEXT,
            availability TEXT
        )
    """)
    conn.commit()
    conn.close()

def migrate_mentors_table():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        ALTER TABLE mentors ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id)
    """)
    conn.commit()
    conn.close()

def init_users_table():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def get_mentors():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT name, role, experience, advise, career_path, style, availability FROM mentors")
    rows = c.fetchall()
    conn.close()
    if not rows:
        return None
    mentor_text = ""
    for i, row in enumerate(rows, 1):
        mentor_text += f"""
MENTOR {i} - {row[0]}
Industry/Role: {row[1]}
Years of experience: {row[2]}
Can advise on: {row[3]}
Career path: {row[4]}
Mentorship style: {row[5]}
Availability: {row[6]}
"""
    return mentor_text

def save_mentor(data):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO mentors (user_id, name, role, experience, advise, career_path, style, availability)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        data.get("user_id"),
        data.get("name", ""),
        data.get("role", ""),
        data.get("experience", ""),
        data.get("advise", ""),
        data.get("career_path", ""),
        data.get("style", ""),
        data.get("availability", "")
    ))
    conn.commit()
    conn.close()

def create_user(email, password, role):
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO users (email, password_hash, role)
        VALUES (%s, %s, %s)
    """, (email, password_hash, role))
    conn.commit()
    conn.close()

def check_user(email, password):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, password_hash, role FROM users WHERE email = %s", (email,))
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    user_id, password_hash, role = row
    if bcrypt.checkpw(password.encode(), password_hash.encode()):
        return {"id": user_id, "email": email, "role": role}
    return None

def extract_pdf_text(pdf_bytes):
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text.strip()
    except Exception:
        return ""

def get_match(student, mentors):
    client = anthropic.Anthropic()
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""You are a mentor matching assistant. Given a student profile and mentor profiles, return the top 3 matches as JSON only. No other text.

STUDENT PROFILE:
{student}

MENTOR PROFILES:
{mentors}

Return exactly this JSON format:
{{
  "matches": [
    {{
      "name": "Mentor Name",
      "role": "Their Role",
      "score": 9,
      "summary": "One sentence explaining why they are a strong match.",
      "pros": ["Pro 1", "Pro 2", "Pro 3"]
    }}
  ]
}}

Return only the top 3. Return only valid JSON, nothing else."""
            }
        ]
    )
    return message.content[0].text

def build_results_page(matches):
    cards = ""
    for i, m in enumerate(matches):
        score = m.get("score", 0)
        pros_html = "".join(f"<li>{p}</li>" for p in m.get("pros", []))
        rank_label = ["#1 Best Match", "#2 Strong Match", "#3 Good Match"][i] if i < 3 else f"#{i+1}"
        cards += f"""
        <div class="card">
            <div class="card-header">
                <div>
                    <div class="rank">{rank_label}</div>
                    <div class="mentor-name">{m.get('name', '')}</div>
                    <div class="mentor-role">{m.get('role', '')}</div>
                </div>
                <div class="score">{score}<span>/10</span></div>
            </div>
            <p class="summary">{m.get('summary', '')}</p>
            <ul class="pros">{pros_html}</ul>
        </div>
        """
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Bridge - Your Matches</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f7fa; color: #1a1a2e; min-height: 100vh; }}
        nav {{ background: #0f172a; padding: 16px 40px; display: flex; align-items: center; justify-content: space-between; }}
        nav h1 {{ color: white; font-size: 20px; font-weight: 600; }}
        nav h1 span {{ color: #38bdf8; }}
        nav div {{ display: flex; gap: 24px; }}
        nav a {{ color: #94a3b8; text-decoration: none; font-size: 14px; font-weight: 500; }}
        .hero {{ background: #0f172a; padding: 50px 40px 70px; text-align: center; }}
        .hero h2 {{ color: white; font-size: 32px; font-weight: 700; margin-bottom: 10px; }}
        .hero p {{ color: #94a3b8; font-size: 15px; }}
        .results {{ max-width: 720px; margin: -40px auto 60px; display: flex; flex-direction: column; gap: 20px; }}
        .card {{ background: white; border-radius: 12px; box-shadow: 0 4px 24px rgba(0,0,0,0.08); padding: 28px 32px; border-top: 4px solid #38bdf8; }}
        .card-header {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 14px; }}
        .rank {{ font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; color: #38bdf8; margin-bottom: 6px; }}
        .mentor-name {{ font-size: 20px; font-weight: 700; color: #0f172a; }}
        .mentor-role {{ font-size: 13px; color: #64748b; margin-top: 2px; }}
        .score {{ font-size: 36px; font-weight: 800; color: #0f172a; line-height: 1; }}
        .score span {{ font-size: 14px; color: #94a3b8; font-weight: 400; }}
        .summary {{ font-size: 14px; color: #475569; line-height: 1.6; margin-bottom: 14px; }}
        .pros {{ list-style: none; display: flex; flex-direction: column; gap: 6px; }}
        .pros li {{ font-size: 13px; color: #334155; padding-left: 18px; position: relative; }}
        .pros li::before {{ content: "✓"; position: absolute; left: 0; color: #38bdf8; font-weight: 700; }}
        .back {{ text-align: center; margin-bottom: 40px; }}
        .back a {{ background: #0f172a; color: white; padding: 12px 28px; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 14px; }}
    </style>
</head>
<body>
    <nav>
        <h1>Bridge<span>.</span></h1>
        <div>
            <a href="/">Home</a>
            <a href="/match">Find a Mentor</a>
            <a href="/signup">Become a Mentor</a>
        </div>
    </nav>
    <div class="hero">
        <h2>Your Mentor Matches</h2>
        <p>Here are your top matches based on your profile and goals.</p>
    </div>
    <div class="results">{cards}</div>
    <div class="back"><a href="/match">Search Again</a></div>
</body>
</html>"""

def parse_multipart(data, content_type):
    boundary = None
    for part in content_type.split(";"):
        part = part.strip()
        if part.startswith("boundary="):
            boundary = part[9:].strip()
            break
    if not boundary:
        return {}, None
    boundary_bytes = ("--" + boundary).encode()
    parts = data.split(boundary_bytes)
    fields = {}
    pdf_bytes = None
    for part in parts[1:]:
        if part in (b"--\r\n", b"--"):
            continue
        if b"\r\n\r\n" not in part:
            continue
        header_section, _, body = part.partition(b"\r\n\r\n")
        body = body.rstrip(b"\r\n")
        headers = header_section.decode(errors="ignore")
        name = None
        for line in headers.split("\r\n"):
            if "Content-Disposition" in line:
                for item in line.split(";"):
                    item = item.strip()
                    if item.startswith('name="'):
                        name = item[6:-1]
        if name == "resume":
            pdf_bytes = body if body else None
        elif name:
            fields[name] = body.decode(errors="ignore")
    return fields, pdf_bytes

class Handler(BaseHTTPRequestHandler):
    def get_current_user(self):
        cookie_header = self.headers.get("Cookie", "")
        for part in cookie_header.split(";"):
            part = part.strip()
            if part.startswith("session_token="):
                token = part[len("session_token="):]
                return SESSIONS.get(token)
        return None

    def do_GET(self):
        if self.path == "/signup":
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(SIGNUP_HTML.encode())
        elif self.path == "/signup-account":
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(ACCOUNT_SIGNUP_HTML.encode())
        elif self.path == "/login":
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(LOGIN_HTML.encode())
        elif self.path == "/match":
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(MATCH_HTML.encode())
        else:
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(LANDING_HTML.encode())

    def do_POST(self):
        length = int(self.headers["Content-Length"])
        raw_data = self.rfile.read(length)
        content_type = self.headers.get("Content-Type", "")

        if self.path == "/signup":
            flat = urllib.parse.parse_qs(raw_data.decode())
            flat = {k: v[0] for k, v in flat.items()}
            user = self.get_current_user()
            if not user:
                self.send_response(302)
                self.send_header("Location", "/login")
                self.end_headers()
                return
            flat["user_id"] = user["id"]
            save_mentor(flat)
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(THANKS_HTML.encode())
            return

        if self.path == "/signup-account":
            flat = urllib.parse.parse_qs(raw_data.decode())
            flat = {k: v[0] for k, v in flat.items()}
            email = flat.get("email", "").strip().lower()
            password = flat.get("password", "")
            role = flat.get("role", "student")
            try:
                create_user(email, password, role)
            except Exception:
                self.send_response(200)
                self.send_header("Content-type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(b"That email is already registered. Try logging in instead.")
                return
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"Account created! You can now log in.")
            return

        if self.path == "/login":
            flat = urllib.parse.parse_qs(raw_data.decode())
            flat = {k: v[0] for k, v in flat.items()}
            email = flat.get("email", "").strip().lower()
            password = flat.get("password", "")
            user = check_user(email, password)
            if not user:
                self.send_response(200)
                self.send_header("Content-type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(b"Invalid email or password.")
                return
            token = secrets.token_hex(16)
            SESSIONS[token] = user
            self.send_response(302)
            self.send_header("Set-Cookie", f"session_token={token}; Path=/; HttpOnly")
            self.send_header("Location", "/")
            self.end_headers()
            return

        if "multipart/form-data" in content_type:
            flat, pdf_bytes = parse_multipart(raw_data, content_type)
        else:
            flat = {k: v[0] for k, v in urllib.parse.parse_qs(raw_data.decode()).items()}
            pdf_bytes = None

        student_text = flat.get("student", "").strip()
        resume_text = ""
        if pdf_bytes:
            resume_text = extract_pdf_text(pdf_bytes)

        combined = student_text
        if resume_text:
            combined += "\n\nRESUME CONTENT:\n" + resume_text

        if not combined.strip():
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"Please enter your profile or upload a resume.")
            return

        mentors = get_mentors()
        if not mentors:
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"No mentors have signed up yet.")
            return

        raw = get_match(combined, mentors)
        try:
            raw = raw.strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
            data_json = json.loads(raw)
            matches = data_json.get("matches", [])[:3]
        except Exception:
            matches = []

        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(build_results_page(matches).encode())

    def log_message(self, format, *args):
        pass

LANDING_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Bridge - Navigate Your Career</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f7fa; color: #1a1a2e; min-height: 100vh; }
        nav { background: #0f172a; padding: 16px 40px; display: flex; align-items: center; justify-content: space-between; }
        nav h1 { color: white; font-size: 20px; font-weight: 600; }
        nav h1 span { color: #38bdf8; }
        nav div { display: flex; gap: 24px; }
        nav a { color: #94a3b8; text-decoration: none; font-size: 14px; font-weight: 500; }
        nav a:hover { color: white; }
        .hero { background: #0f172a; padding: 100px 40px; text-align: center; }
        .hero h2 { color: white; font-size: 48px; font-weight: 800; margin-bottom: 16px; line-height: 1.2; }
        .hero h2 span { color: #38bdf8; }
        .hero p { color: #94a3b8; font-size: 18px; max-width: 560px; margin: 0 auto 36px; line-height: 1.7; }
        .hero-buttons { display: flex; gap: 16px; justify-content: center; flex-wrap: wrap; }
        .btn-primary { background: #38bdf8; color: #0f172a; padding: 14px 28px; border-radius: 8px; text-decoration: none; font-weight: 700; font-size: 15px; }
        .btn-secondary { background: transparent; color: white; padding: 14px 28px; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 15px; border: 1.5px solid #475569; }
        .features { max-width: 900px; margin: 80px auto; padding: 0 40px; display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; }
        .feature { background: white; border-radius: 12px; padding: 28px; box-shadow: 0 4px 24px rgba(0,0,0,0.06); }
        .feature-icon { font-size: 28px; margin-bottom: 14px; }
        .feature h3 { font-size: 16px; font-weight: 700; color: #0f172a; margin-bottom: 8px; }
        .feature p { font-size: 14px; color: #64748b; line-height: 1.6; }
        .cta { background: #0f172a; padding: 80px 40px; text-align: center; }
        .cta h2 { color: white; font-size: 32px; font-weight: 700; margin-bottom: 12px; }
        .cta p { color: #94a3b8; font-size: 16px; margin-bottom: 28px; }
        .cta a { background: #38bdf8; color: #0f172a; padding: 14px 32px; border-radius: 8px; text-decoration: none; font-weight: 700; font-size: 15px; }
        footer { text-align: center; padding: 24px; color: #94a3b8; font-size: 13px; }
    </style>
</head>
<body>
    <nav>
        <h1>Bridge<span>.</span></h1>
        <div>
            <a href="/">Home</a>
            <a href="/match">Find a Mentor</a>
            <a href="/signup">Become a Mentor</a>
        </div>
    </nav>
    <div class="hero">
        <h2>Navigate Your Career<br><span>With Confidence.</span></h2>
        <p>The Bridge makes navigating career paths easier. Whether it be directly after college or a mid-career pivot, The Bridge serves as a spot to manage your career and learn new skills.</p>
        <div class="hero-buttons">
            <a href="/match" class="btn-primary">Find My Mentor Match</a>
            <a href="/signup" class="btn-secondary">Become a Mentor</a>
        </div>
    </div>
    <div class="features">
        <div class="feature">
            <div class="feature-icon">🎯</div>
            <h3>AI-Powered Matching</h3>
            <p>Our AI analyzes your goals, skills, and career stage to find the mentor who fits you best — not just the most available one.</p>
        </div>
        <div class="feature">
            <div class="feature-icon">🛤️</div>
            <h3>Any Stage, Any Path</h3>
            <p>Whether you're a student figuring out your first move or a professional making a pivot, Bridge meets you where you are.</p>
        </div>
        <div class="feature">
            <div class="feature-icon">🤝</div>
            <h3>Real Mentors</h3>
            <p>Every mentor on Bridge is a real professional who has signed up to help. No bots, no generic advice — just people who've been there.</p>
        </div>
    </div>
    <div class="cta">
        <h2>Ready to find your path?</h2>
        <p>Tell us where you are and where you want to go. We'll handle the matching.</p>
        <a href="/match">Get Started</a>
    </div>
    <footer>© 2026 Bridge. Built to help you find your way.</footer>
</body>
</html>"""

MATCH_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Bridge - Find a Mentor</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f7fa; color: #1a1a2e; min-height: 100vh; }
        nav { background: #0f172a; padding: 16px 40px; display: flex; align-items: center; justify-content: space-between; }
        nav h1 { color: white; font-size: 20px; font-weight: 600; }
        nav h1 span { color: #38bdf8; }
        nav div { display: flex; gap: 24px; }
        nav a { color: #94a3b8; text-decoration: none; font-size: 14px; font-weight: 500; }
        nav a:hover { color: white; }
        .hero { background: #0f172a; padding: 60px 40px 80px; text-align: center; }
        .hero h2 { color: white; font-size: 36px; font-weight: 700; margin-bottom: 12px; }
        .hero p { color: #94a3b8; font-size: 16px; max-width: 500px; margin: 0 auto; }
        .card { background: white; border-radius: 12px; box-shadow: 0 4px 24px rgba(0,0,0,0.08); max-width: 720px; margin: -40px auto 40px; padding: 40px; }
        label { display: block; font-size: 13px; font-weight: 600; color: #475569; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 8px; }
        .hint { font-size: 13px; color: #94a3b8; margin-bottom: 12px; font-weight: normal; text-transform: none; letter-spacing: 0; }
        textarea { width: 100%; height: 160px; padding: 14px; font-size: 14px; border: 1.5px solid #e2e8f0; border-radius: 8px; resize: vertical; font-family: inherit; color: #1a1a2e; line-height: 1.6; outline: none; }
        .divider { display: flex; align-items: center; gap: 12px; margin: 24px 0; color: #94a3b8; font-size: 13px; }
        .divider::before, .divider::after { content: ""; flex: 1; height: 1px; background: #e2e8f0; }
        .upload-box { border: 2px dashed #e2e8f0; border-radius: 8px; padding: 24px; text-align: center; cursor: pointer; transition: border-color 0.2s; }
        .upload-box:hover { border-color: #38bdf8; }
        .upload-box p { font-size: 14px; color: #64748b; margin-bottom: 8px; }
        .upload-box span { font-size: 12px; color: #94a3b8; }
        input[type="file"] { display: none; }
        .upload-label { cursor: pointer; display: block; }
        button { width: 100%; background: #0f172a; color: white; padding: 14px; border: none; border-radius: 8px; font-size: 15px; font-weight: 600; cursor: pointer; margin-top: 16px; }
    </style>
</head>
<body>
    <nav>
        <h1>Bridge<span>.</span></h1>
        <div>
            <a href="/">Home</a>
            <a href="/match">Find a Mentor</a>
            <a href="/signup">Become a Mentor</a>
        </div>
    </nav>
    <div class="hero">
        <h2>Find Your Mentor Match</h2>
        <p>Tell us about yourself and our AI will find your best mentor matches.</p>
    </div>
    <div class="card">
        <form method="POST" action="/match" enctype="multipart/form-data">
            <label>Your Profile <span class="hint">Include: Name, Major/Year, Career goals, Skills you have, Skills you want to develop, What you want in a mentor</span></label>
            <textarea name="student" placeholder="Name: &#10;Major/Year: &#10;Career goals: &#10;Skills I have: &#10;Skills I want to develop: &#10;What I want in a mentor:"></textarea>
            <div class="divider">or upload your resume</div>
            <label class="upload-label" for="resume-input">
                <div class="upload-box" id="upload-box">
                    <p>📄 Click to upload your resume</p>
                    <span>PDF files only</span>
                </div>
            </label>
            <input type="file" id="resume-input" name="resume" accept=".pdf" onchange="updateUploadBox(this)">
            <button type="submit">Find My Mentor Match &rarr;</button>
        </form>
    </div>
    <script>
        function updateUploadBox(input) {
            const box = document.getElementById('upload-box');
            if (input.files && input.files[0]) {
                box.innerHTML = '<p>✅ ' + input.files[0].name + '</p><span>Click to change</span>';
                box.style.borderColor = '#38bdf8';
            }
        }
    </script>
</body>
</html>"""

SIGNUP_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Bridge - Become a Mentor</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f7fa; color: #1a1a2e; min-height: 100vh; }
        nav { background: #0f172a; padding: 16px 40px; display: flex; align-items: center; justify-content: space-between; }
        nav h1 { color: white; font-size: 20px; font-weight: 600; }
        nav h1 span { color: #38bdf8; }
        nav div { display: flex; gap: 24px; }
        nav a { color: #94a3b8; text-decoration: none; font-size: 14px; font-weight: 500; }
        .hero { background: #0f172a; padding: 60px 40px 80px; text-align: center; }
        .hero h2 { color: white; font-size: 36px; font-weight: 700; margin-bottom: 12px; }
        .hero p { color: #94a3b8; font-size: 16px; max-width: 500px; margin: 0 auto; }
        .card { background: white; border-radius: 12px; box-shadow: 0 4px 24px rgba(0,0,0,0.08); max-width: 720px; margin: -40px auto 40px; padding: 40px; }
        .field { margin-bottom: 20px; }
        label { display: block; font-size: 13px; font-weight: 600; color: #475569; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 6px; }
        input, textarea { width: 100%; padding: 12px 14px; font-size: 14px; border: 1.5px solid #e2e8f0; border-radius: 8px; font-family: inherit; color: #1a1a2e; outline: none; }
        textarea { height: 80px; resize: vertical; }
        button { width: 100%; background: #0f172a; color: white; padding: 14px; border: none; border-radius: 8px; font-size: 15px; font-weight: 600; cursor: pointer; margin-top: 8px; }
    </style>
</head>
<body>
    <nav>
        <h1>Bridge<span>.</span></h1>
        <div>
            <a href="/">Home</a>
            <a href="/match">Find a Mentor</a>
            <a href="/signup">Become a Mentor</a>
        </div>
    </nav>
    <div class="hero">
        <h2>Become a Mentor</h2>
        <p>Share your experience and help the next generation find their path.</p>
    </div>
    <div class="card">
        <form method="POST" action="/signup">
            <div class="field"><label>Your Name</label><input name="name" placeholder="Jane Smith" required></div>
            <div class="field"><label>Industry / Role</label><input name="role" placeholder="e.g. Senior Product Manager at Google" required></div>
            <div class="field"><label>Years of Experience</label><input name="experience" placeholder="e.g. 8+" required></div>
            <div class="field"><label>What You Can Advise On</label><textarea name="advise" placeholder="e.g. Breaking into tech, resume reviews, interview prep..."></textarea></div>
            <div class="field"><label>Your Career Path</label><textarea name="career_path" placeholder="e.g. Business degree -> Analyst -> PM -> Director"></textarea></div>
            <div class="field"><label>Your Mentorship Style</label><input name="style" placeholder="e.g. Structured and goal-oriented, hands-on..." required></div>
            <div class="field"><label>Your Availability</label><input name="availability" placeholder="e.g. Biweekly sessions + async messaging" required></div>
            <button type="submit">Join as a Mentor &rarr;</button>
        </form>
    </div>
</body>
</html>"""

ACCOUNT_SIGNUP_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Bridge - Create Account</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f7fa; min-height: 100vh; }
        nav { background: #0f172a; padding: 16px 40px; }
        nav h1 { color: white; font-size: 20px; font-weight: 600; }
        nav h1 span { color: #38bdf8; }
        .card { background: white; border-radius: 12px; box-shadow: 0 4px 24px rgba(0,0,0,0.08); max-width: 420px; margin: 60px auto; padding: 40px; }
        h2 { margin-bottom: 20px; color: #0f172a; }
        .field { margin-bottom: 16px; }
        label { display: block; font-size: 13px; font-weight: 600; color: #475569; margin-bottom: 6px; }
        input, select { width: 100%; padding: 12px; font-size: 14px; border: 1.5px solid #e2e8f0; border-radius: 8px; }
        button { width: 100%; background: #0f172a; color: white; padding: 14px; border: none; border-radius: 8px; font-weight: 600; cursor: pointer; margin-top: 8px; }
    </style>
</head>
<body>
    <nav><h1>Bridge<span>.</span></h1></nav>
    <div class="card">
        <h2>Create Your Account</h2>
        <form method="POST" action="/signup-account">
            <div class="field"><label>Email</label><input type="email" name="email" required></div>
            <div class="field"><label>Password</label><input type="password" name="password" required></div>
            <div class="field">
                <label>I am a</label>
                <select name="role">
                    <option value="student">Student / Mentee</option>
                    <option value="mentor">Mentor</option>
                </select>
            </div>
            <button type="submit">Create Account</button>
        </form>
    </div>
</body>
</html>"""

LOGIN_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Bridge - Log In</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f7fa; min-height: 100vh; }
        nav { background: #0f172a; padding: 16px 40px; }
        nav h1 { color: white; font-size: 20px; font-weight: 600; }
        nav h1 span { color: #38bdf8; }
        .card { background: white; border-radius: 12px; box-shadow: 0 4px 24px rgba(0,0,0,0.08); max-width: 420px; margin: 60px auto; padding: 40px; }
        h2 { margin-bottom: 20px; color: #0f172a; }
        .field { margin-bottom: 16px; }
        label { display: block; font-size: 13px; font-weight: 600; color: #475569; margin-bottom: 6px; }
        input { width: 100%; padding: 12px; font-size: 14px; border: 1.5px solid #e2e8f0; border-radius: 8px; }
        button { width: 100%; background: #0f172a; color: white; padding: 14px; border: none; border-radius: 8px; font-weight: 600; cursor: pointer; margin-top: 8px; }
    </style>
</head>
<body>
    <nav><h1>Bridge<span>.</span></h1></nav>
    <div class="card">
        <h2>Log In</h2>
        <form method="POST" action="/login">
            <div class="field"><label>Email</label><input type="email" name="email" required></div>
            <div class="field"><label>Password</label><input type="password" name="password" required></div>
            <button type="submit">Log In</button>
        </form>
    </div>
</body>
</html>"""

THANKS_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Bridge - Thanks!</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f7fa; min-height: 100vh; }
        nav { background: #0f172a; padding: 16px 40px; display: flex; align-items: center; justify-content: space-between; }
        nav h1 { color: white; font-size: 20px; font-weight: 600; }
        nav h1 span { color: #38bdf8; }
        nav div { display: flex; gap: 24px; }
        nav a { color: #94a3b8; text-decoration: none; font-size: 14px; }
        .center { text-align: center; padding: 100px 40px; }
        .center h2 { font-size: 32px; color: #0f172a; margin-bottom: 12px; }
        .center p { color: #64748b; font-size: 16px; margin-bottom: 24px; }
        .center a { background: #0f172a; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 600; }
    </style>
</head>
<body>
    <nav>
        <h1>Bridge<span>.</span></h1>
        <div>
            <a href="/">Home</a>
            <a href="/match">Find a Mentor</a>
            <a href="/signup">Become a Mentor</a>
        </div>
    </nav>
    <div class="center">
        <h2>You're in. Welcome to Bridge.</h2>
        <p>Your profile has been added. Students will now be matched with you.</p>
        <a href="/">Go to home</a>
    </div>
</body>
</html>"""

init_db()
migrate_mentors_table()
init_users_table()
port = int(os.environ.get("PORT", 8080))
print(f"Server running at http://localhost:{port}")
HTTPServer(("", port), Handler).serve_forever()

