import json
import os
import re
import uuid
import urllib.request
import urllib.parse
from pathlib import Path
from typing import List

from dotenv import load_dotenv

load_dotenv()

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from pydantic import BaseModel

import db
import embeddings as emb_utils
from pipeline import ScientistState, scientist_pipeline

app = FastAPI(title="AI Scientist API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_UPLOAD_RAW = Path(os.getenv("UPLOAD_DIR", "./uploads"))
UPLOAD_DIR = _UPLOAD_RAW if _UPLOAD_RAW.is_absolute() else Path(__file__).parent / _UPLOAD_RAW
UPLOAD_DIR.mkdir(exist_ok=True)


@app.on_event("startup")
def startup():
    db.init_db()


# ── Papers ────────────────────────────────────────────────────────────────────


@app.post("/api/papers")
async def upload_papers(files: List[UploadFile] = File(...)):
    uploaded = []
    conn = db.get_conn()
    try:
        for f in files:
            if not f.filename or not f.filename.lower().endswith(".pdf"):
                continue
            paper_id = str(uuid.uuid4())
            dest = UPLOAD_DIR / f"{paper_id}.pdf"
            content = await f.read()
            dest.write_bytes(content)
            conn.execute(
                "INSERT INTO papers (id, filename, text_path, status) VALUES (?, ?, ?, ?)",
                (paper_id, f.filename, str(dest), "uploaded"),
            )
            uploaded.append({"id": paper_id, "filename": f.filename})
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")
    finally:
        conn.close()
    return {"papers": uploaded}


@app.get("/api/papers")
def list_papers():
    conn = db.get_conn()
    rows = conn.execute(
        "SELECT id, filename, status, source, uploaded_at FROM papers ORDER BY uploaded_at DESC"
    ).fetchall()
    conn.close()
    return {"papers": [dict(r) for r in rows]}


# ── Wikipedia ─────────────────────────────────────────────────────────────────

WIKI_REST = "https://en.wikipedia.org/api/rest_v1"
WIKI_MW = "https://en.wikipedia.org/w/api.php"
WIKI_HEADERS = {"User-Agent": "AI-Scientist/1.0 (research tool)"}


def _wiki_rest_get(path: str) -> dict:
    url = f"{WIKI_REST}{path}"
    r = urllib.request.Request(url, headers=WIKI_HEADERS)
    with urllib.request.urlopen(r, timeout=10) as resp:
        return json.loads(resp.read().decode())


def _wiki_mw_get(params: dict) -> dict:
    params["format"] = "json"
    url = f"{WIKI_MW}?{urllib.parse.urlencode(params)}"
    r = urllib.request.Request(url, headers=WIKI_HEADERS)
    with urllib.request.urlopen(r, timeout=15) as resp:
        return json.loads(resp.read().decode())


def _wiki_article_text(title: str) -> str:
    data = _wiki_mw_get({
        "action": "query",
        "prop": "extracts",
        "titles": title,
        "explaintext": "1",
        "exlimit": "1",
    })
    pages = data.get("query", {}).get("pages", {})
    if not pages:
        return ""
    page = next(iter(pages.values()))
    return page.get("extract", "")


def _wiki_related_titles(title: str, max_related: int) -> list[str]:
    try:
        data = _wiki_mw_get({
            "action": "query",
            "prop": "links",
            "titles": title,
            "pllimit": str(max_related * 4),
            "plnamespace": "0",
        })
        pages = data.get("query", {}).get("pages", {})
        if not pages:
            return []
        page = next(iter(pages.values()))
        links = page.get("links", [])
        return [lnk["title"] for lnk in links if lnk.get("title")][:max_related]
    except Exception:
        return []


class WikiRequest(BaseModel):
    topic: str
    max_related: int = 5


@app.post("/api/wiki")
async def fetch_wikipedia(body: WikiRequest):
    if not body.topic.strip():
        raise HTTPException(400, "topic must not be empty")

    # Resolve canonical title and check it's not a disambiguation page
    encoded = urllib.parse.quote(body.topic.strip(), safe="")
    try:
        summary = _wiki_rest_get(f"/page/summary/{encoded}")
    except Exception as e:
        raise HTTPException(404, f"Wikipedia article not found for '{body.topic}': {e}")

    if summary.get("type") == "disambiguation":
        raise HTTPException(422, f"'{body.topic}' is a disambiguation page. Try a more specific topic.")

    canonical = summary.get("title", body.topic.strip())

    # Collect articles: main + related
    titles_to_fetch = [canonical] + _wiki_related_titles(canonical, body.max_related)

    conn = db.get_conn()
    uploaded = []
    try:
        for title in titles_to_fetch:
            try:
                text = _wiki_article_text(title)
            except Exception:
                continue
            if not text.strip():
                continue

            paper_id = str(uuid.uuid4())
            dest = UPLOAD_DIR / f"{paper_id}.txt"
            dest.write_text(text, encoding="utf-8")

            conn.execute(
                "INSERT INTO papers (id, filename, text_path, status, source) VALUES (?, ?, ?, ?, ?)",
                (paper_id, f"{title} (Wikipedia)", str(dest), "uploaded", "wikipedia"),
            )
            uploaded.append({"id": paper_id, "filename": f"{title} (Wikipedia)", "source": "wikipedia"})

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(500, f"Wikipedia fetch failed: {e}")
    finally:
        conn.close()

    if not uploaded:
        raise HTTPException(502, f"Could not extract text from any Wikipedia articles for '{body.topic}'.")

    return {"papers": uploaded}


# ── Pipeline ──────────────────────────────────────────────────────────────────


def _run_pipeline(job_id: str, paper_ids: list[str]):
    conn = db.get_conn()
    conn.execute(
        "UPDATE jobs SET status='running', current_node='paper_reader' WHERE id=?",
        (job_id,),
    )
    conn.commit()
    conn.close()

    try:
        initial: ScientistState = {
            "job_id": job_id,
            "paper_ids": paper_ids,
            "chunks": [],
            "concepts": [],
            "relationships": [],
            "gaps": [],
            "hypotheses": [],
            "experiments": [],
            "error": None,
        }
        scientist_pipeline.invoke(initial)

        conn = db.get_conn()
        conn.execute(
            "UPDATE jobs SET status='complete', current_node='done', updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (job_id,),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[pipeline] job {job_id} failed: {e}")
        conn = db.get_conn()
        conn.execute(
            "UPDATE jobs SET status='failed', error=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (str(e), job_id),
        )
        conn.commit()
        conn.close()


class PipelineRequest(BaseModel):
    paper_ids: list[str]


@app.post("/api/pipeline")
async def start_pipeline(body: PipelineRequest, background_tasks: BackgroundTasks):
    if not body.paper_ids:
        raise HTTPException(400, "paper_ids must not be empty")

    job_id = str(uuid.uuid4())
    conn = db.get_conn()
    conn.execute(
        "INSERT INTO jobs (id, paper_ids, status, current_node, counts) VALUES (?, ?, ?, ?, ?)",
        (job_id, json.dumps(body.paper_ids), "pending", "queued", "{}"),
    )
    conn.commit()
    conn.close()

    background_tasks.add_task(_run_pipeline, job_id, body.paper_ids)
    return {"job_id": job_id}


@app.get("/api/pipeline/{job_id}/status")
def pipeline_status(job_id: str):
    conn = db.get_conn()
    row = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, "Job not found")
    data = dict(row)
    data["counts"] = json.loads(data.get("counts") or "{}")
    data["paper_ids"] = json.loads(data.get("paper_ids") or "[]")
    return data


@app.get("/api/pipeline/{job_id}/results")
def pipeline_results(job_id: str):
    conn = db.get_conn()
    gaps = [dict(r) for r in conn.execute(
        "SELECT * FROM gaps WHERE job_id=? ORDER BY rank", (job_id,)
    ).fetchall()]
    hypotheses = [dict(r) for r in conn.execute(
        "SELECT * FROM hypotheses WHERE job_id=? ORDER BY novelty_score DESC", (job_id,)
    ).fetchall()]
    experiments = [dict(r) for r in conn.execute(
        "SELECT * FROM experiments WHERE job_id=?", (job_id,)
    ).fetchall()]
    conn.close()

    for h in hypotheses:
        h["outcomes"] = json.loads(h.get("outcomes") or "[]")
        h["risks"] = json.loads(h.get("risks") or "[]")

    for e in experiments:
        e["variables"] = json.loads(e.get("variables") or "{}")
        e["metrics"] = json.loads(e.get("metrics") or "[]")

    exp_by_hyp = {e["hypothesis_id"]: e for e in experiments}
    for h in hypotheses:
        h["experiment"] = exp_by_hyp.get(h["id"])

    gap_by_id = {g["id"]: g for g in gaps}
    for h in hypotheses:
        h["gap"] = gap_by_id.get(h["gap_id"])

    return {"gaps": gaps, "hypotheses": hypotheses}


# ── Knowledge ─────────────────────────────────────────────────────────────────


@app.get("/api/knowledge")
def get_knowledge(job_id: str | None = None):
    conn = db.get_conn()

    if job_id:
        row = conn.execute("SELECT paper_ids FROM jobs WHERE id=?", (job_id,)).fetchone()
        if row:
            paper_ids = json.loads(row["paper_ids"])
            placeholders = ",".join("?" * len(paper_ids))
            concepts = [dict(r) for r in conn.execute(
                f"SELECT * FROM concepts WHERE paper_id IN ({placeholders}) LIMIT 300",
                paper_ids,
            ).fetchall()]
            relationships = [dict(r) for r in conn.execute(
                f"SELECT * FROM relationships WHERE paper_id IN ({placeholders}) LIMIT 300",
                paper_ids,
            ).fetchall()]
        else:
            concepts, relationships = [], []
    else:
        concepts = [dict(r) for r in conn.execute("SELECT * FROM concepts LIMIT 300").fetchall()]
        relationships = [dict(r) for r in conn.execute("SELECT * FROM relationships LIMIT 300").fetchall()]

    conn.close()
    return {"concepts": concepts, "relationships": relationships}


# ── Jobs listing ──────────────────────────────────────────────────────────────


@app.get("/api/jobs")
def list_jobs():
    conn = db.get_conn()
    rows = conn.execute(
        "SELECT id, status, current_node, counts, created_at, updated_at FROM jobs ORDER BY created_at DESC LIMIT 20"
    ).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        d["counts"] = json.loads(d.get("counts") or "{}")
        result.append(d)
    return {"jobs": result}


# ── Chat ──────────────────────────────────────────────────────────────────────


class ChatRequest(BaseModel):
    query: str
    job_id: str | None = None


@app.post("/api/chat")
async def chat(body: ChatRequest):
    if not body.query.strip():
        raise HTTPException(400, "query must not be empty")

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), timeout=30)
    conn = db.get_conn()

    # Retrieve relevant chunks via embedding similarity
    query_emb = emb_utils.embed(body.query)

    if body.job_id:
        row = conn.execute("SELECT paper_ids FROM jobs WHERE id=?", (body.job_id,)).fetchone()
        paper_ids = json.loads(row["paper_ids"]) if row else []
        if paper_ids:
            placeholders = ",".join("?" * len(paper_ids))
            chunk_rows = conn.execute(
                f"SELECT text, embedding FROM chunks WHERE paper_id IN ({placeholders}) AND embedding IS NOT NULL",
                paper_ids,
            ).fetchall()
        else:
            chunk_rows = conn.execute(
                "SELECT text, embedding FROM chunks WHERE embedding IS NOT NULL LIMIT 150"
            ).fetchall()
    else:
        chunk_rows = conn.execute(
            "SELECT text, embedding FROM chunks WHERE embedding IS NOT NULL LIMIT 150"
        ).fetchall()

    scored = []
    for row in chunk_rows:
        if row["embedding"]:
            sim = emb_utils.cosine_sim(query_emb, emb_utils.deserialize_embedding(row["embedding"]))
            scored.append((sim, row["text"]))
    scored.sort(key=lambda x: -x[0])
    top_context = "\n\n---\n\n".join(text for _, text in scored[:5])

    # Retrieve AI-generated insights for context
    if body.job_id:
        gaps = [dict(r) for r in conn.execute(
            "SELECT title, description FROM gaps WHERE job_id=? ORDER BY rank LIMIT 5",
            (body.job_id,),
        ).fetchall()]
        hyps = [dict(r) for r in conn.execute(
            "SELECT title, mechanism FROM hypotheses WHERE job_id=? ORDER BY novelty_score DESC LIMIT 3",
            (body.job_id,),
        ).fetchall()]
    else:
        gaps, hyps = [], []

    system_prompt = f"""You are the AI Scientist, an expert scientific reasoning assistant.

You have analyzed research papers and identified the following insights:

RESEARCH GAPS IDENTIFIED:
{json.dumps(gaps, indent=2)}

TOP HYPOTHESES:
{json.dumps(hyps, indent=2)}

RELEVANT PAPER CONTEXT:
{top_context[:3000]}

Answer the user's scientific questions based on this knowledge. Be specific, cite evidence,
and explain your reasoning mechanistically. If asked why a hypothesis was generated,
walk through the gap → hypothesis → mechanism chain."""

    resp = client.chat.completions.create(
        model=os.getenv("PIPELINE_MODEL", "gpt-4o"),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": body.query},
        ],
        temperature=0.3,
    )
    answer = resp.choices[0].message.content

    chat_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO chat_history (id, job_id, query, context, response) VALUES (?, ?, ?, ?, ?)",
        (chat_id, body.job_id, body.query, top_context[:500], answer),
    )
    conn.commit()
    conn.close()

    return {"response": answer, "chat_id": chat_id}


@app.get("/api/chat/history")
def chat_history(job_id: str | None = None):
    conn = db.get_conn()
    if job_id:
        rows = conn.execute(
            "SELECT id, query, response, created_at FROM chat_history WHERE job_id=? ORDER BY created_at",
            (job_id,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id, query, response, created_at FROM chat_history ORDER BY created_at DESC LIMIT 50"
        ).fetchall()
    conn.close()
    return {"history": [dict(r) for r in rows]}


@app.get("/api/health")
def health():
    return {"status": "ok"}
