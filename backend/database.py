from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# データベース接続設定（SQLiteを使用）
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./study_game.db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# 学習セッションモデル
class StudySession(Base):
    __tablename__ = "study_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    character_id = Column(Integer, nullable=False)
    duration = Column(Float, nullable=False)  # 学習時間（分）
    subject = Column(String(200))
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime)

# 資格モデル
class Certification(Base):
    __tablename__ = "certifications"
    
    id = Column(Integer, primary_key=True, index=True)
    character_id = Column(Integer, ForeignKey("characters.id"), nullable=False)
    name = Column(String(200), nullable=False)  # 資格名
    category = Column(String(100))  # カテゴリー（IT、語学など）
    itss_level = Column(Integer, default=1)  # ITSSレベル（1-7）
    obtained_date = Column(DateTime)  # 取得日
    description = Column(Text)  # 説明
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # リレーション
    character = relationship("Character", back_populates="certifications")

# キャラクターモデルを更新
class Character(Base):
    __tablename__ = "characters"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    level = Column(Integer, default=1)
    total_study_time = Column(Float, default=0.0)  # 総学習時間（分）
    experience = Column(Integer, default=0)
    coins = Column(Integer, default=0)  # 所持コイン
    current_color = Column(String(20), default="#8B4513")  # 現在の色
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # リレーション
    certifications = relationship("Certification", back_populates="character")
    equipment = relationship("CharacterEquipment", back_populates="character")
    exam_schedules = relationship("ExamSchedule", back_populates="character")

# 装備アイテムマスター
class Equipment(Base):
    __tablename__ = "equipment"
    
    id = Column(String(50), primary_key=True)  # "hat", "glasses"等
    name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)  # "accessory", "color"
    price = Column(Integer, nullable=False)
    description = Column(Text)
    color_code = Column(String(10))  # 色装備の場合のカラーコード
    created_at = Column(DateTime, default=datetime.utcnow)

# キャラクターの装備情報
class CharacterEquipment(Base):
    __tablename__ = "character_equipment"
    
    id = Column(Integer, primary_key=True, index=True)
    character_id = Column(Integer, ForeignKey("characters.id"), nullable=False)
    equipment_id = Column(String(50), ForeignKey("equipment.id"), nullable=False)
    is_equipped = Column(Integer, default=0)  # 0: 未装備, 1: 装備中
    purchased_at = Column(DateTime, default=datetime.utcnow)
    
    # リレーション
    character = relationship("Character", back_populates="equipment")
    equipment_item = relationship("Equipment")

# コイン取得履歴
class CoinTransaction(Base):
    __tablename__ = "coin_transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    character_id = Column(Integer, ForeignKey("characters.id"), nullable=False)
    amount = Column(Integer, nullable=False)  # 取得/消費したコイン数
    transaction_type = Column(String(20), nullable=False)  # "earned", "spent"
    source = Column(String(50))  # "study", "equipment_purchase"等
    study_session_id = Column(Integer, ForeignKey("study_sessions.id"))
    equipment_id = Column(String(50), ForeignKey("equipment.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

# 試験予定モデル
class ExamSchedule(Base):
    __tablename__ = "exam_schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    character_id = Column(Integer, ForeignKey("characters.id"), nullable=False)
    exam_name = Column(String(200), nullable=False)  # 試験名
    exam_date = Column(DateTime, nullable=False)  # 試験日
    category = Column(String(100))  # カテゴリー（IT、語学など）
    description = Column(Text)  # 詳細・メモ
    status = Column(String(20), default="scheduled")  # "scheduled", "completed", "cancelled"
    reminder_days = Column(Integer, default=7)  # 何日前にリマインドするか
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # リレーション
    character = relationship("Character", back_populates="exam_schedules")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    Base.metadata.create_all(bind=engine)
