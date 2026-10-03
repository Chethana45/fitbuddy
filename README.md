# FitBuddy - AI Fitness Plan Generator using Gemini Models

FitBuddy is a modern web application that generates personalized 7-day workout plans using Google Gemini AI. Users provide their fitness profile (name, age, gender, weight, goal, and intensity), and the app creates a custom fitness plan with optional nutrition guidance and iterative plan improvements based on feedback.

Built with FastAPI, SQLAlchemy, and a simple Jinja2-based frontend, FitBuddy is designed to help users get a tailored training plan quickly and easily.

## Features

- Personalized 7-day workout plan generation
- AI-powered fitness coaching via Google Gemini
- User profile storage in SQLite
- Workout plan history per user
- Feedback-based plan revision
- Nutrition or recovery tip generation based on goal
- Simple web UI for interaction
- REST API endpoints for easy extension

## Tech Stack

- Python
- FastAPI
- SQLAlchemy
- SQLite
- Jinja2
- Google Generative AI (Gemini)
- Pydantic
- python-dotenv

## Project Structure

```text
FitBuddy-AI-Fitness-Plan-Generator-using-Gemini-Models/
├── ai_service.py
├── crud.py
├── database.py
├── main.py
├── models.py
├── schemas.py
├── requirements.txt
├── test_models.py
├── static/
│   ├── css/
│   └── js/
├── templates/
│   └── index.html
├── fitbuddy.db
├── README.md
└── .env
