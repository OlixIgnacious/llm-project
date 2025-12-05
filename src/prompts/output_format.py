OUTPUT_FORMAT_PROMPT = """
OUTPUT INSTRUCTION (MANDATORY):
Return ONLY a single valid JSON object (no surrounding code fences, no commentary).
Follow this exact schema (types shown). If a value is not available, use "unknown" or empty list.

{
  "name": "string",
  "summary": "string (1-3 sentences)",
  "market": {
    "size_estimate": "string (qual or numeric like '>$100M' or 'unknown')",
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

Important: return valid JSON that will parse into the above structure. No extra fields.
"""