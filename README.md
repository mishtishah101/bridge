# Bridge

Bridge is an AI-powered mentor matching platform that connects students and professionals seeking career guidance with real mentors. Users submit a profile or resume, and Bridge uses the Anthropic API to surface the top 3 most relevant mentor matches — along with the ability to browse the full mentor directory.

**Live demo:** https://bridge-production-f9bb.up.railway.app

## Features

- **AI-powered matching** — Claude analyzes a student's goals and background against mentor profiles to generate ranked, personalized matches with explanations
- **User accounts** — separate student and mentor account types, with hashed password storage and session-based login
- **Persistent profiles** — students' submitted profiles are saved and reused automatically on return visits; mentors manage their own profile data
- **Mentor directory** — a browsable list of all approved mentors, with top-match badges shown to logged-in students
- **Admin approval workflow** — new mentor signups are held for manual approval before appearing publicly
- **Resume parsing** — students can upload a PDF resume, which is parsed and factored into the matching prompt

## Tech Stack

- **Backend:** Python (`http.server`, no framework)
- **Database:** PostgreSQL (hosted on Railway)
- **AI:** Anthropic API (Claude)
- **PDF parsing:** pypdf
- **Auth:** bcrypt password hashing, cookie-based sessions
- **Deployment:** Railway, with GitHub-based CI

## Running Locally

```bash
pip3 install -r requirements.txt
DATABASE_URL="your_postgres_url" ANTHROPIC_API_KEY="your_api_key" python3 app.py
```

The app will run at `http://localhost:8080`.

## Status

Actively developed. Built as a solo summer project to learn full-stack AI application development.
