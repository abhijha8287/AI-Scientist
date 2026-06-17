import json
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END

import db
import embeddings as emb_utils
from agents import reader, extractor, gap_detector, hypothesis, experiment


class ScientistState(TypedDict):
    job_id: str
    paper_ids: list[str]
    chunks: list[dict]
    concepts: list[dict]
    relationships: list[dict]
    gaps: list[dict]
    hypotheses: list[dict]
    experiments: list[dict]
    error: Optional[str]


# ── Node 1: Read PDFs and chunk text ──────────────────────────────────────────

def paper_reader_node(state: ScientistState) -> ScientistState:
    job_id = state["job_id"]
    db.update_job(job_id, "paper_reader", {"status": "Reading PDFs..."})

    conn = db.get_conn()
    all_chunks: list[dict] = []
    failed: list[str] = []

    for paper_id in state["paper_ids"]:
        row = conn.execute("SELECT text_path, filename FROM papers WHERE id=?", (paper_id,)).fetchone()
        if not row:
            continue
        try:
            chunks = reader.extract_chunks(row["text_path"], paper_id)
            all_chunks.extend(chunks)
            for chunk in chunks:
                conn.execute(
                    "INSERT OR REPLACE INTO chunks (id, paper_id, text, embedding, chunk_index) VALUES (?, ?, ?, ?, ?)",
                    (chunk["id"], chunk["paper_id"], chunk["text"], None, chunk["chunk_index"]),
                )
            conn.execute("UPDATE papers SET status='processed' WHERE id=?", (paper_id,))
        except Exception as e:
            print(f"[reader] error for {paper_id}: {e}")
            failed.append(paper_id)
            conn.execute("UPDATE papers SET status='parse_failed' WHERE id=?", (paper_id,))

    conn.commit()
    conn.close()

    db.update_job(job_id, "paper_reader", {
        "chunks": len(all_chunks),
        "failed_papers": len(failed),
    })
    return {**state, "chunks": all_chunks}


# ── Node 2: Extract concepts and relationships; generate embeddings ───────────

def knowledge_extractor_node(state: ScientistState) -> ScientistState:
    job_id = state["job_id"]
    db.update_job(job_id, "knowledge_extractor", {
        "chunks": len(state["chunks"]),
        "status": "Extracting knowledge...",
    })

    conn = db.get_conn()
    all_concepts: list[dict] = []
    all_relationships: list[dict] = []

    # Group chunks by paper
    chunks_by_paper: dict[str, list[dict]] = {}
    for chunk in state["chunks"]:
        chunks_by_paper.setdefault(chunk["paper_id"], []).append(chunk)

    for paper_id, paper_chunks in chunks_by_paper.items():
        result = extractor.extract_knowledge(paper_chunks, paper_id)
        all_concepts.extend(result["concepts"])
        all_relationships.extend(result["relationships"])
        for c in result["concepts"]:
            conn.execute(
                "INSERT OR REPLACE INTO concepts (id, paper_id, name, type, context) VALUES (?, ?, ?, ?, ?)",
                (c["id"], c["paper_id"], c["name"], c["type"], c["context"]),
            )
        for r in result["relationships"]:
            conn.execute(
                "INSERT OR REPLACE INTO relationships (id, paper_id, subject, predicate, object) VALUES (?, ?, ?, ?, ?)",
                (r["id"], r["paper_id"], r["subject"], r["predicate"], r["object"]),
            )

    # Embed chunks and store
    embedded = 0
    for chunk in state["chunks"]:
        try:
            emb = emb_utils.embed(chunk["text"])
            conn.execute(
                "UPDATE chunks SET embedding=? WHERE id=?",
                (emb_utils.serialize_embedding(emb), chunk["id"]),
            )
            embedded += 1
        except Exception as e:
            print(f"[embeddings] chunk {chunk['id']}: {e}")

    conn.commit()
    conn.close()

    db.update_job(job_id, "knowledge_extractor", {
        "concepts": len(all_concepts),
        "relationships": len(all_relationships),
        "embedded_chunks": embedded,
    })
    return {**state, "concepts": all_concepts, "relationships": all_relationships}


# ── Node 3: Detect research gaps ──────────────────────────────────────────────

def gap_detector_node(state: ScientistState) -> ScientistState:
    job_id = state["job_id"]
    db.update_job(job_id, "gap_detector", {"status": "Detecting research gaps..."})

    gaps = gap_detector.detect_gaps(state["concepts"], state["relationships"])

    conn = db.get_conn()
    for gap in gaps:
        conn.execute(
            "INSERT OR REPLACE INTO gaps (id, job_id, title, description, evidence, rank) VALUES (?, ?, ?, ?, ?, ?)",
            (gap["id"], job_id, gap["title"], gap["description"], gap["evidence"], gap["rank"]),
        )
    conn.commit()
    conn.close()

    db.update_job(job_id, "gap_detector", {"gaps": len(gaps)})
    return {**state, "gaps": gaps}


# ── Node 4: Generate hypotheses ───────────────────────────────────────────────

def hypothesis_generator_node(state: ScientistState) -> ScientistState:
    job_id = state["job_id"]
    db.update_job(job_id, "hypothesis_generator", {"status": "Generating hypotheses..."})

    hypotheses = hypothesis.generate_hypotheses(state["gaps"])

    # Compute novelty scores from stored embeddings
    conn = db.get_conn()
    chunk_rows = conn.execute(
        "SELECT embedding FROM chunks WHERE embedding IS NOT NULL"
    ).fetchall()
    chunk_embeddings = [
        emb_utils.deserialize_embedding(row["embedding"])
        for row in chunk_rows
        if row["embedding"]
    ]

    for h in hypotheses:
        score = emb_utils.novelty_score(h["title"] + " " + h["mechanism"], chunk_embeddings)
        h["novelty_score"] = score
        conn.execute(
            "INSERT OR REPLACE INTO hypotheses "
            "(id, gap_id, job_id, title, reasoning, mechanism, outcomes, risks, novelty_score) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (h["id"], h["gap_id"], job_id, h["title"], h["reasoning"],
             h["mechanism"], h["outcomes"], h["risks"], h["novelty_score"]),
        )

    conn.commit()
    conn.close()

    db.update_job(job_id, "hypothesis_generator", {"hypotheses": len(hypotheses)})
    return {**state, "hypotheses": hypotheses}


# ── Node 5: Design experiments ────────────────────────────────────────────────

def experiment_designer_node(state: ScientistState) -> ScientistState:
    job_id = state["job_id"]
    db.update_job(job_id, "experiment_designer", {"status": "Designing experiments..."})

    experiments = experiment.design_experiments(state["hypotheses"])

    conn = db.get_conn()
    for exp in experiments:
        conn.execute(
            "INSERT OR REPLACE INTO experiments "
            "(id, hypothesis_id, job_id, objective, methodology, variables, controls, metrics, criteria) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (exp["id"], exp["hypothesis_id"], job_id, exp["objective"], exp["methodology"],
             exp["variables"], exp["controls"], exp["metrics"], exp["criteria"]),
        )
    conn.commit()
    conn.close()

    db.update_job(job_id, "experiment_designer", {"experiments": len(experiments)})
    return {**state, "experiments": experiments}


# ── Build the LangGraph pipeline ──────────────────────────────────────────────

def build_pipeline():
    graph: StateGraph = StateGraph(ScientistState)
    graph.add_node("paper_reader", paper_reader_node)
    graph.add_node("knowledge_extractor", knowledge_extractor_node)
    graph.add_node("gap_detector", gap_detector_node)
    graph.add_node("hypothesis_generator", hypothesis_generator_node)
    graph.add_node("experiment_designer", experiment_designer_node)

    graph.set_entry_point("paper_reader")
    graph.add_edge("paper_reader", "knowledge_extractor")
    graph.add_edge("knowledge_extractor", "gap_detector")
    graph.add_edge("gap_detector", "hypothesis_generator")
    graph.add_edge("hypothesis_generator", "experiment_designer")
    graph.add_edge("experiment_designer", END)

    return graph.compile()


_pipeline = None


def get_pipeline():
    global _pipeline
    if _pipeline is None:
        _pipeline = build_pipeline()
    return _pipeline


# Keep the name for backward compatibility — resolved lazily on first use
class _LazyPipeline:
    def invoke(self, state):
        return get_pipeline().invoke(state)


scientist_pipeline = _LazyPipeline()
