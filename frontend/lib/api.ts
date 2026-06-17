const BASE = "/api";

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  if (!res.ok) {
    let msg = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      msg = body.detail || body.message || JSON.stringify(body);
    } catch {
      msg = (await res.text().catch(() => "")) || msg;
    }
    throw new Error(msg);
  }
  return res.json() as Promise<T>;
}

// ── Papers ────────────────────────────────────────────────────────────────────

export interface Paper {
  id: string;
  filename: string;
  status: string;
  source?: string;
  uploaded_at: string;
}

export async function uploadPapers(files: File[]): Promise<{ papers: Paper[] }> {
  const form = new FormData();
  files.forEach((f) => form.append("files", f));
  const res = await fetch(`${BASE}/papers`, { method: "POST", body: form });
  if (!res.ok) {
    let msg = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      msg = body.detail || body.message || JSON.stringify(body);
    } catch {
      msg = (await res.text().catch(() => "")) || msg;
    }
    throw new Error(msg);
  }
  return res.json();
}

export async function listPapers(): Promise<{ papers: Paper[] }> {
  return req("/papers");
}

export async function fetchFromWikipedia(
  topic: string,
  maxRelated = 5,
): Promise<{ papers: Paper[] }> {
  return req("/wiki", {
    method: "POST",
    body: JSON.stringify({ topic, max_related: maxRelated }),
  });
}

// ── Pipeline ──────────────────────────────────────────────────────────────────

export interface JobStatus {
  id: string;
  status: "pending" | "running" | "complete" | "failed";
  current_node: string;
  counts: Record<string, number | string>;
  error?: string;
  created_at: string;
  updated_at: string;
  paper_ids: string[];
}

export async function startPipeline(paper_ids: string[]): Promise<{ job_id: string }> {
  return req("/pipeline", {
    method: "POST",
    body: JSON.stringify({ paper_ids }),
  });
}

export async function getPipelineStatus(job_id: string): Promise<JobStatus> {
  return req(`/pipeline/${job_id}/status`);
}

export async function getPipelineResults(job_id: string): Promise<{
  gaps: Gap[];
  hypotheses: Hypothesis[];
}> {
  return req(`/pipeline/${job_id}/results`);
}

export async function listJobs(): Promise<{ jobs: JobStatus[] }> {
  return req("/jobs");
}

// ── Knowledge ─────────────────────────────────────────────────────────────────

export interface Concept {
  id: string;
  paper_id: string;
  name: string;
  type: string;
  context: string;
}

export interface Relationship {
  id: string;
  paper_id: string;
  subject: string;
  predicate: string;
  object: string;
}

export async function getKnowledge(job_id?: string): Promise<{
  concepts: Concept[];
  relationships: Relationship[];
}> {
  const qs = job_id ? `?job_id=${job_id}` : "";
  return req(`/knowledge${qs}`);
}

// ── Hypotheses ────────────────────────────────────────────────────────────────

export interface Gap {
  id: string;
  job_id: string;
  title: string;
  description: string;
  evidence: string;
  rank: number;
}

export interface Experiment {
  id: string;
  hypothesis_id: string;
  objective: string;
  methodology: string;
  variables: { independent: string[]; dependent: string[]; controlled: string[] };
  controls: string;
  metrics: string[];
  criteria: string;
}

export interface Hypothesis {
  id: string;
  gap_id: string;
  job_id: string;
  title: string;
  reasoning: string;
  mechanism: string;
  outcomes: string[];
  risks: string[];
  novelty_score: number;
  experiment?: Experiment;
  gap?: Gap;
}

// ── Chat ──────────────────────────────────────────────────────────────────────

export interface ChatMessage {
  id: string;
  query: string;
  response: string;
  created_at: string;
}

export async function sendChat(query: string, job_id?: string): Promise<{ response: string; chat_id: string }> {
  return req("/chat", {
    method: "POST",
    body: JSON.stringify({ query, job_id }),
  });
}

export async function getChatHistory(job_id?: string): Promise<{ history: ChatMessage[] }> {
  const qs = job_id ? `?job_id=${job_id}` : "";
  return req(`/chat/history${qs}`);
}
