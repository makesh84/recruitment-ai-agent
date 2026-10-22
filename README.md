# Recruitment AI Agent

An AI-powered recruitment portfolio project that combines job search, resume parsing, technical skill extraction, and job recommendations.

## Features

- Keyword-based job search
- Semantic job search using Sentence Transformers and FAISS
- LangGraph-based request routing
- PDF resume text extraction using PyMuPDF
- Rule-based technical skill extraction
- Skill-overlap job ranking
- REST APIs built with FastAPI

## Technology Stack

**Backend:** Python, FastAPI

**AI and Search:** LangGraph, Sentence Transformers, FAISS, Ollama

**Resume Processing:** PyMuPDF

**Testing:** Pytest

## Project Structure

```text
recruitment-ai-agent/
├── app/
│   ├── main.py
│   ├── agent.py
│   ├── jobs.py
│   ├── matching.py
│   ├── semantic_search.py
│   ├── resume_parser.py
│   ├── skill_extractor.py
│   ├── recommendations.py
│   ├── resume_api.py
│   └── recommendation_api.py
├── tests/
├── requirements.txt
└── README.md
```

## Local Installation

```bash
git clone https://github.com/makesh84/recruitment-ai-agent.git
cd recruitment-ai-agent

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

## Start the API

```bash
python -m uvicorn app.main:app --reload
```

Open the API documentation:

http://127.0.0.1:8000/docs

## Testing

Run:

```bash
python -m pytest -q
```

Latest confirmed automated test result:

**23 tests passed in 13.28 seconds**, with one deprecation warning.

Additional recommendation tests require verification.

## Job Matching

The current matching algorithm measures skill overlap:

`Score = (Matched Required Skills / Total Required Skills) × 100`

This score is not a hiring probability or a complete assessment of candidate suitability.

## Current Limitations

- Uses fictional sample job listings
- Resume parsing requires selectable PDF text
- Skill extraction uses a predefined dictionary
- Ranking does not assess candidate experience or education
- Production security, scalability, and performance benchmarks are not yet validated

## Roadmap

- [ ] Verify end-to-end resume recommendations
- [ ] Add persistent job and candidate storage
- [ ] Build a larger job-matching evaluation dataset
- [ ] Measure ranking quality and API latency
- [ ] Add Docker deployment and CI/CD
- [ ] Add monitoring and structured logging
