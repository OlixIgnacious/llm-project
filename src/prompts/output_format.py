"""
Output format prompt and schema instructions.
Export: OUTPUT_FORMAT_PROMPT (string)
"""
OUTPUT_FORMAT_PROMPT = """
OUTPUT INSTRUCTIONS (MANDATORY):
Return ONLY a single valid JSON object (no surrounding code fences, no commentary). Follow this exact schema. If a value is not available, use "unknown" or an empty list.

{
  "name": "string",
  "summary": "string (1-3 sentences)",
  "market": {
    "size_estimate": "string (e.g., '> $100M' or 'unknown')",
    "top_markets": ["string"],
    "competitors": ["string"]
  },
  "product": {
    "category": "string",
    "differentiation": "string"
  },
  "business_model": {
    "revenue_streams": ["string"],
    "monetization_risks": ["string"]
  },
  "team": {
    "founders_count": "int or 'unknown'",
    "strengths": ["string"],
    "gaps": ["string"]
  },
  "risks": ["string"],
  "recommendation": {
    "invest": "yes/no/hold",
    "rationale": "string"
  },
  "assumptions": ["string"]
}

STRICT: No extra fields. No surrounding text. The JSON must parse. If partial, include filled fields and set unknowns explicitly.
"""