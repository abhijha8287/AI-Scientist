import sqlite3
import json
from pathlib import Path
import os

_HERE = Path(__file__).parent


def _resolve_db_path() -> Path:
    raw = os.getenv("DATABASE_URL", "ai_scientist.db")
    for prefix in ("sqlite:///./", "sqlite:///", "sqlite://"):
        if raw.startswith(prefix):
            raw = raw[len(prefix):]
            break
    p = Path(raw)
    return p if p.is_absolute() else _HERE / p


DB_PATH = _resolve_db_path()


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS papers (
            id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            text_path TEXT NOT NULL,
            status TEXT DEFAULT 'uploaded',
            source TEXT DEFAULT 'pdf',
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        /* safe migration for existing databases */

        CREATE TABLE IF NOT EXISTS chunks (
            id TEXT PRIMARY KEY,
            paper_id TEXT NOT NULL,
            text TEXT NOT NULL,
            embedding BLOB,
            chunk_index INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS concepts (
            id TEXT PRIMARY KEY,
            paper_id TEXT NOT NULL,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            context TEXT
        );

        CREATE TABLE IF NOT EXISTS relationships (
            id TEXT PRIMARY KEY,
            paper_id TEXT NOT NULL,
            subject TEXT NOT NULL,
            predicate TEXT NOT NULL,
            object TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            paper_ids TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            current_node TEXT DEFAULT 'queued',
            counts TEXT DEFAULT '{}',
            error TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS gaps (
            id TEXT PRIMARY KEY,
            job_id TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            evidence TEXT NOT NULL,
            rank INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS hypotheses (
            id TEXT PRIMARY KEY,
            gap_id TEXT NOT NULL,
            job_id TEXT NOT NULL,
            title TEXT NOT NULL,
            reasoning TEXT NOT NULL,
            mechanism TEXT NOT NULL,
            outcomes TEXT DEFAULT '[]',
            risks TEXT DEFAULT '[]',
            novelty_score REAL DEFAULT 0.0
        );

        CREATE TABLE IF NOT EXISTS experiments (
            id TEXT PRIMARY KEY,
            hypothesis_id TEXT NOT NULL,
            job_id TEXT NOT NULL,
            objective TEXT NOT NULL,
            methodology TEXT NOT NULL,
            variables TEXT DEFAULT '{}',
            controls TEXT,
            metrics TEXT DEFAULT '[]',
            criteria TEXT
        );

        CREATE TABLE IF NOT EXISTS chat_history (
            id TEXT PRIMARY KEY,
            job_id TEXT,
            query TEXT NOT NULL,
            context TEXT,
            response TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    # Safe migration: add source column to databases created before this column existed
    try:
        conn.execute("ALTER TABLE papers ADD COLUMN source TEXT DEFAULT 'pdf'")
    except Exception:
        pass
    conn.commit()
    conn.close()


def update_job(job_id: str, node: str, counts: dict, status: str = "running"):
    conn = get_conn()
    conn.execute(
        "UPDATE jobs SET current_node=?, counts=?, status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
        (node, json.dumps(counts), status, job_id),
    )
    conn.commit()
    conn.close()
