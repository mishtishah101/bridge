import anthropic
import os

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

print("Enter student profile (press Enter twice when done):")
lines = []
while True:
    line = input()
    if line == "":
        break
    lines.append(line)
student = "\n".join(lines)

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

print(message.content[0].text)
