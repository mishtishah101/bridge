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
<html>
<head>
    <title>Bridge - Mentor Matcher</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
        h1 { color: #333; }
        textarea { width: 100%; height: 200px; padding: 10px; font-size: 14px; }
        button { background: #4A90E2; color: white; padding: 10px 20px; border: none; font-size: 16px; cursor: pointer; margin-top: 10px; }
        button:hover { background: #357ABD; }
        .hint { color: #666; font-size: 13px; margin-bottom: 5px; }
        .results { margin-top: 30px; background: #f9f9f9; padding: 20px; border-left: 4px solid #4A90E2; }
    </style>
</head>
<body>
    <h1>Bridge - Mentor Matcher</h1>
    <p class="hint">Include: Name, Major/Year, Career goals, Skills you have, Skills you want to develop, What you want in a mentor</p>
    <form method="POST">
        <textarea name="student" placeholder="Enter your profile here..."></textarea>
        <br>
        <button type="submit">Find My Mentor Match</button>
    </form>
    <div class="results">RESULTS_HERE</div>
</body>
</html>
"""

print("Server running at http://localhost:8080")
HTTPServer(("", 8080), Handler).serve_forever()

