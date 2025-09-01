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
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # リレーション
    certifications = relationship("Certification", back_populates="character")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    Base.metadata.create_all(bind=engine)
