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
    coins: int
    current_color: str
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
    coins: int
    current_color: str
    created_at: datetime
    certifications: List[CertificationResponse]
    
    class Config:
        from_attributes = True

# 装備関連スキーマ
class EquipmentResponse(BaseModel):
    id: str
    name: str
    category: str
    price: int
    description: Optional[str]
    color_code: Optional[str]
    
    class Config:
        from_attributes = True

class CharacterEquipmentResponse(BaseModel):
    id: int
    character_id: int
    equipment_id: str
    is_equipped: int
    purchased_at: datetime
    equipment_item: EquipmentResponse
    
    class Config:
        from_attributes = True

class EquipmentPurchase(BaseModel):
    character_id: int
    equipment_id: str

class EquipmentEquip(BaseModel):
    character_id: int
    equipment_id: str
    equip: bool  # True: 装備, False: 装備解除

class CoinTransactionResponse(BaseModel):
    id: int
    character_id: int
    amount: int
    transaction_type: str
    source: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

# 試験予定関連スキーマ
class ExamScheduleCreate(BaseModel):
    character_id: int
    exam_name: str
    exam_date: str  # ISO形式の文字列として受け取る
    category: Optional[str] = None
    description: Optional[str] = None
    reminder_days: int = 7

class ExamScheduleUpdate(BaseModel):
    exam_name: Optional[str] = None
    exam_date: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    reminder_days: Optional[int] = None

class ExamScheduleResponse(BaseModel):
    id: int
    character_id: int
    exam_name: str
    exam_date: datetime
    category: Optional[str]
    description: Optional[str]
    status: str
    reminder_days: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
