from typing import List, Optional
from pydantic import BaseModel, Field

class ReadmeGenerationRequest(BaseModel):
    project_title: str = Field(..., min_length=2)
    tagline: str = Field(..., min_length=5)
    features: List[str] = Field(default_factory=list)
    tech_stack: List[str] = Field(default_factory=list)
    installation_steps: Optional[str] = Field(default=None)
    license_type: str = Field(default="MIT")

class ReadmeGenerationResponse(BaseModel):
    markdown_content: str = Field(..., description="The fully formatted professional markdown README")
    sections_included: List[str] = Field(default_factory=list)
    