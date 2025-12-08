from typing import Optional

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

    def generate(self, system: str, user: str, temperature: float = 0.1) -> str:
        return self.response_text