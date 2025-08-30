from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# データベース接続設定（SQLiteを使用）
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./study_game.db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# キャラクターモデル
class Character(Base):
    __tablename__ = "characters"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    level = Column(Integer, default=1)
    total_study_time = Column(Float, default=0.0)  # 総学習時間（分）
    experience = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

# 学習セッションモデル
class StudySession(Base):
    __tablename__ = "study_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    character_id = Column(Integer, nullable=False)
    duration = Column(Float, nullable=False)  # 学習時間（分）
    subject = Column(String(200))
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    Base.metadata.create_all(bind=engine)
