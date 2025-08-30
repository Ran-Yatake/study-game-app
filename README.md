# 学習時間記録ゲーム

キャラクターを育成しながら学習時間を記録するゲームアプリです。

## 機能

- キャラクター作成・管理
- タイマーを使った学習時間の記録
- 学習時間に応じたキャラクターのレベルアップ
- レベルに応じた見た目の変化
- 学習統計の表示（今日、今週、総学習時間など）

## 技術スタック

- **フロントエンド**: Next.js 15 + TypeScript + Tailwind CSS
- **バックエンド**: Python + FastAPI
- **データベース**: SQLite（簡単なセットアップのため）

## セットアップ方法

### 1. バックエンドの起動

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windowsの場合: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

バックエンドは `http://localhost:8000` で起動します。

### 2. フロントエンドの起動

```bash
cd frontend
npm install
npm run dev
```

フロントエンドは `http://localhost:3000` で起動します。

### 簡単起動スクリプト

バックエンド：
```bash
./start_backend.sh
```

フロントエンド：
```bash
./start_frontend.sh
```

## 使い方

1. ブラウザで `http://localhost:3000` にアクセス
2. 「新しいキャラクター名」欄にキャラクター名を入力して「作成」をクリック
3. タイマーで学習時間を計測
4. 学習するとキャラクターが経験値を獲得し、レベルアップします
5. レベルが上がるとキャラクターの見た目が変化します

## キャラクターのレベルシステム

- **レベル1**: 茶色、小サイズ
- **レベル2**: 緑色、帽子付き
- **レベル3**: 青色、帽子+本
- **レベル4**: 赤色、帽子+本+メガネ
- **レベル5**: 金色、王冠+本+メガネ+ローブ（大サイズ）

### 経験値計算
- 1分の学習 = 10経験値
- レベル1: 0-99exp
- レベル2: 100-399exp
- レベル3: 400-899exp
- ...

## API エンドポイント

- `GET /characters` - キャラクター一覧取得
- `POST /characters` - キャラクター作成
- `GET /characters/{id}/appearance` - キャラクター外見取得
- `POST /timer/start` - タイマー開始
- `POST /timer/stop` - タイマー停止
- `GET /stats/{character_id}` - 統計情報取得

## 開発時の注意事項

- バックエンドとフロントエンドを両方起動する必要があります
- 初回起動時、データベーステーブルは自動で作成されます

## フォルダ構成

study-game-app/
├── backend/           # Python FastAPI バックエンド
│   ├── main.py       # メインAPIサーバー
│   ├── database.py   # SQLiteデータベース設定
│   ├── schemas.py    # Pydanticスキーマ
│   ├── game_logic.py # ゲームロジック（レベル計算など）
│   ├── requirements.txt
│   └── .env
├── frontend/         # Next.js フロントエンド  
│   ├── src/
│   │   ├── app/page.tsx        # メインページ
│   │   ├── components/         # Reactコンポーネント
│   │   │   ├── Character.tsx   # キャラクター表示
│   │   │   ├── Timer.tsx       # タイマー機能
│   │   │   └── Stats.tsx       # 統計表示
│   │   └── lib/api.ts          # APIクライアント
├── start_backend.sh   # バックエンド起動スクリプト
├── start_frontend.sh  # フロントエンド起動スクリプト
└── README.md         # 使用方法説明
