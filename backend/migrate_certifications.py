"""
資格テーブルを追加するマイグレーションスクリプト
"""

from sqlalchemy import create_engine, text
import os

# データベース接続
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./study_game.db")
engine = create_engine(DATABASE_URL)

def run_migration():
    """資格テーブルのマイグレーションを実行"""
    
    with engine.connect() as connection:
        # トランザクションを開始
        transaction = connection.begin()
        
        try:
            # 資格テーブルが既に存在するかチェック
            result = connection.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='certifications'
            """))
            
            if result.fetchone() is None:
                # 資格テーブルを作成
                connection.execute(text("""
                    CREATE TABLE certifications (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        character_id INTEGER NOT NULL,
                        name VARCHAR(200) NOT NULL,
                        category VARCHAR(100),
                        itss_level INTEGER DEFAULT 1,
                        obtained_date DATETIME,
                        description TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (character_id) REFERENCES characters(id)
                    )
                """))
                
                print("✅ 資格テーブル (certifications) を作成しました")
            else:
                print("ℹ️  資格テーブル (certifications) は既に存在します")
            
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
