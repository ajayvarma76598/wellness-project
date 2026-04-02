from pydantic import BaseModel, Field
from uuid import UUID

class UserRequest(BaseModel):
    user_input: str = Field(..., min_length=20, json_schema_extra={"example": "I'm stuck in back-to-back meetings and feeling very overwhelmed."})

class AnalyseResponse(BaseModel):
    emotion: str = Field(...)
    
class FeedbackRequest(BaseModel):
    activity_id: UUID
    rating: int = Field(..., ge=1, le=5, json_schema_extra={"example": 4})
    effective: bool = Field(..., json_schema_extra={"example": True})
    comment: str = Field(..., json_schema_extra={"example": "The breathing exercise helped me relax."})