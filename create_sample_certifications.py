"""
サンプル資格データを作成するスクリプトです。
"""

import requests
import json
from datetime import datetime, timedelta

API_BASE_URL = "http://localhost:8000"

def create_sample_certifications():
    """サンプル資格データを作成"""
    
    # まずキャラクターを取得
    try:
        response = requests.get(f"{API_BASE_URL}/characters")
        characters = response.json()
        
        if not characters:
            print("キャラクターが存在しません。先にキャラクターを作成してください。")
            return
        
        character_id = characters[0]['id']
        print(f"キャラクター ID {character_id} に資格を追加します...")
        
        # サンプル資格データ
        sample_certifications = [
            {
                "character_id": character_id,
                "name": "基本情報技術者試験",
                "category": "IT・情報処理",
                "itss_level": 2,
                "obtained_date": (datetime.now() - timedelta(days=365)).isoformat(),
                "description": "ITの基礎知識を証明する国家資格。プログラミング、システム設計、データベース、ネットワークなどの幅広い知識をカバー。"
            },
            {
                "character_id": character_id,
                "name": "応用情報技術者試験",
                "category": "IT・情報処理",
                "itss_level": 3,
                "obtained_date": (datetime.now() - timedelta(days=180)).isoformat(),
                "description": "ITエンジニアとしての実践的な知識とスキルを証明する国家資格。システム開発、プロジェクト管理、情報セキュリティなど。"
            },
            {
                "character_id": character_id,
                "name": "Python 3 エンジニア認定基礎試験",
                "category": "プログラミング",
                "itss_level": 2,
                "obtained_date": (datetime.now() - timedelta(days=90)).isoformat(),
                "description": "Pythonプログラミングの基礎的な知識を証明する認定試験。文法、ライブラリ、プログラミング手法など。"
            },
            {
                "character_id": character_id,
                "name": "AWS Solutions Architect Associate",
                "category": "クラウド",
                "itss_level": 4,
                "obtained_date": (datetime.now() - timedelta(days=30)).isoformat(),
                "description": "AWS上でのシステムアーキテクチャ設計能力を証明する認定資格。可用性、コスト効率性、セキュリティを考慮した設計。"
            },
            {
                "character_id": character_id,
                "name": "情報セキュリティマネジメント試験",
                "category": "セキュリティ",
                "itss_level": 3,
                "obtained_date": (datetime.now() - timedelta(days=200)).isoformat(),
                "description": "情報セキュリティ管理の実務能力を認定する国家資格。リスク管理、インシデント対応、セキュリティ対策など。"
            },
            {
                "character_id": character_id,
                "name": "TOEIC 800点",
                "category": "語学",
                "itss_level": 4,
                "obtained_date": (datetime.now() - timedelta(days=120)).isoformat(),
                "description": "ビジネス英語能力を証明するテスト。国際的なコミュニケーション能力と読解力の証明。"
            },
            {
                "character_id": character_id,
                "name": "データサイエンティスト検定 リテラシーレベル",
                "category": "AI・機械学習",
                "itss_level": 3,
                "obtained_date": (datetime.now() - timedelta(days=60)).isoformat(),
                "description": "データサイエンスの基礎知識を証明する検定。統計学、機械学習、データ分析手法など。"
            }
        ]
        
        # 各資格を作成
        for cert_data in sample_certifications:
            try:
                response = requests.post(
                    f"{API_BASE_URL}/certifications",
                    headers={"Content-Type": "application/json"},
                    data=json.dumps(cert_data)
                )
                
                if response.status_code == 200:
                    cert = response.json()
                    print(f"✅ 資格「{cert['name']}」を作成しました (レベル {cert['itss_level']})")
                else:
                    print(f"❌ 資格「{cert_data['name']}」の作成に失敗: {response.status_code}")
                    print(f"   エラー: {response.text}")
            
            except Exception as e:
                print(f"❌ 資格「{cert_data['name']}」の作成中にエラー: {e}")
        
        print("\n📊 サンプル資格データの作成が完了しました！")
        print("アプリケーションの「資格管理」タブで確認してください。")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        print("バックエンドサーバーが起動しているか確認してください。")

if __name__ == "__main__":
    create_sample_certifications()
