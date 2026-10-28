# AI Scientist

A research assistant that reads papers or Wikipedia articles, finds gaps in the literature, proposes hypotheses and designs experiments to test them.

## Why this exists
An experiment in multi-step research automation: can a chain of LLM agents go from raw papers to testable ideas, while showing its reasoning so a person can check it?

## What it does
- Takes uploaded PDFs, or a topic name whose Wikipedia article and up to 5 linked articles are fetched
- Runs a 5-stage LangGraph pipeline:
  1. Paper Reader: extracts and chunks text
  2. Knowledge Extractor: pulls out concepts and relationships, creates embeddings
  3. Gap Detector: finds under-explored areas
  4. Hypothesis Generator: proposes testable hypotheses with novelty scores
  5. Experiment Designer: designs an experiment for each hypothesis
- Shows progress live, then hypotheses, a knowledge graph and experiments in the web UI
- Lets you chat with the model about its reasoning

## Project structure
```
AI-Scientist/
├── backend/
│   ├── agents/         The five pipeline agents
│   ├── pipeline.py     LangGraph workflow
│   ├── embeddings.py   OpenAI embedding calls
│   ├── db.py           SQLite storage
│   ├── main.py         FastAPI app
│   ├── Procfile, nixpacks.toml  Deployment config
│   └── requirements.txt         Python dependencies
├── frontend/
│   ├── app/            Next.js pages
│   ├── components/     UI components
│   └── lib/            API client and helpers
├── pdf/                Sample papers and generator script
├── start.bat           One-command start (Windows)
└── .env.example        Required settings
```

## Getting started
Requirements: Python 3.11+, Node.js 18+, an OpenAI API key.
```bash
git clone https://github.com/abhijha8287/AI-Scientist.git
cd AI-Scientist
cp .env.example backend/.env                # set OPENAI_API_KEY

cd backend                                  # terminal 1
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

cd frontend                                 # terminal 2
npm install
npm run dev                                 # http://localhost:3000
```
On Windows, `start.bat` starts both servers. Upload PDFs (samples are in `pdf/`) or fetch a Wikipedia topic, select the papers, then click **Run AI Scientist**.

## Configuration
| Variable | Purpose |
|:--|:--|
| `OPENAI_API_KEY` | OpenAI API key |
| `PIPELINE_MODEL` | Model for the reasoning stages |
| `EXTRACTION_MODEL` | Model for knowledge extraction |
| `EMBEDDING_MODEL` | Embedding model (default `text-embedding-3-small`) |
| `DATABASE_URL` | SQLite database path |
| `UPLOAD_DIR` | Where uploaded PDFs are stored |

## Tech stack
Python, FastAPI, LangGraph, OpenAI API, PyMuPDF, MediaWiki API, SQLite, Next.js 15, React 19, Tailwind CSS, TanStack Query, Zustand

## API reference

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/papers` | Upload PDF files |
| GET | `/api/papers` | List uploaded papers |
| POST | `/api/wiki` | Fetch Wikipedia articles by topic |
| POST | `/api/pipeline` | Start analysis job |
| GET | `/api/pipeline/{job_id}/status` | Poll job progress |
| GET | `/api/pipeline/{job_id}/results` | Fetch gaps & hypotheses |
| GET | `/api/knowledge` | Concepts & relationships |
| GET | `/api/jobs` | Recent jobs |
| POST | `/api/chat` | Chat with the AI |
| GET | `/api/chat/history` | Chat history |

### `/api/wiki` request body

```json
{
  "topic": "quantum error correction",
  "max_related": 5
}
```

Returns a list of papers added to the database (same shape as `/api/papers`). Papers sourced from Wikipedia carry `"source": "wikipedia"` and are shown with a globe icon in the UI.
