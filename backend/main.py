from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List
from contextlib import asynccontextmanager

from database import get_db, create_tables, Character, StudySession, Certification
from schemas import (
    CharacterCreate, CharacterResponse, StudySessionCreate, StudySessionResponse, 
    TimerStart, TimerStop, CertificationCreate, CertificationUpdate, CertificationResponse,
    CharacterWithCertifications
)
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

# 資格関連API
@app.post("/certifications", response_model=CertificationResponse)
def create_certification(certification: CertificationCreate, db: Session = Depends(get_db)):
    try:
        # キャラクターが存在するかチェック
        character = db.query(Character).filter(Character.id == certification.character_id).first()
        if not character:
            raise HTTPException(status_code=404, detail="Character not found")
        
        # ITSSレベルの範囲チェック
        if certification.itss_level < 1 or certification.itss_level > 7:
            raise HTTPException(status_code=400, detail="ITSS level must be between 1 and 7")
        
        # 日付文字列をdatetimeオブジェクトに変換
        obtained_date_obj = None
        if certification.obtained_date:
            try:
                obtained_date_obj = datetime.fromisoformat(certification.obtained_date.replace('Z', '+00:00'))
            except ValueError:
                try:
                    obtained_date_obj = datetime.strptime(certification.obtained_date, '%Y-%m-%d')
                except ValueError:
                    raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD or ISO format")
        
        db_certification = Certification(
            character_id=certification.character_id,
            name=certification.name,
            category=certification.category,
            itss_level=certification.itss_level,
            obtained_date=obtained_date_obj,
            description=certification.description
        )
        db.add(db_certification)
        db.commit()
        db.refresh(db_certification)
        return db_certification
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating certification: {e}")
        print(f"Certification data: {certification}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/certifications/{character_id}", response_model=List[CertificationResponse])
def get_character_certifications(character_id: int, db: Session = Depends(get_db)):
    # キャラクターが存在するかチェック
    character = db.query(Character).filter(Character.id == character_id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    return db.query(Certification).filter(Certification.character_id == character_id).order_by(Certification.created_at.desc()).all()

@app.get("/characters/{character_id}/with-certifications", response_model=CharacterWithCertifications)
def get_character_with_certifications(character_id: int, db: Session = Depends(get_db)):
    character = db.query(Character).filter(Character.id == character_id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    return character

@app.put("/certifications/{certification_id}", response_model=CertificationResponse)
def update_certification(certification_id: int, certification_update: CertificationUpdate, db: Session = Depends(get_db)):
    try:
        certification = db.query(Certification).filter(Certification.id == certification_id).first()
        if not certification:
            raise HTTPException(status_code=404, detail="Certification not found")
        
        # 更新フィールドをチェック
        update_data = certification_update.dict(exclude_unset=True)
        
        # ITSSレベルの範囲チェック
        if 'itss_level' in update_data:
            if update_data['itss_level'] < 1 or update_data['itss_level'] > 7:
                raise HTTPException(status_code=400, detail="ITSS level must be between 1 and 7")
        
        # 日付文字列の変換
        if 'obtained_date' in update_data and update_data['obtained_date']:
            try:
                update_data['obtained_date'] = datetime.fromisoformat(update_data['obtained_date'].replace('Z', '+00:00'))
            except ValueError:
                try:
                    update_data['obtained_date'] = datetime.strptime(update_data['obtained_date'], '%Y-%m-%d')
                except ValueError:
                    raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD or ISO format")
        
        for field, value in update_data.items():
            setattr(certification, field, value)
        
        db.commit()
        db.refresh(certification)
        return certification
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating certification: {e}")
        print(f"Certification ID: {certification_id}")
        print(f"Update data: {certification_update}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.delete("/certifications/{certification_id}")
def delete_certification(certification_id: int, db: Session = Depends(get_db)):
    certification = db.query(Certification).filter(Certification.id == certification_id).first()
    if not certification:
        raise HTTPException(status_code=404, detail="Certification not found")
    
    db.delete(certification)
    db.commit()
    return {"message": "Certification deleted successfully"}

@app.get("/certifications/{certification_id}/color")
def get_certification_color(certification_id: int, db: Session = Depends(get_db)):
    certification = db.query(Certification).filter(Certification.id == certification_id).first()
    if not certification:
        raise HTTPException(status_code=404, detail="Certification not found")
    
    # ITSSレベルに基づく色分け
    color_map = {
        1: "#8B4513",  # ブラウン - 基礎レベル
        2: "#CD853F",  # ペルー - 応用レベル
        3: "#32CD32",  # ライムグリーン - 実用レベル
        4: "#00CED1",  # ダークターコイズ - 専門レベル
        5: "#4169E1",  # ロイヤルブルー - 上級レベル
        6: "#9932CC",  # ダークオーキッド - エキスパート
        7: "#FFD700"   # ゴールド - マスター
    }
    
    return {
        "certification_id": certification_id,
        "itss_level": certification.itss_level,
        "color": color_map.get(certification.itss_level, "#808080"),
        "level_name": get_itss_level_name(certification.itss_level)
    }

def get_itss_level_name(level: int) -> str:
    """ITSSレベルに対応する名称を返す"""
    level_names = {
        1: "エントリレベル",
        2: "基礎レベル",
        3: "応用レベル",
        4: "専門レベル",
        5: "上級レベル",
        6: "エキスパートレベル",
        7: "マスターレベル"
    }
    return level_names.get(level, "不明")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
