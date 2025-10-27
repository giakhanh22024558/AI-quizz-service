# AI Quiz Generator - Flask API

A Flask-based REST API that generates AI-powered quizzes using Google's Gemini AI.

## Features

- Generate multiple-choice questions (MCQ)
- Generate essay questions
- Submit and score MCQ answers
- Get AI feedback on essay answers
- CORS-enabled for frontend integration

## Setup

1. Create virtual environment:
```bash
python -m venv venv
venv\Scripts\Activate.ps1
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python app.py
```

The API will be available at `http://localhost:5000`

## API Endpoints

### POST /generate
Generate a new quiz
```json
{
  "lesson": "Python Basics",
  "level": "Beginner",
  "numMCQ": 5,
  "numEssay": 2
}
```

### POST /submit_mcq
Submit MCQ answers for scoring

### POST /submit_essay
Submit essay answers for AI feedback

## Technologies

- Flask
- Google Generative AI (Gemini)
- Flask-CORS
- Markdown