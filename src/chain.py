import json
import time
from typing import Tuple, Any, Dict, Optional

from .prompts.role import ROLE_PROMPT
from .prompts.behavior import BEHAVIOR_PROMPT
from .prompts.style import STYLE_PROMPT
from .prompts.output_format import OUTPUT_FORMAT_PROMPT

from .utils import validate_output
from .models import LLMClient  # abstract client you should implement / wire
from .memory import ShortTermMemory  # simple session memory (last N turns)

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
        """
        Assemble the role, behavior, style, and output-format prompts in a deterministic order.
        """
        parts = [
            "SYSTEM: Begin system instructions.",
            ROLE_PROMPT.strip(),
            BEHAVIOR_PROMPT.strip(),
            STYLE_PROMPT.strip(),
            OUTPUT_FORMAT_PROMPT.strip(),
            "SYSTEM: End system instructions."
        ]
        return "\n\n".join(parts)

    def _build_user_prompt(self, user_input: str) -> str:
        """
        Build the user + memory context prompt to send to the LLM.
        Memory should be short and recent (handled by ShortTermMemory).
        """
        mem_entries = self.memory.get_recent()
        mem_text = ""
        if mem_entries:
            # format memory as short bullet list
            mem_text = "RECENT_CONVERSATION:\n" + "\n".join(f"- {m}" for m in mem_entries) + "\n\n"

        user_block = f"USER_INPUT:\n{user_input}\n\nINSTRUCTIONS:\nReturn only the JSON following the schema in the system instructions."
        return mem_text + user_block

    def run(self, user_input: str, session_id: Optional[str] = None) -> Tuple[bool, Any]:
        """
        Execute the chain: assemble prompts, call the LLM, validate output, retry if necessary.
        Returns (True, parsed_model) on success, or (False, error_info) on failure.
        """
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(user_input)

        # Prepare the complete payload for the LLM client
        prompt_payload = {
            "system": system_prompt,
            "user": user_prompt
        }

        # Call LLM with retries
        attempt = 0
        last_raw_output = None
        while attempt <= self.max_retries:
            attempt += 1
            try:
                # deterministic settings
                raw = self.llm.generate(
                    system=system_prompt,
                    user=user_prompt,
                    temperature=TEMPERATURE
                )
            except Exception as e:
                # LLM call failed; if unrecoverable, break and return error
                return False, {"error": "llm_call_failed", "detail": str(e), "attempt": attempt}

            last_raw_output = raw

            # Try to parse raw output as JSON
            try:
                parsed = json.loads(raw)
            except Exception as e:
                # If not JSON, prepare a stricter instruction and retry
                if attempt <= self.max_retries:
                    user_prompt = (
                        "Return STRICT JSON matching the schema from system instructions. "
                        "Do not include any explanation or commentary—only the JSON object.\n\n"
                        + user_prompt
                    )
                    # small backoff to avoid rate limits
                    time.sleep(0.2 * attempt)
                    continue
                else:
                    return False, {"error": "invalid_json", "raw": raw, "detail": str(e)}

            # Validate parsed JSON against pydantic schema
            ok, model_or_err = validate_output(parsed)
            if ok:
                # success — update memory and return
                # store a short summary in memory
                summary = parsed.get("summary", "") if isinstance(parsed, dict) else ""
                if session_id:
                    # memory key could be session-specific inside ShortTermMemory impl
                    self.memory.add(session_id, f"USER: {user_input}")
                    self.memory.add(session_id, f"ASSISTANT_SUMMARY: {summary}")
                return True, model_or_err
            else:
                # validation failed; on retry, ask LLM to return STRICT JSON
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

        # Should not get here
        return False, {"error": "unknown", "raw": last_raw_output}