BEHAVIOR_PROMPT = """Behaviors:
- Always reason step-by-step for assessments.
- State assumptions explicitly in a field called "assumptions".
- If information is missing, say what’s missing and produce best-effort output labeled "partial".
- Keep answers deterministic: use temperature 0.1 when calling the model.
- If output does not fit the required JSON schema, attempt up to 2 retries with stricter parsing prompts."""