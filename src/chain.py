import json
import time
from typing import Tuple, Any, Dict, Optional

from .prompts.role import ROLE_PROMPT
from .prompts.behavior import BEHAVIOR_PROMPT
from .prompts.style import STYLE_PROMPT
from .prompts.output_format import OUTPUT_FORMAT_PROMPT

from .utils import validate_output
from .models import LLMClient
from .memory import ShortTermMemory

# Config

MAX_RETRIES = 3
TEMPERATURE = 0.2

class ChainError(Exception):
    pass

class DeterministicChain:
    def __init__(self, llm_client: LLMClient, memory: ShortTermMemory, max_retries: int = MAX_RETRIES):
        self.llm = llm_client
        self.memory = memory
        self.max_retries = max_retries
    
    def _build_system_prompt(self, user_input: str) -> str:
        parts = [
            ROLE_PROMPT,
            BEHAVIOR_PROMPT,
            STYLE_PROMPT,
            OUTPUT_FORMAT_PROMPT,
        ]
    
    def _build_user_prompt(self, user_input: str) -> str:
        mem_entries = self.memory.get_recent()
        mem_text = ""
        if mem_entries:
            mem_text = "RECENT_CONVERSATION: \n" + "\n".join(f"- {m}" for m in mem_entries) + "\n\n"

        user_block = f"USER_INPUT:\n{user_input}\n\nINSTRUCTIONS:\nReturn only the JSON following the schema in the system instructions."
        return mem_text + user_block
    
    def run(self, user_input: str, session_id: Optional[str] = None) -> Tuple[bool, Any]:
        system_prompt = self._build_system_prompt(user_input)
        user_prompt = self._build_user_prompt(user_input)

        prompt_payload = {
            "system": system_prompt,
            "user": user_prompt
        }        

        attempt = 0
        last_raw_output = None
        while attempt < self.max_retries:
            attempt += 1
            try: 
                raw = self.llm.generate(
                    system = system_prompt,
                    user = user_prompt,
                    temperature = TEMPERATURE
                )
            except Exception as e:
                last_raw_output = f"LLM generation error: {str(e)}"
                time.sleep(1)
                continue
            last_raw_output = raw

            # Parse JSON
            try:
                parsed = json.loads(raw)
            except Exception as e:
                if attempt <= self.max_retries:
                    user_prompt = (
                        "Return STRICT JSON matching the schema from system instructions. "
                        "Do not include any explanation or commentary—only the JSON object.\n\n"
                        + user_prompt
                    )

                    # sleep before retrying
                    time.sleep(0.2*attempt)
                    continue
                else:
                    return False, f"JSON parsing error after {attempt} attempts: {str(e)}. Last output: {last_raw_output}"
                
            ok, model_or_err = validate_output(parsed)
            if ok:
                summary = parsed.get("summary", "")if isinstance(parsed.get("summary", ""), str) else ""
                if session_id:
                    self.memory.add(session_id, f"USER: {user_input}")
                    self.memory.add(session_id, f"ASSISTANT_SUMMARY: {summary}")
                return True, model_or_err
            else:
                if attempt <= self.max_retries:
                    user_prompt = (
                        "Return STRICT JSON matching the schema from system instructions. "
                        "Do not include any explanation or commentary—only the JSON object.\n\n"
                        + user_prompt
                    )

                    # sleep before retrying
                    time.sleep(0.2*attempt)
                    continue
                else:
                    return False, f"Validation error after {attempt} attempts: {str(model_or_err)}. Last output: {last_raw_output}"
    
        return False, f"Exceeded maximum retries ({self.max_retries}). Last output: {last_raw_output}"