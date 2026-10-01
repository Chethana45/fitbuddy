# 5. Project Development Phase

The FitBuddy source code lives at the **repository root** so it can be run directly
(`uvicorn app.main:app --reload` from the root folder):

| Folder / file | Contents |
|---|---|
| [`app/`](../app) | FastAPI application: routes, Gemini integration, database, templates, static files |
| [`tests/`](../tests) | 245 pytest tests, Locust load test, CPU/memory monitor |
| [`reports/`](../reports) | Load-test report, performance summary, repo audit |
| [`requirements.txt`](../requirements.txt) | Pinned dependencies |
| [`.env.example`](../.env.example) | Configuration template (copy to `.env`) |

Setup and run instructions are in the root [README](../README.md) and in
`7.Project Documentation/Project Executable Files.pdf`.

Phase documents in this folder:
- Code-Layout, Readability and Reusability.pdf
- Coding & Solution.pdf
- No. of Functional Features Included in the Solution.pdf
