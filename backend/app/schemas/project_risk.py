from typing import List, Optional
from pydantic import BaseModel, Field

class ProjectRiskInput(BaseModel):
    title: str = Field(..., min_length=3)
    description: str = Field(..., min_length=10)
    timeline_days: Optional[int] = Field(default=None, ge=1)
    required_roles: Optional[List[str]] = Field(default_factory=list)
    scope: Optional[str] = Field(default=None)

class RiskItem(BaseModel):
    category: str = Field(..., description="e.g., Timeline, Roles, Requirements, Scope")
    severity: str = Field(..., description="Low, Medium, High, or Critical")
    message: str = Field(..., description="Description of the risk")
    suggestion: str = Field(..., description="Suggested improvement")

class ProjectRiskReport(BaseModel):
    is_publishable: bool
    risk_score: float = Field(..., description="Scale from 0 to 100")
    risks: List[RiskItem] = []
    