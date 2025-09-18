from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List
from contextlib import asynccontextmanager

from database import get_db, create_tables, Character, StudySession, Certification, Equipment, CharacterEquipment, CoinTransaction, ExamSchedule
from schemas import (
    CharacterCreate, CharacterResponse, StudySessionCreate, StudySessionResponse, 
    TimerStart, TimerStop, CertificationCreate, CertificationUpdate, CertificationResponse,
    CharacterWithCertifications, EquipmentResponse, CharacterEquipmentResponse,
    EquipmentPurchase, EquipmentEquip, CoinTransactionResponse,
    ExamScheduleCreate, ExamScheduleUpdate, ExamScheduleResponse
)
from game_logic import calculate_experience, calculate_level, get_character_appearance, get_next_level_exp, calculate_coins, get_available_equipment, calculate_equipment_bonus

# アクティブなタイマーセッションを管理しています。
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
    
    # 装備中のアイテムを取得
    equipped_items = db.query(CharacterEquipment).filter(
        CharacterEquipment.character_id == character_id,
        CharacterEquipment.is_equipped == 1
    ).all()
    
    # 基本の外見を取得
    base_appearance = get_character_appearance(character.level)
    
    # 装備による外見の更新
    equipped_accessories = []
    current_color = character.current_color
    
    for item in equipped_items:
        equipment = db.query(Equipment).filter(Equipment.id == item.equipment_id).first()
        if equipment:
            if equipment.category == "accessory":
                equipped_accessories.append(equipment.id)
            elif equipment.category == "color":
                current_color = equipment.color_code
    
    # 装備ボーナス情報を取得
    equipment_list = [item.equipment_id for item in equipped_items]
    bonus = calculate_equipment_bonus(equipment_list)
    
    appearance = {
        "color": current_color,
        "size": base_appearance["size"],
        "accessories": equipped_accessories,
        "level_accessories": base_appearance["accessories"]  # レベルによる基本アクセサリー
    }
    
    next_level_exp = get_next_level_exp(character.level)
    
    return {
        "character": character,
        "appearance": appearance,
        "next_level_exp": next_level_exp,
        "exp_to_next_level": next_level_exp - character.experience,
        "equipment_bonus": bonus
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
    
    # キャラクターの装備ボーナスを取得
    character = db.query(Character).filter(Character.id == session.character_id).first()
    equipped_items = db.query(CharacterEquipment).filter(
        CharacterEquipment.character_id == character.id,
        CharacterEquipment.is_equipped == 1
    ).all()
    
    equipment_list = [item.equipment_id for item in equipped_items]
    bonus = calculate_equipment_bonus(equipment_list)
    
    old_level = character.level
    
    # 基本経験値とコイン計算
    base_experience = calculate_experience(duration_minutes)
    base_coins = calculate_coins(duration_minutes)
    
    # ボーナス適用
    final_experience = int(base_experience * bonus["experience_multiplier"])
    final_coins = int(base_coins * bonus["coin_multiplier"])
    
    # キャラクター更新
    character.total_study_time += duration_minutes
    character.experience += final_experience
    character.coins += final_coins
    character.level = calculate_level(character.experience)
    
    # コイン取得履歴を記録
    coin_transaction = CoinTransaction(
        character_id=character.id,
        amount=final_coins,
        transaction_type="earned",
        source="study",
        study_session_id=session.id
    )
    db.add(coin_transaction)
    
    db.commit()
    
    # アクティブセッションから削除
    del active_sessions[session_id]
    
    level_up = character.level > old_level
    
    return {
        "duration_minutes": duration_minutes,
        "experience_gained": final_experience,
        "coins_gained": final_coins,
        "level_up": level_up,
        "new_level": character.level,
        "total_experience": character.experience,
        "total_coins": character.coins,
        "equipment_bonus": bonus
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

# 装備関連API
@app.get("/equipment", response_model=List[EquipmentResponse])
def get_all_equipment(db: Session = Depends(get_db)):
    """すべての装備アイテムを取得"""
    return db.query(Equipment).all()

@app.get("/equipment/shop/{character_id}")
def get_equipment_shop(character_id: int, db: Session = Depends(get_db)):
    """キャラクター用の装備ショップ情報を取得"""
    character = db.query(Character).filter(Character.id == character_id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    # すべての装備アイテム
    all_equipment = db.query(Equipment).all()
    
    # キャラクターが所持している装備
    owned_equipment = db.query(CharacterEquipment).filter(
        CharacterEquipment.character_id == character_id
    ).all()
    
    owned_ids = {item.equipment_id for item in owned_equipment}
    equipped_ids = {item.equipment_id for item in owned_equipment if item.is_equipped == 1}
    
    # 装備情報を整形
    shop_items = []
    for equipment in all_equipment:
        shop_items.append({
            "id": equipment.id,
            "name": equipment.name,
            "category": equipment.category,
            "price": equipment.price,
            "description": equipment.description,
            "color_code": equipment.color_code,
            "owned": equipment.id in owned_ids,
            "equipped": equipment.id in equipped_ids
        })
    
    return {
        "character_coins": character.coins,
        "equipment": shop_items
    }

@app.post("/equipment/purchase")
def purchase_equipment(purchase: EquipmentPurchase, db: Session = Depends(get_db)):
    """装備を購入"""
    character = db.query(Character).filter(Character.id == purchase.character_id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    equipment = db.query(Equipment).filter(Equipment.id == purchase.equipment_id).first()
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    
    # 既に所持しているかチェック
    existing = db.query(CharacterEquipment).filter(
        CharacterEquipment.character_id == purchase.character_id,
        CharacterEquipment.equipment_id == purchase.equipment_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Already owned this equipment")
    
    # コイン不足チェック
    if character.coins < equipment.price:
        raise HTTPException(status_code=400, detail="Insufficient coins")
    
    # コイン消費
    character.coins -= equipment.price
    
    # 装備を追加
    character_equipment = CharacterEquipment(
        character_id=purchase.character_id,
        equipment_id=purchase.equipment_id,
        is_equipped=0
    )
    db.add(character_equipment)
    
    # コイン消費履歴を記録
    coin_transaction = CoinTransaction(
        character_id=character.id,
        amount=-equipment.price,
        transaction_type="spent",
        source="equipment_purchase",
        equipment_id=equipment.id
    )
    db.add(coin_transaction)
    
    db.commit()
    
    return {
        "message": f"{equipment.name}を購入しました",
        "remaining_coins": character.coins
    }

@app.post("/equipment/equip")
def equip_unequip_item(equip_data: EquipmentEquip, db: Session = Depends(get_db)):
    """装備の着脱"""
    character = db.query(Character).filter(Character.id == equip_data.character_id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    character_equipment = db.query(CharacterEquipment).filter(
        CharacterEquipment.character_id == equip_data.character_id,
        CharacterEquipment.equipment_id == equip_data.equipment_id
    ).first()
    
    if not character_equipment:
        raise HTTPException(status_code=404, detail="Equipment not owned")
    
    equipment = db.query(Equipment).filter(Equipment.id == equip_data.equipment_id).first()
    
    if equip_data.equip:
        # 装備する
        # カラー装備の場合は、他のカラーを外す
        if equipment.category == "color":
            db.query(CharacterEquipment).filter(
                CharacterEquipment.character_id == equip_data.character_id,
                CharacterEquipment.equipment_item.has(category="color")
            ).update({"is_equipped": 0})
            
            # キャラクターの現在の色を更新
            character.current_color = equipment.color_code
        
        character_equipment.is_equipped = 1
        message = f"{equipment.name}を装備しました"
    else:
        # 装備を外す
        character_equipment.is_equipped = 0
        
        # カラー装備の場合は、デフォルト色に戻す
        if equipment.category == "color":
            character.current_color = "#8B4513"  # デフォルト色
        
        message = f"{equipment.name}の装備を外しました"
    
    db.commit()
    
    return {"message": message}

@app.get("/equipment/{character_id}", response_model=List[CharacterEquipmentResponse])
def get_character_equipment(character_id: int, db: Session = Depends(get_db)):
    """キャラクターの所持装備を取得"""
    character = db.query(Character).filter(Character.id == character_id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    return db.query(CharacterEquipment).filter(
        CharacterEquipment.character_id == character_id
    ).all()

@app.get("/coins/{character_id}/transactions", response_model=List[CoinTransactionResponse])
def get_coin_transactions(character_id: int, db: Session = Depends(get_db)):
    """キャラクターのコイン取引履歴を取得"""
    character = db.query(Character).filter(Character.id == character_id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    return db.query(CoinTransaction).filter(
        CoinTransaction.character_id == character_id
    ).order_by(CoinTransaction.created_at.desc()).all()

# 試験予定関連API
@app.post("/exam-schedules", response_model=ExamScheduleResponse)
def create_exam_schedule(exam_schedule: ExamScheduleCreate, db: Session = Depends(get_db)):
    """試験予定を作成"""
    try:
        # キャラクターが存在するかチェック
        character = db.query(Character).filter(Character.id == exam_schedule.character_id).first()
        if not character:
            raise HTTPException(status_code=404, detail="Character not found")
        
        # 日付文字列をdatetimeオブジェクトに変換
        try:
            exam_date_obj = datetime.fromisoformat(exam_schedule.exam_date.replace('Z', '+00:00'))
        except ValueError:
            try:
                exam_date_obj = datetime.strptime(exam_schedule.exam_date, '%Y-%m-%d')
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD or ISO format")
        
        db_exam_schedule = ExamSchedule(
            character_id=exam_schedule.character_id,
            exam_name=exam_schedule.exam_name,
            exam_date=exam_date_obj,
            category=exam_schedule.category,
            description=exam_schedule.description,
            reminder_days=exam_schedule.reminder_days
        )
        
        db.add(db_exam_schedule)
        db.commit()
        db.refresh(db_exam_schedule)
        return db_exam_schedule
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating exam schedule: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/exam-schedules/{character_id}", response_model=List[ExamScheduleResponse])
def get_character_exam_schedules(character_id: int, db: Session = Depends(get_db)):
    """キャラクターの試験予定一覧を取得"""
    character = db.query(Character).filter(Character.id == character_id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    return db.query(ExamSchedule).filter(
        ExamSchedule.character_id == character_id
    ).order_by(ExamSchedule.exam_date.asc()).all()

@app.get("/exam-schedules/calendar/{character_id}")
def get_exam_calendar(character_id: int, year: int, month: int, db: Session = Depends(get_db)):
    """指定した年月のカレンダー形式で試験予定を取得"""
    character = db.query(Character).filter(Character.id == character_id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    # 指定月の開始日と終了日
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)
    
    # 該当月の試験予定を取得
    exams = db.query(ExamSchedule).filter(
        ExamSchedule.character_id == character_id,
        ExamSchedule.exam_date >= start_date,
        ExamSchedule.exam_date < end_date
    ).order_by(ExamSchedule.exam_date.asc()).all()
    
    # 日付ごとにグループ化
    calendar_data = {}
    for exam in exams:
        date_key = exam.exam_date.strftime('%Y-%m-%d')
        if date_key not in calendar_data:
            calendar_data[date_key] = []
        calendar_data[date_key].append({
            "id": exam.id,
            "exam_name": exam.exam_name,
            "category": exam.category,
            "status": exam.status
        })
    
    return {
        "year": year,
        "month": month,
        "exams": calendar_data
    }

@app.put("/exam-schedules/{exam_id}", response_model=ExamScheduleResponse)
def update_exam_schedule(exam_id: int, exam_update: ExamScheduleUpdate, db: Session = Depends(get_db)):
    """試験予定を更新"""
    try:
        exam_schedule = db.query(ExamSchedule).filter(ExamSchedule.id == exam_id).first()
        if not exam_schedule:
            raise HTTPException(status_code=404, detail="Exam schedule not found")
        
        update_data = exam_update.dict(exclude_unset=True)
        
        # 日付文字列の変換
        if 'exam_date' in update_data and update_data['exam_date']:
            try:
                update_data['exam_date'] = datetime.fromisoformat(update_data['exam_date'].replace('Z', '+00:00'))
            except ValueError:
                try:
                    update_data['exam_date'] = datetime.strptime(update_data['exam_date'], '%Y-%m-%d')
                except ValueError:
                    raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD or ISO format")
        
        # 更新日時を設定
        update_data['updated_at'] = datetime.utcnow()
        
        for field, value in update_data.items():
            setattr(exam_schedule, field, value)
        
        db.commit()
        db.refresh(exam_schedule)
        return exam_schedule
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating exam schedule: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.delete("/exam-schedules/{exam_id}")
def delete_exam_schedule(exam_id: int, db: Session = Depends(get_db)):
    """試験予定を削除"""
    exam_schedule = db.query(ExamSchedule).filter(ExamSchedule.id == exam_id).first()
    if not exam_schedule:
        raise HTTPException(status_code=404, detail="Exam schedule not found")
    
    db.delete(exam_schedule)
    db.commit()
    return {"message": "Exam schedule deleted successfully"}

@app.get("/exam-schedules/upcoming/{character_id}")
def get_upcoming_exams(character_id: int, days: int = 30, db: Session = Depends(get_db)):
    """近日中の試験予定を取得（リマインダー用）"""
    character = db.query(Character).filter(Character.id == character_id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    # 今日から指定日数後までの範囲
    today = datetime.now().date()
    end_date = today + timedelta(days=days)
    
    upcoming_exams = db.query(ExamSchedule).filter(
        ExamSchedule.character_id == character_id,
        ExamSchedule.exam_date >= datetime.combine(today, datetime.min.time()),
        ExamSchedule.exam_date <= datetime.combine(end_date, datetime.max.time()),
        ExamSchedule.status == "scheduled"
    ).order_by(ExamSchedule.exam_date.asc()).all()
    
    return upcoming_exams

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
