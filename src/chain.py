# src/chain.py
import json
import time
from typing import Tuple, Any, Optional

from .prompts.role import ROLE_PROMPT
from .prompts.behavior import BEHAVIOR_PROMPT
from .prompts.style import STYLE_PROMPT
from .prompts.output_format import OUTPUT_FORMAT_PROMPT

from .utils import validate_output
from .models import LLMClient
from .memory import ShortTermMemory

# Config
MAX_RETRIES = 2
TEMPERATURE = 0.1

class ChainError(Exception):
    pass

class DeterministicChain:
    def __init__(self, llm_client: LLMClient, memory: ShortTermMemory, max_retries: int = MAX_RETRIES):
        self.llm = llm_client
        self.memory = memory
        self.max_retries = max_retries

    def _build_system_prompt(self) -> str:
        parts = [
            "SYSTEM: Begin system instructions.",
            ROLE_PROMPT.strip(),
            BEHAVIOR_PROMPT.strip(),
            STYLE_PROMPT.strip(),
            OUTPUT_FORMAT_PROMPT.strip(),
            "SYSTEM: End system instructions."
        ]
        return "\n\n".join(parts)

    def _build_user_prompt(self, user_input: str, session_id: Optional[str] = None) -> str:
        mem_text = ""
        if session_id:
            mem_entries = self.memory.get_recent(session_id)
            if mem_entries:
                mem_text = "RECENT_CONVERSATION:\n" + "\n".join(f"- {m}" for m in mem_entries) + "\n\n"

        user_block = (
            f"USER_INPUT:\n{user_input}\n\n"
            "INSTRUCTIONS:\nReturn only the JSON following the schema in the system instructions."
        )
        return mem_text + user_block

    def run(self, user_input: str, session_id: Optional[str] = None) -> Tuple[bool, Any]:
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(user_input, session_id)

        attempt = 0
        last_raw_output = None

        while attempt <= self.max_retries:
            attempt += 1
            try:
                raw = self.llm.generate(
                    system=system_prompt,
                    user=user_prompt,
                    temperature=TEMPERATURE
                )
            except Exception as e:
                last_raw_output = f"LLM generation error: {str(e)}"
                # transient LLM error: backoff and retry (up to max_retries)
                if attempt <= self.max_retries:
                    time.sleep(0.5 * attempt)
                    continue
                return False, {"error": "llm_call_failed", "detail": str(e), "attempt": attempt}

            last_raw_output = raw

            # Try parse JSON
            try:
                parsed = json.loads(raw)
            except Exception as e:
                if attempt <= self.max_retries:
                    user_prompt = (
                        "Return STRICT JSON matching the schema from system instructions. "
                        "Do not include any explanation or commentary—only the JSON object.\n\n"
                        + user_prompt
                    )
                    time.sleep(0.2 * attempt)
                    continue
                else:
                    return False, {"error": "invalid_json", "raw": raw, "detail": str(e)}

            # Validate parsed JSON against pydantic schema
            ok, model_or_err = validate_output(parsed)
            if ok:
                # success — update memory and return parsed model
                summary = parsed.get("summary", "") if isinstance(parsed.get("summary", ""), str) else ""
                if session_id:
                    self.memory.add(session_id, f"USER: {user_input}")
                    self.memory.add(session_id, f"ASSISTANT_SUMMARY: {summary}")
                return True, model_or_err
            else:
                # validation failed; retry with stricter instruction
                if attempt <= self.max_retries:
                    user_prompt = (
                        "Validation failed. Return STRICT JSON matching the schema exactly. "
                        "Do not include any text outside the JSON object.\n\n"
                        + user_prompt
                    )
                    time.sleep(0.2 * attempt)
                    continue
                else:
                    return False, {"error": "validation_failed", "validation": str(model_or_err), "raw": raw}

        return False, {"error": "exceeded_retries", "last_output": last_raw_output}