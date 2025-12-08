import json
from src.chain import DeterministicChain
from src.models import MockClient
from src.memory import ShortTermMemory

VALID_JSON_STR = json.dumps({
    "name": "Acme Market",
    "summary": "Marketplace connecting SMBs to local suppliers; target: tier-2 cities; revenue: transaction fee.",
    "market": {
        "size_estimate": "> $50M",
        "top_markets": ["India"],
        "competitors": ["Competitor A"]
    },
    "product": {
        "category": "marketplace",
        "differentiation": "Local logistics focus"
    },
    "business_model": {
        "revenue_streams": ["fees"],
        "monetization_risks": []
    },
    "team": {
        "founders_count": 2,
        "strengths": [],
        "gaps": []
    },
    "risks": [],
    "recommendation": {"invest": "hold", "rationale": "unit economics unclear"},
    "assumptions": []
})

def test_chain_success():
    mock = MockClient(VALID_JSON_STR)
    memory = ShortTermMemory(max_len=4)
    chain = DeterministicChain(mock, memory)
    ok, result = chain.run("Analyze this startup: Acme Market", session_id="test")
    assert ok is True
    # result is a pydantic model
    assert result.name == "Acme Market"
    # memory should have entries
    mem = memory.get_recent("test")
    assert any("USER:" in m or "ASSISTANT_SUMMARY" in m for m in mem)

def test_chain_invalid_json_retries_and_fails():
    # Mock returns non-json first, then valid json on retry
    responses = ["not-json", VALID_JSON_STR]
    class SequenceMock:
        def __init__(self, seq):
            self.seq = seq
            self.i = 0
        def generate(self, system, user, temperature=0.1):
            out = self.seq[min(self.i, len(self.seq)-1)]
            self.i += 1
            return out

    mock = SequenceMock(responses)
    memory = ShortTermMemory()
    chain = DeterministicChain(mock, memory, max_retries=2)
    ok, result = chain.run("Please analyze", session_id="s1")
    assert ok is True
    assert result.name == "Acme Market"