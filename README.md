# AI Scientist

An AI-powered research assistant that reads scientific papers, identifies knowledge gaps, generates novel hypotheses, and designs experiments — all automatically.

## What it does

Feed it research content — either by uploading PDFs or by typing a Wikipedia topic — and the system runs a 5-stage LangGraph pipeline:

1. **Paper Reader** — extracts and chunks text from PDFs or Wikipedia articles
2. **Knowledge Extractor** — pulls out concepts, relationships, and generates embeddings
3. **Gap Detector** — identifies underexplored areas in the literature
4. **Hypothesis Generator** — proposes testable hypotheses with novelty scores
5. **Experiment Designer** — designs experiments for each hypothesis

Results are viewable in a web UI, and you can chat with the AI to explore its reasoning.

### Wikipedia ingestion

Instead of uploading files, type any research topic in the **Fetch from Wikipedia** card on the home page. The app:

1. Looks up the canonical Wikipedia article for the topic
2. Fetches up to 5 related articles via internal links
3. Saves them as text files and adds them to your paper list (shown with a globe icon)
4. Lets you run the same pipeline on them immediately

This makes it easy to explore any field without needing PDFs — just type "CRISPR", "transformer neural network", "quantum error correction", etc.

## Tech stack

| Layer | Tech |
|---|---|
| Backend | FastAPI + LangGraph + OpenAI |
| PDF parsing | PyMuPDF |
| Wikipedia | MediaWiki API (`w/api.php`) |
| Embeddings | OpenAI `text-embedding-3-small` |
| Database | SQLite (WAL mode) |
| Frontend | Next.js 15, React 19, Tailwind CSS |
| State | TanStack Query + Zustand |

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- An OpenAI API key

### 1. Configure environment

```bash
cp .env.example backend/.env
```

Edit `backend/.env` and set your key:

```
OPENAI_API_KEY=sk-...
```

### 2. Start both servers

**Windows (one command):**

```bat
start.bat
```

**Manual:**

```bash
# Terminal 1 — backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Terminal 2 — frontend
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Usage

1. **Upload PDFs** — drag and drop PDF papers onto the home page, or
   **Fetch from Wikipedia** — type a topic name and click "Fetch Articles"
2. **Select** — check the papers you want to analyse (Wikipedia articles auto-select)
3. **Run** — click "Run AI Scientist" to start the pipeline
4. **Monitor** — watch the pipeline progress in real time
5. **Explore** — browse hypotheses, knowledge graph, and designed experiments
6. **Chat** — ask the AI to explain gaps, mechanisms, and reasoning

## Project structure

```
.
├── backend/
│   ├── agents/
│   │   ├── reader.py        # PDF → text chunks
│   │   ├── extractor.py     # concepts & relationships
│   │   ├── gap_detector.py  # research gap analysis
│   │   ├── hypothesis.py    # hypothesis generation
│   │   └── experiment.py    # experiment design
│   ├── main.py              # FastAPI routes
│   ├── pipeline.py          # LangGraph state machine
│   ├── db.py                # SQLite schema & helpers
│   ├── embeddings.py        # embed / cosine sim / novelty score
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── page.tsx         # upload & paper selection
│   │   ├── pipeline/[jobId] # live pipeline progress
│   │   ├── hypotheses/      # results browser
│   │   ├── knowledge/       # concept & relationship graph
│   │   └── chat/            # conversational interface
│   └── components/ui/       # shadcn-style UI primitives
├── .env.example
└── start.bat
```

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
