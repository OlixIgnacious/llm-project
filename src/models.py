from typing import Optional
import logging

logger = logging.getLogger(__name__)

class LLMClient:
    """
    Abstract LLM client. Implement `generate` for your provider (OpenAI, local LLM, etc).
    """
    def generate(self, system: str, user: str, temperature: float = 0.1) -> str:
        raise NotImplementedError("Implement in subclass")


class MockClient(LLMClient):
    """
    Deterministic mock for tests: returns a supplied JSON string or raises.
    Use MockClient(response_text) for predictable testing.
    """
    def __init__(self, response_text: str):
        self.response_text = response_text
        logger.debug("MockClient initialized")

    def generate(self, system: str, user: str, temperature: float = 0.1) -> str:
        logger.info("MockClient.generate called (temp=%s)", temperature)
        logger.debug("System prompt len=%d, user prompt len=%d", len(system or ""), len(user or ""))
        return self.response_text