Required output: JSON object with keys:
- name: string (startup name or "unknown")
- summary: string (1-3 sentences)
- market: {size_estimate: string, top_markets: [strings], competitors: [strings]}
- product: {category: string, differentiation: string}
- business_model: {revenue_streams: [strings], monetization_risks: [strings]}
- team: {founders_count: int or "unknown", strengths: [strings], gaps: [strings]}
- risks: [strings]
- recommendation: {invest: yes/no/hold, rationale: string}
- assumptions: [strings]

Return ONLY valid JSON. No commentary outside JSON. If incomplete, set fields to "unknown" or empty arrays as appropriate.