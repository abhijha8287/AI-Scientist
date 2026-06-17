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

_SYSTEM = """You are an expert scientist generating precise, mechanistically-grounded scientific hypotheses.
Never be vague. Never say "X may affect Y" — say HOW and WHY at the molecular/computational/systems level.
Every hypothesis must be falsifiable and cite the evidence it builds on."""

_PROMPT = """A research gap has been identified from a set of papers:

GAP TITLE: {title}
GAP DESCRIPTION: {description}
EVIDENCE FROM PAPERS: {evidence}

Generate ONE specific, mechanistically-grounded hypothesis to address this gap.

The hypothesis MUST:
- State the specific mechanism (not just "X may affect Y" — explain the molecular/computational pathway)
- Reference the evidence that makes this plausible
- Be falsifiable with a real experiment
- Predict measurable outcomes with numerical criteria where possible

Return ONLY valid JSON:
{{
  "title": "Hypothesis title (one sentence, present tense, active voice)",
  "reasoning": "Why this hypothesis is plausible given the evidence — 3-4 sentences citing the specific relationships found in the papers",
  "mechanism": "The specific mechanistic explanation — HOW and WHY the effect would occur — 2-3 sentences at the appropriate domain level",
  "outcomes": [
    "Expected outcome 1 with measurable criterion (e.g., >20% reduction in X when Y is applied)",
    "Expected outcome 2 with measurable criterion"
  ],
  "risks": [
    "Assumption that could fail and why",
    "Alternative explanation that would invalidate this hypothesis"
  ]
}}
"""


def generate_hypotheses(gaps: list[dict]) -> list[dict]:
    client = _get_client()
    hypotheses = []

    for gap in gaps:
        try:
            prompt = _PROMPT.format(
                title=gap["title"],
                description=gap["description"],
                evidence=gap["evidence"],
            )
            resp = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": _SYSTEM},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
            )
            data = json.loads(resp.choices[0].message.content)

            def _s(v, fb=""):
                if v is None: return fb
                return json.dumps(v) if isinstance(v, (dict, list)) else str(v)

            def _lst(v):
                if isinstance(v, list): return v
                if isinstance(v, dict): return list(v.values())
                return [str(v)] if v else []

            if data.get("title"):
                hypotheses.append({
                    "id": str(uuid.uuid4()),
                    "gap_id": gap["id"],
                    "title": _s(data.get("title")),
                    "reasoning": _s(data.get("reasoning")),
                    "mechanism": _s(data.get("mechanism")),
                    "outcomes": json.dumps(_lst(data.get("outcomes"))),
                    "risks": json.dumps(_lst(data.get("risks"))),
                    "novelty_score": 0.0,
                })
        except Exception as e:
            print(f"[hypothesis] error for gap {gap['id']}: {e}")
            continue

    return hypotheses
