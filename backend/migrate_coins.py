#!/usr/bin/env python3
"""
データベースの既存キャラクターにコインフィールドを追加するマイグレーション
"""

import sqlite3
from datetime import datetime

def migrate_database():
    """既存データベースにコインと色の情報を追加"""
    
    # SQLiteデータベースに接続
    conn = sqlite3.connect('study_game.db')
    cursor = conn.cursor()
    
    try:
        print("データベースマイグレーション開始...")
        
        # キャラクターテーブルに新しいカラムを追加
        print("キャラクターテーブルにcoinsカラムを追加...")
        try:
            cursor.execute('ALTER TABLE characters ADD COLUMN coins INTEGER DEFAULT 0')
            print("coinsカラムを追加しました")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("coinsカラムは既に存在します")
            else:
                raise e
        
        print("キャラクターテーブルにcurrent_colorカラムを追加...")
        try:
            cursor.execute('ALTER TABLE characters ADD COLUMN current_color VARCHAR(20) DEFAULT "#8B4513"')
            print("current_colorカラムを追加しました")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("current_colorカラムは既に存在します")
            else:
                raise e
        
        # 新しいテーブルを作成
        print("装備テーブルを作成...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS equipment (
                id VARCHAR(50) PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                category VARCHAR(50) NOT NULL,
                price INTEGER NOT NULL,
                description TEXT,
                color_code VARCHAR(10),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        print("キャラクター装備テーブルを作成...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS character_equipment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                character_id INTEGER NOT NULL,
                equipment_id VARCHAR(50) NOT NULL,
                is_equipped INTEGER DEFAULT 0,
                purchased_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (character_id) REFERENCES characters (id),
                FOREIGN KEY (equipment_id) REFERENCES equipment (id)
            )
        ''')
        
        print("コイン取引履歴テーブルを作成...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS coin_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                character_id INTEGER NOT NULL,
                amount INTEGER NOT NULL,
                transaction_type VARCHAR(20) NOT NULL,
                source VARCHAR(50),
                study_session_id INTEGER,
                equipment_id VARCHAR(50),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (character_id) REFERENCES characters (id),
                FOREIGN KEY (study_session_id) REFERENCES study_sessions (id),
                FOREIGN KEY (equipment_id) REFERENCES equipment (id)
            )
        ''')
        
        conn.commit()
        print("データベースマイグレーション完了！")
        
        # 既存キャラクターの統計を表示
        cursor.execute('SELECT COUNT(*) FROM characters')
        char_count = cursor.fetchone()[0]
        print(f"既存キャラクター数: {char_count}")
        
        if char_count > 0:
            print("既存キャラクターに初期コイン（100コイン）を付与します...")
            cursor.execute('UPDATE characters SET coins = 100 WHERE coins = 0')
            updated_count = cursor.rowcount
            print(f"{updated_count} 人のキャラクターにコインを付与しました")
            conn.commit()
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        conn.rollback()
        raise e
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()
