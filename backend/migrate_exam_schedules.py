"""
試験予定テーブルを追加するマイグレーションスクリプト
"""

from sqlalchemy import create_engine, text
import os

# データベース接続
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./study_game.db")
engine = create_engine(DATABASE_URL)

def run_migration():
    """試験予定テーブルのマイグレーションを実行"""
    
    with engine.connect() as connection:
        # トランザクションを開始
        transaction = connection.begin()
        
        try:
            # 試験予定テーブルが既に存在するかチェック
            result = connection.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='exam_schedules'
            """))
            
            if result.fetchone() is None:
                # 試験予定テーブルを作成
                connection.execute(text("""
                    CREATE TABLE exam_schedules (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        character_id INTEGER NOT NULL,
                        exam_name VARCHAR(200) NOT NULL,
                        exam_date DATETIME NOT NULL,
                        category VARCHAR(100),
                        description TEXT,
                        status VARCHAR(20) DEFAULT 'scheduled',
                        reminder_days INTEGER DEFAULT 7,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (character_id) REFERENCES characters(id)
                    )
                """))
                
                print("✅ 試験予定テーブル (exam_schedules) を作成しました")
            else:
                print("ℹ️  試験予定テーブル (exam_schedules) は既に存在します")
            
            # コミット
            transaction.commit()
            print("✅ マイグレーションが完了しました")
            
        except Exception as e:
            # ロールバック
            transaction.rollback()
            print(f"❌ マイグレーションでエラーが発生しました: {e}")
            raise

if __name__ == "__main__":
    run_migration()
