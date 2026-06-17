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

_SYSTEM = """You are an expert experimental scientist. You design rigorous, reproducible experiments.
Be domain-appropriate: biology uses wet lab methods, ML uses benchmarks and datasets, chemistry uses
chemical synthesis and analysis. Name specific techniques, instruments, reagents, or datasets.
Always include quantitative success criteria."""

_PROMPT = """Design a concrete experiment to test this hypothesis:

HYPOTHESIS: {title}
REASONING: {reasoning}
MECHANISM: {mechanism}
EXPECTED OUTCOMES: {outcomes}

Design a rigorous experiment. Name specific techniques, instruments, datasets, or reagents.

Return ONLY valid JSON:
{{
  "objective": "What this experiment will definitively prove or disprove (one sentence)",
  "methodology": "Step-by-step experimental procedure — be specific about techniques, tools, and parameters. At least 4 steps.",
  "variables": {{
    "independent": ["variable being manipulated (what you change)"],
    "dependent": ["variable being measured (what you observe)"],
    "controlled": ["variables held constant to ensure validity"]
  }},
  "controls": "Describe the control group/condition and why it's the right control for this hypothesis",
  "metrics": [
    "Specific metric with unit and measurement method (e.g., cell viability % measured by MTT assay)",
    "Second metric"
  ],
  "criteria": "Specific numerical thresholds: success = [condition], failure = [condition], inconclusive = [condition]"
}}
"""


def _to_str(val: object, fallback: str = "") -> str:
    """Coerce any value to a plain string safe for SQLite TEXT columns."""
    if val is None:
        return fallback
    if isinstance(val, (dict, list)):
        return json.dumps(val)
    return str(val)


def _to_list(val: object) -> list:
    """Coerce any value to a list for SQLite JSON storage."""
    if val is None:
        return []
    if isinstance(val, list):
        return val
    if isinstance(val, dict):
        return list(val.values())
    return [str(val)]


def design_experiments(hypotheses: list[dict]) -> list[dict]:
    client = _get_client()
    experiments = []

    for h in hypotheses:
        try:
            outcomes = h.get("outcomes", "[]")
            if isinstance(outcomes, str):
                outcomes = json.loads(outcomes)

            prompt = _PROMPT.format(
                title=h["title"],
                reasoning=h["reasoning"],
                mechanism=h["mechanism"],
                outcomes=json.dumps(outcomes),
            )
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

            experiments.append({
                "id": str(uuid.uuid4()),
                "hypothesis_id": h["id"],
                "objective": _to_str(data.get("objective")),
                "methodology": _to_str(data.get("methodology")),
                "variables": json.dumps(data.get("variables", {})),
                "controls": _to_str(data.get("controls")),
                "metrics": json.dumps(_to_list(data.get("metrics"))),
                "criteria": _to_str(data.get("criteria")),
            })
        except Exception as e:
            print(f"[experiment] error for hypothesis {h['id']}: {e}")
            continue

    return experiments
