#!/usr/bin/env python3
"""
装備マスターデータを初期化するスクリプト
"""

from sqlalchemy.orm import sessionmaker
from database import engine, Equipment
from game_logic import get_available_equipment

def init_equipment_data():
    """装備マスターデータをデータベースに登録"""
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # 既存の装備データを確認
        existing_count = db.query(Equipment).count()
        if existing_count > 0:
            print(f"装備データが既に {existing_count} 件存在します。")
            response = input("既存データを削除して再初期化しますか？ (y/N): ")
            if response.lower() == 'y':
                db.query(Equipment).delete()
                db.commit()
                print("既存データを削除しました。")
            else:
                print("初期化をキャンセルしました。")
                return
        
        # 装備データを取得して登録
        equipment_data = get_available_equipment()
        
        # アクセサリー装備を登録
        for item in equipment_data["accessories"]:
            equipment = Equipment(
                id=item["id"],
                name=item["name"],
                category="accessory",
                price=item["price"],
                description=item["description"]
            )
            db.add(equipment)
        
        # 色装備を登録
        for item in equipment_data["colors"]:
            equipment = Equipment(
                id=item["id"],
                name=item["name"],
                category="color",
                price=item["price"],
                description=f"{item['name']}のカラーリング",
                color_code=item["color"]
            )
            db.add(equipment)
        
        db.commit()
        print(f"装備データの初期化が完了しました。")
        print(f"アクセサリー: {len(equipment_data['accessories'])} 件")
        print(f"カラー: {len(equipment_data['colors'])} 件")
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_equipment_data()
