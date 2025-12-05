import pytest
from src.utils import validate_output
from pydantic import ValidationError

VALID_EXAMPLE = {
    "name": "Acme Market",
    "summary": "Marketplace connecting SMBs to local suppliers; target: tier-2 cities; revenue: transaction fee.",
    "market": {
        "size_estimate": "> $50M",
        "top_markets": ["India", "SE Asia"],
        "competitors": ["Competitor A"]
    },
    "product": {
        "category": "marketplace",
        "differentiation": "Focus on local logistics and micro-fulfillment."
    },
    "business_model": {
        "revenue_streams": ["transaction fees", "subscription"],
        "monetization_risks": ["low take rate", "merchant churn"]
    },
    "team": {
        "founders_count": 2,
        "strengths": ["domain experience", "strong ops"],
        "gaps": ["no senior sales hire"]
    },
    "risks": ["execution risk", "unit economics"],
    "recommendation": {
        "invest": "hold",
        "rationale": "Early traction but unit economics unproven."
    },
    "assumptions": ["market size estimated from comparable players"]
}

INVALID_EXAMPLE = {
    # Missing 'summary' and 'market' keys and invalid recommendation.invest value
    "name": "Bad Startup",
    "product": {"category": "saas", "differentiation": "unknown"},
    "business_model": {},
    "team": {"founders_count": "unknown"},
    "risks": [],
    "recommendation": {"invest": "maybe", "rationale": "no data"},
    "assumptions": []
}

PARTIAL_EXAMPLE = {
    "name": "Partial Startup",
    "summary": "An MVP with limited data.",
    "market": {
        "size_estimate": "unknown",
        "top_markets": [],
        "competitors": []
    },
    "product": {"category": "saas", "differentiation": "unknown"},
    "business_model": {"revenue_streams": [], "monetization_risks": []},
    "team": {"founders_count": "unknown", "strengths": [], "gaps": []},
    "risks": [],
    "recommendation": {"invest": "no", "rationale": "insufficient data"},
    "assumptions": ["insufficient public info"]
}

def test_valid_example_parses():
    ok, model_or_err = validate_output(VALID_EXAMPLE)
    assert ok is True
    # model_or_err is a pydantic model
    assert model_or_err.name == "Acme Market"

def test_invalid_example_fails():
    ok, model_or_err = validate_output(INVALID_EXAMPLE)
    assert ok is False
    # Ensure ValidationError contains missing keys or invalid values
    assert "summary" in str(model_or_err) or "market" in str(model_or_err) or "invest" in str(model_or_err)

def test_partial_example_parses():
    ok, model_or_err = validate_output(PARTIAL_EXAMPLE)
    assert ok is True
    assert model_or_err.team.founders_count == "unknown"