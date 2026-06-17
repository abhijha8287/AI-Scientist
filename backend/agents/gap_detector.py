import json
import uuid
import os
from openai import OpenAI

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), timeout=60)
    return _client


MODEL = os.getenv("PIPELINE_MODEL", "gpt-4o")

_SYSTEM = """You are an expert scientific research analyst. You identify genuine research gaps —
things that logically should have been studied but weren't, contradictions that need resolution,
and cross-domain opportunities invisible to any single researcher. Be specific, not generic."""

_PROMPT = """You have been given structured knowledge extracted from a set of research papers.

CONCEPTS EXTRACTED:
{concepts}

RELATIONSHIPS EXTRACTED:
{relationships}

Identify the 3-5 MOST IMPORTANT unexplored research gaps. Look for:
1. Missing edges in the knowledge graph — A affects B and B affects C, but A→C is unstudied
2. Contradictory claims — paper X says relationship is positive, paper Y says negative
3. Unstudied combinations — two concepts appear in the same papers but their interaction is never examined
4. Methodological gaps — a claim was made but never experimentally validated
5. Cross-domain transfers — a method from field A that could solve an open problem in field B

Return ONLY valid JSON:
{{
  "gaps": [
    {{
      "title": "concise gap title (max 10 words)",
      "description": "2-3 sentences describing exactly what is missing and why it matters scientifically",
      "evidence": "cite specific concepts and relationships from above that point to this gap",
      "rank": 1
    }}
  ]
}}

Rank 1 = highest priority. Each gap MUST cite specific concepts/relationships from the input.
"""


def detect_gaps(concepts: list[dict], relationships: list[dict]) -> list[dict]:
    client = _get_client()

    concept_summary = json.dumps(
        [{"name": c["name"], "type": c["type"]} for c in concepts[:100]]
    )
    rel_summary = json.dumps(
        [{"s": r["subject"], "p": r["predicate"], "o": r["object"]} for r in relationships[:120]]
    )

    prompt = _PROMPT.format(concepts=concept_summary, relationships=rel_summary)

    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        data = json.loads(resp.choices[0].message.content)
    except Exception as e:
        print(f"[gap_detector] API error: {e}")
        return []

    gaps = []
    for g in data.get("gaps", []):
        if g.get("title"):
            gaps.append({
                "id": str(uuid.uuid4()),
                "title": g["title"],
                "description": g.get("description", ""),
                "evidence": g.get("evidence", ""),
                "rank": int(g.get("rank", 99)),
            })

    return sorted(gaps, key=lambda x: x["rank"])
