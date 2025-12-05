from typing import List, Optional, Union
from pydantic import BaseModel, Field, field_validator

class Market(BaseModel):
    size_estimate: str = Field(..., description="Market size estimate (e.g., '> $100M' or 'unknown')")  
    top_markets: List[str] = Field(default_factory=list)
    competitors: List[str] = Field(default_factory=list)

class Product(BaseModel):
    category: str 
    differentiation: str

class BusinessModel(BaseModel):
    revenue_streams: List[str] = Field(default_factory=list)
    monetization_risks: List[str] = Field(default_factory=list)

class Team(BaseModel):
    founders_count: Union[int, str]
    strengths: List[str] = Field(default_factory=list)
    gaps: List[str] = Field(default_factory=list)

class Recommendation(BaseModel):
    invest: str = Field(..., description="Investment recommendation (yes/no/hold)")
    rationale: str

    @field_validator('invest')
    def invest_must_be_valid(cls, v):
        if v not in {'yes', 'no', 'hold'}:
            raise ValueError("invest must be 'yes', 'no', or 'hold'")
        return v
    
class StartupAssessment(BaseModel):
    name: str
    summary: str = Field(..., description="Brief summary (1-3 sentences)")
    market: Market
    product: Product
    business_model: BusinessModel
    team: Team
    risks: List[str] = Field(default_factory=list)
    recommendation: Recommendation
    assumptions: List[str] = Field(default_factory=list)

    @field_validator('summary')
    def summary_length(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("summary cannot be empty")
        return v