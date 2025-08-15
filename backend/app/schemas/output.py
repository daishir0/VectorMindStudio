from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Any

class OutputDetailResponse(BaseModel):
    id: str
    template_id: str
    user_id: str
    name: str
    input_variables: Dict[str, Any]
    generated_content: str
    ai_model: str
    generation_time: int
    created_at: datetime

    class Config:
        from_attributes = True
