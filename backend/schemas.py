from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class CharacterCreate(BaseModel):
    name: str

class CharacterResponse(BaseModel):
    id: int
    name: str
    level: int
    total_study_time: float
    experience: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class StudySessionCreate(BaseModel):
    character_id: int
    duration: float
    subject: Optional[str] = None

class StudySessionResponse(BaseModel):
    id: int
    character_id: int
    duration: float
    subject: Optional[str]
    started_at: datetime
    ended_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class TimerStart(BaseModel):
    character_id: int
    subject: Optional[str] = None

class TimerStop(BaseModel):
    session_id: int
