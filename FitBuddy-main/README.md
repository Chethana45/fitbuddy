# FitBuddy - AI Fitness Plan Generator

FitBuddy is a FastAPI web application that uses Google Gemini models to
generate personalized seven-day workout plans, nutrition/recovery tips, and
feedback-based plan refinements. It stores users and plans with SQLite and
SQLAlchemy and renders the interface with Jinja2.

## Repository Structure

```text
fitbuddy_GenAI_project/
├── .vscode/
├── FitBuddy/
│   ├── app/
│   ├── static/
│   ├── docs/
│   ├── screenshots/
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md
├── Project Documents/
│   ├── _Original Templates/
│   ├── 1. Brainstorming & Ideation/
│   ├── 2. Requirement Analysis/
│   ├── 3. Project Design Phase/
│   ├── 4. Project Planning Phase/
│   ├── 5. Project Development Phase/
│   ├── 6. Project Testing/
│   ├── 7. Project Documentation/
│   └── 8. Project Demonstration/
├── .gitignore
├── README.md
├── PROJECT_DOCUMENTATION_CHECKLIST.md
└── PROJECT_DOCUMENTATION_REPORT.md
```

`FitBuddy/` contains the working application and five screenshots captured
from a live run. `Project Documents/` contains the 22 official documents, each
as an editable DOCX and a PDF exported from it, plus the untouched templates in
`_Original Templates/`. See `PROJECT_DOCUMENTATION_REPORT.md` for what was
tested and what still needs manual input.

## Run the application

From the repository root:

```powershell
cd FitBuddy
python -m venv fitbuddy-env
.\fitbuddy-env\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Set `GEMINI_API_KEY` in `FitBuddy/.env`, then run:

```powershell
python -m uvicorn app.main:app --reload
```

Open:

- http://127.0.0.1:8000
- http://127.0.0.1:8000/docs
- http://127.0.0.1:8000/view-all-users

See [FitBuddy/README.md](./FitBuddy/README.md) for application details and
[FitBuddy/docs/](./FitBuddy/docs/) for architecture, API, and testing
documentation.
