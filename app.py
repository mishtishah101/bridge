import anthropic
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

mentors = """
MENTOR 1 - Career Navigator
Industry/Role: Senior Product Manager / Strategy Consultant
Years of experience: 12+
Can advise on: Career exploration, breaking into tech/business, resume, networking, long-term roadmaps
Career path: Business degree -> Analyst -> Product/Strategy -> Leadership
Mentorship style: Structured and goal-oriented, gives action steps
Availability: 2 virtual sessions/month + async messaging

MENTOR 2 - Skill Builder
Industry/Role: Data Analytics & AI Professional
Years of experience: 7+
Can advise on: Technical and business skills, AI tools, portfolio building, certifications
Career path: Entry-level analyst -> Business/Data Analyst -> AI specialization
Mentorship style: Hands-on and project-based, learning by doing
Availability: Weekly office hours + monthly skill workshops

MENTOR 3 - Network Connector
Industry/Role: Startup Founder / People & Talent Leader
Years of experience: 15+
Can advise on: Professional relationships, leadership, personal branding, entrepreneurship
Career path: Corporate -> Leadership -> Founded ventures -> Mentoring
Mentorship style: Conversational and connection-focused
Availability: Monthly 1:1 + networking events
"""

def get_match(student):
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

Rank the mentors 1 to 3 (1 = best fit). For each, give:
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
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(HTML.encode())

    def do_POST(self):
        length = int(self.headers["Content-Length"])
        data = self.rfile.read(length).decode()
        params = urllib.parse.parse_qs(data)
        student = params.get("student", [""])[0]
        result = get_match(student)
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        response = HTML.replace("RESULTS_HERE", result.replace("\n", "<br>"))
        self.wfile.write(response.encode())

    def log_message(self, format, *args):
        pass

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bridge - Mentor Matching</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f7fa;
            color: #1a1a2e;
            min-height: 100vh;
        }
        nav {
            background: #0f172a;
            padding: 16px 40px;
            display: flex;
            align-items: center;
        }
        nav h1 {
            color: white;
            font-size: 20px;
            font-weight: 600;
            letter-spacing: 0.5px;
        }
        nav span {
            color: #38bdf8;
        }
        .hero {
            background: #0f172a;
            padding: 60px 40px 80px;
            text-align: center;
        }
        .hero h2 {
            color: white;
            font-size: 36px;
            font-weight: 700;
            margin-bottom: 12px;
        }
        .hero p {
            color: #94a3b8;
            font-size: 16px;
            max-width: 500px;
            margin: 0 auto;
        }
        .card {
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 24px rgba(0,0,0,0.08);
            max-width: 720px;
            margin: -40px auto 40px;
            padding: 40px;
        }
        label {
            display: block;
            font-size: 13px;
            font-weight: 600;
            color: #475569;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            margin-bottom: 8px;
        }
        .hint {
            font-size: 13px;
            color: #94a3b8;
            margin-bottom: 12px;
            font-weight: normal;
            text-transform: none;
            letter-spacing: 0;
        }
        textarea {
            width: 100%;
            height: 180px;
            padding: 14px;
            font-size: 14px;
            border: 1.5px solid #e2e8f0;
            border-radius: 8px;
            resize: vertical;
            font-family: inherit;
            color: #1a1a2e;
            line-height: 1.6;
            outline: none;
            transition: border-color 0.2s;
        }
        textarea:focus {
            border-color: #38bdf8;
        }
        button {
            width: 100%;
            background: #0f172a;
            color: white;
            padding: 14px;
            border: none;
            border-radius: 8px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            margin-top: 16px;
            letter-spacing: 0.3px;
            transition: background 0.2s;
        }
        button:hover {
            background: #1e293b;
        }
        .results-section {
            max-width: 720px;
            margin: 0 auto 60px;
            padding: 0 0px;
        }
        .results-card {
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 24px rgba(0,0,0,0.08);
            padding: 32px 40px;
            border-top: 4px solid #38bdf8;
            font-size: 14px;
            line-height: 1.8;
            color: #334155;
        }
        .results-label {
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #38bdf8;
            margin-bottom: 16px;
        }
    </style>
</head>
<body>
    <nav>
        <h1>Bridge<span>.</span></h1>
    </nav>
    <div class="hero">
        <h2>Find Your Mentor Match</h2>
        <p>Enter your profile and our AI will match you with the right mentor for your goals.</p>
    </div>
    <div class="card">
        <label>Your Profile
            <span class="hint">Include: Name, Major/Year, Career goals, Skills you have, Skills you want to develop, What you want in a mentor</span>
        </label>
        <form method="POST">
            <textarea name="student" placeholder="Name: &#10;Major/Year: &#10;Career goals: &#10;Skills I have: &#10;Skills I want to develop: &#10;What I want in a mentor:"></textarea>
            <button type="submit">Find My Mentor Match &rarr;</button>
        </form>
    </div>
    RESULTS_SECTION
</body>
</html>
"""

HTML = HTML.replace("RESULTS_SECTION", "")

def build_response(result):
    results_html = f"""
    <div class="results-section">
        <div class="results-card">
            <div class="results-label">Your Mentor Match Results</div>
            {result.replace(chr(10), '<br>')}
        </div>
    </div>
    """
    return HTML.replace("", results_html)

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(HTML.encode())

    def do_POST(self):
        length = int(self.headers["Content-Length"])
        data = self.rfile.read(length).decode()
        params = urllib.parse.parse_qs(data)
        student = params.get("student", [""])[0]
        result = get_match(student)
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(build_response(result).encode())

    def log_message(self, format, *args):
        pass

print("Server running at http://localhost:8080")
HTTPServer(("", 8080), Handler).serve_forever()
