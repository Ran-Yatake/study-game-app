from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List
from contextlib import asynccontextmanager

from database import get_db, create_tables, Character, StudySession
from schemas import CharacterCreate, CharacterResponse, StudySessionCreate, StudySessionResponse, TimerStart, TimerStop
from game_logic import calculate_experience, calculate_level, get_character_appearance, get_next_level_exp

# アクティブなタイマーセッションを管理
active_sessions = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    create_tables()
    yield
    # Shutdown
    pass

app = FastAPI(title="Study Game API", lifespan=lifespan)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# キャラクター関連API
@app.post("/characters", response_model=CharacterResponse)
def create_character(character: CharacterCreate, db: Session = Depends(get_db)):
    db_character = Character(name=character.name)
    db.add(db_character)
    db.commit()
    db.refresh(db_character)
    return db_character

@app.get("/characters", response_model=List[CharacterResponse])
def get_characters(db: Session = Depends(get_db)):
    return db.query(Character).all()

@app.get("/characters/{character_id}", response_model=CharacterResponse)
def get_character(character_id: int, db: Session = Depends(get_db)):
    character = db.query(Character).filter(Character.id == character_id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    return character

@app.get("/characters/{character_id}/appearance")
def get_character_appearance_api(character_id: int, db: Session = Depends(get_db)):
    character = db.query(Character).filter(Character.id == character_id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    appearance = get_character_appearance(character.level)
    next_level_exp = get_next_level_exp(character.level)
    
    return {
        "character": character,
        "appearance": appearance,
        "next_level_exp": next_level_exp,
        "exp_to_next_level": next_level_exp - character.experience
    }

# タイマー関連API
@app.post("/timer/start")
def start_timer(timer_data: TimerStart, db: Session = Depends(get_db)):
    # キャラクターが存在するかチェック
    character = db.query(Character).filter(Character.id == timer_data.character_id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    # 新しい学習セッションを作成
    session = StudySession(
        character_id=timer_data.character_id,
        duration=0.0,
        subject=timer_data.subject,
        started_at=datetime.utcnow()
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    
    # アクティブセッションに追加
    active_sessions[session.id] = {
        "start_time": datetime.utcnow(),
        "character_id": timer_data.character_id
    }
    
    return {"session_id": session.id, "message": "Timer started"}

@app.post("/timer/stop")
def stop_timer(timer_data: TimerStop, db: Session = Depends(get_db)):
    session_id = timer_data.session_id
    
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Active session not found")
    
    # 経過時間を計算
    start_time = active_sessions[session_id]["start_time"]
    end_time = datetime.utcnow()
    duration_minutes = (end_time - start_time).total_seconds() / 60
    
    # セッションを更新
    session = db.query(StudySession).filter(StudySession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session.duration = duration_minutes
    session.ended_at = end_time
    
    # キャラクターのレベルアップ処理
    character = db.query(Character).filter(Character.id == session.character_id).first()
    old_level = character.level
    
    character.total_study_time += duration_minutes
    additional_exp = calculate_experience(duration_minutes)
    character.experience += additional_exp
    character.level = calculate_level(character.experience)
    
    db.commit()
    
    # アクティブセッションから削除
    del active_sessions[session_id]
    
    level_up = character.level > old_level
    
    return {
        "duration_minutes": duration_minutes,
        "experience_gained": additional_exp,
        "level_up": level_up,
        "new_level": character.level,
        "total_experience": character.experience
    }

# 学習セッション関連API
@app.get("/sessions/{character_id}", response_model=List[StudySessionResponse])
def get_character_sessions(character_id: int, db: Session = Depends(get_db)):
    return db.query(StudySession).filter(
        StudySession.character_id == character_id,
        StudySession.ended_at.isnot(None)
    ).order_by(StudySession.started_at.desc()).all()

@app.get("/stats/{character_id}")
def get_character_stats(character_id: int, db: Session = Depends(get_db)):
    character = db.query(Character).filter(Character.id == character_id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    # 今日の学習時間
    today = datetime.now().date()
    today_sessions = db.query(StudySession).filter(
        StudySession.character_id == character_id,
        StudySession.started_at >= datetime.combine(today, datetime.min.time()),
        StudySession.ended_at.isnot(None)
    ).all()
    
    today_study_time = sum(session.duration for session in today_sessions)
    
    # 今週の学習時間
    week_start = today - timedelta(days=today.weekday())
    week_sessions = db.query(StudySession).filter(
        StudySession.character_id == character_id,
        StudySession.started_at >= datetime.combine(week_start, datetime.min.time()),
        StudySession.ended_at.isnot(None)
    ).all()
    
    week_study_time = sum(session.duration for session in week_sessions)
    
    return {
        "character": character,
        "today_study_time": today_study_time,
        "week_study_time": week_study_time,
        "total_sessions": len(db.query(StudySession).filter(
            StudySession.character_id == character_id,
            StudySession.ended_at.isnot(None)
        ).all())
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
