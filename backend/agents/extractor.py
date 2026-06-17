import json
import uuid
import os
from openai import OpenAI

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), timeout=30)
    return _client


MODEL = os.getenv("EXTRACTION_MODEL", "gpt-4o-mini")

_SYSTEM = "You extract scientific knowledge as structured JSON. Be precise, literal, and specific."

_PROMPT = """Analyze this text from a research paper and extract structured knowledge.

Return ONLY valid JSON in this exact format:
{
  "concepts": [
    {"name": "exact term from text", "type": "method|entity|result|hypothesis|material|disease|protein|algorithm|drug|gene|pathway|other", "context": "1-sentence description"}
  ],
  "relationships": [
    {"subject": "concept A", "predicate": "relationship verb", "object": "concept B"}
  ]
}

Extract 5-15 concepts and 3-10 relationships. Focus on scientific claims, not metadata.

TEXT:
"""


def extract_knowledge(chunks: list[dict], paper_id: str) -> dict:
    client = _get_client()
    all_concepts: list[dict] = []
    all_relationships: list[dict] = []

    batch_size = 3
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        combined = "\n\n".join(c["text"] for c in batch)[:6000]
        try:
            resp = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": _SYSTEM},
                    {"role": "user", "content": _PROMPT + combined},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
            )
            data = json.loads(resp.choices[0].message.content)

            for c in data.get("concepts", []):
                if c.get("name"):
                    all_concepts.append({
                        "id": str(uuid.uuid4()),
                        "paper_id": paper_id,
                        "name": c["name"],
                        "type": c.get("type", "entity"),
                        "context": c.get("context", ""),
                    })

            for r in data.get("relationships", []):
                if r.get("subject") and r.get("predicate") and r.get("object"):
                    all_relationships.append({
                        "id": str(uuid.uuid4()),
                        "paper_id": paper_id,
                        "subject": r["subject"],
                        "predicate": r["predicate"],
                        "object": r["object"],
                    })
        except Exception as e:
            print(f"[extractor] batch {i} error: {e}")
            continue

    return {"concepts": all_concepts, "relationships": all_relationships}
