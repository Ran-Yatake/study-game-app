from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

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

# 資格関連スキーマ
class CertificationCreate(BaseModel):
    character_id: int
    name: str
    category: Optional[str] = None
    itss_level: int = 1
    obtained_date: Optional[str] = None  # 文字列として受け取る
    description: Optional[str] = None

class CertificationUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    itss_level: Optional[int] = None
    obtained_date: Optional[str] = None  # 文字列として受け取る
    description: Optional[str] = None

class CertificationResponse(BaseModel):
    id: int
    character_id: int
    name: str
    category: Optional[str]
    itss_level: int
    obtained_date: Optional[datetime]
    description: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

# 更新されたキャラクターレスポンス（資格情報を含む）
class CharacterWithCertifications(BaseModel):
    id: int
    name: str
    level: int
    total_study_time: float
    experience: int
    created_at: datetime
    certifications: List[CertificationResponse]
    
    class Config:
        from_attributes = True
