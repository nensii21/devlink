from typing import List, Optional
from pydantic import BaseModel, Field

class OnboardingRequest(BaseModel):
    project_id: str
    user_skills: List[str] = Field(default_factory=list)
    experience_level: str = Field(default="beginner", description="beginner, intermediate, advanced")

class BeginnerIssue(BaseModel):
    title: str
    issue_url: str
    labels: List[str] = Field(default_factory=list)

class OnboardingResponse(BaseModel):
    project_overview: str
    project_structure: List[str] = Field(default_factory=list)
    beginner_issues: List[BeginnerIssue] = Field(default_factory=list)
    relevant_docs: List[str] = Field(default_factory=list)
    coding_standards: List[str] = Field(default_factory=list)
    