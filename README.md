# llm-project — Startup Analyst AI (Week 6)

One-liner
----------
Startup Analyst AI converts short startup descriptions into validated, structured JSON assessments for investors and founders.

Why this repo
--------------
This project demonstrates prompt engineering, deterministic chain logic, JSON schema validation, short-term memory, and a quick Gradio demo — all implemented without LangChain to show end-to-end LLM engineering.

Quick demo
----------
- Run tests: `PYTHONPATH=. pytest -q`
- Launch demo: `PYTHONPATH=. python app/gradio_app.py`
- Open: `http://127.0.0.1:7860`

Design decisions (short)
------------------------
- **Prompts split**: identity vs behavior vs style vs output schema to separate concerns and enable targeted testing.
- **Deterministic chain**: low temperature + explicit retries + validation to ensure high schema-conformance.
- **Validation**: pydantic ensures outputs are typed and safe for downstream pipelines.

How it works (example)
----------------------
Input:
“Marketplace connecting local suppliers to SMBs in Tier-2 cities. Revenue: transaction fees.”

Output (example):
```json
{
  "name": "Demo Startup",
  "summary": "Marketplace connecting local suppliers to SMBs; revenue: transaction fees.",
  "market": {
    "size_estimate": "unknown",
    "top_markets": ["India"],
    "competitors": []
  },
  "product": {
    "category": "marketplace",
    "differentiation": "focus on local logistics"
  },
  "business_model": {
    "revenue_streams": ["transaction fees"],
    "monetization_risks": []
  },
  "team": {
    "founders_count": "unknown",
    "strengths": [],
    "gaps": []
  },
  "risks": ["execution risk"],
  "recommendation": {
    "invest": "hold",
    "rationale": "insufficient data on unit economics"
  },
  "assumptions": ["market size unknown — estimated qualitatively"]
}

