from pydantic import BaseModel, Field, AliasChoices
from typing import Dict, Any

class ActivityBase(BaseModel):
    meta: Dict[str, Any] = Field(default_factory=dict, validation_alias=AliasChoices("meta", "metadata"), serialization_alias="metadata")

print(ActivityBase(**{"metadata": {"foo": "bar"}}).model_dump(by_alias=True))
