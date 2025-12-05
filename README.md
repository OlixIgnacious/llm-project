# llm-project — Week 6 Day 1

Identity: Startup Analyst AI

Problem: Build a modular LLM assistant that converts short startup descriptions into validated, structured JSON assessments for investors.

Prompt strategy: prompts separated into role, behavior, style, and output_format to enforce identity, deterministic behavior, writing style, and strict JSON output. Output schema is validated via pydantic/jsonschema in Day 2.