import anthropic
import os
import sqlite3
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

DB = "mentors.db"

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS mentors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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

def get_mentors():
    conn = sqlite3.connect(DB)
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
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
        INSERT INTO mentors (name, role, experience, advise, career_path, style, availability)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
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

def get_match(student, mentors):
    client = anthropic.Anthropic()
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""You are a mentor matching assistant. Given a student profile and a list of mentors, rank the mentors from best to worst fit for this student. For each mentor, explain the pros and cons of the match.

STUDENT PROFILE:
{student}

MENTOR PROFILES:
{mentors}

Rank the mentors (1 = best fit). For each, give:
- Match score (1-10)
- Top 3 pros
- Top 2 cons
- One sentence summary of why they are or aren't a good fit"""
            }
        ]
    )
    return message.content[0].text

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/signup":
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(SIGNUP_HTML.encode())
        else:
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HOME_HTML.encode())

    def do_POST(self):
        length = int(self.headers["Content-Length"])
        data = urllib.parse.parse_qs(self.rfile.read(length).decode())
        flat = {k: v[0] for k, v in data.items()}

        if self.path == "/signup":
            save_mentor(flat)
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(THANKS_HTML.encode())
        else:
            student = flat.get("student", "")
            mentors = get_mentors()
            if not mentors:
                result = "No mentors have signed up yet. Check back soon!"
            else:
                result = get_match(student, mentors)
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            response = HOME_HTML.replace("RESULTS_HERE", result.replace("\n", "<br>"))
            self.wfile.write(response.encode())

    def log_message(self, format, *args):
        pass

HOME_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Bridge - Mentor Matching</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f7fa; color: #1a1a2e; min-height: 100vh; }
        nav { background: #0f172a; padding: 16px 40px; display: flex; align-items: center; justify-content: space-between; }
        nav h1 { color: white; font-size: 20px; font-weight: 600; }
        nav h1 span { color: #38bdf8; }
        nav a { color: #38bdf8; text-decoration: none; font-size: 14px; font-weight: 600; }
        .hero { background: #0f172a; padding: 60px 40px 80px; text-align: center; }
        .hero h2 { color: white; font-size: 36px; font-weight: 700; margin-bottom: 12px; }
        .hero p { color: #94a3b8; font-size: 16px; max-width: 500px; margin: 0 auto; }
        .card { background: white; border-radius: 12px; box-shadow: 0 4px 24px rgba(0,0,0,0.08); max-width: 720px; margin: -40px auto 40px; padding: 40px; }
        label { display: block; font-size: 13px; font-weight: 600; color: #475569; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 8px; }
        .hint { font-size: 13px; color: #94a3b8; margin-bottom: 12px; font-weight: normal; text-transform: none; letter-spacing: 0; }
        textarea { width: 100%; height: 180px; padding: 14px; font-size: 14px; border: 1.5px solid #e2e8f0; border-radius: 8px; resize: vertical; font-family: inherit; color: #1a1a2e; line-height: 1.6; outline: none; }
        button { width: 100%; background: #0f172a; color: white; padding: 14px; border: none; border-radius: 8px; font-size: 15px; font-weight: 600; cursor: pointer; margin-top: 16px; }
        .results { max-width: 720px; margin: 0 auto 60px; }
        .results-card { background: white; border-radius: 12px; box-shadow: 0 4px 24px rgba(0,0,0,0.08); padding: 32px 40px; border-top: 4px solid #38bdf8; font-size: 14px; line-height: 1.8; color: #334155; }
        .results-label { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; color: #38bdf8; margin-bottom: 16px; }
    </style>
</head>
<body>
    <nav>
        <h1>Bridge<span>.</span></h1>
        <a href="/signup">Become a Mentor</a>
    </nav>
    <div class="hero">
        <h2>Find Your Mentor Match</h2>
        <p>Enter your profile and our AI will match you with the right mentor for your goals.</p>
    </div>
    <div class="card">
        <label>Your Profile <span class="hint">Include: Name, Major/Year, Career goals, Skills you have, Skills you want to develop, What you want in a mentor</span></label>
        <form method="POST" action="/">
            <textarea name="student" placeholder="Name: &#10;Major/Year: &#10;Career goals: &#10;Skills I have: &#10;Skills I want to develop: &#10;What I want in a mentor:"></textarea>
            <button type="submit">Find My Mentor Match &rarr;</button>
        </form>
    </div>
    RESULTS_HERE
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
        nav a { color: #38bdf8; text-decoration: none; font-size: 14px; font-weight: 600; }
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
        <a href="/">Find a Mentor</a>
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

THANKS_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Bridge - Thanks!</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f7fa; min-height: 100vh; }
        nav { background: #0f172a; padding: 16px 40px; }
        nav h1 { color: white; font-size: 20px; font-weight: 600; }
        nav h1 span { color: #38bdf8; }
        .center { text-align: center; padding: 100px 40px; }
        .center h2 { font-size: 32px; color: #0f172a; margin-bottom: 12px; }
        .center p { color: #64748b; font-size: 16px; margin-bottom: 24px; }
        .center a { background: #0f172a; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 600; }
    </style>
</head>
<body>
    <nav><h1>Bridge<span>.</span></h1></nav>
    <div class="center">
        <h2>You're in. Welcome to Bridge.</h2>
        <p>Your profile has been added. Students will now be matched with you.</p>
        <a href="/">Go to home</a>
    </div>
</body>
</html>"""


init_db()
port = int(os.environ.get("PORT", 8080))
print(f"Server running at http://localhost:{port}")
HTTPServer(("", port), Handler).serve_forever()
