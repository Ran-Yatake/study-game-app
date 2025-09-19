-- データベースとテーブルの初期化
-- 既存のテーブルが存在する場合は削除
DROP TABLE IF EXISTS coin_transactions;
DROP TABLE IF EXISTS character_equipment;
DROP TABLE IF EXISTS equipment;
DROP TABLE IF EXISTS exam_schedules;
DROP TABLE IF EXISTS certifications;
DROP TABLE IF EXISTS study_sessions;
DROP TABLE IF EXISTS characters;

-- キャラクターテーブル
CREATE TABLE characters (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    level INT DEFAULT 1,
    total_study_time DECIMAL(10,2) DEFAULT 0.0,
    experience INT DEFAULT 0,
    coins INT DEFAULT 0,
    current_color VARCHAR(20) DEFAULT '#8B4513',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 学習セッションテーブル
CREATE TABLE study_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    character_id INT NOT NULL,
    duration DECIMAL(10,2) NOT NULL,
    subject VARCHAR(200),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP NULL,
    FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE CASCADE
);

-- 資格テーブル
CREATE TABLE certifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    character_id INT NOT NULL,
    name VARCHAR(200) NOT NULL,
    category VARCHAR(100),
    itss_level INT DEFAULT 1,
    obtained_date DATE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE CASCADE
);

-- 装備アイテムマスターテーブル
CREATE TABLE equipment (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    price INT NOT NULL,
    description TEXT,
    color_code VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- キャラクター装備テーブル
CREATE TABLE character_equipment (
    id INT AUTO_INCREMENT PRIMARY KEY,
    character_id INT NOT NULL,
    equipment_id VARCHAR(50) NOT NULL,
    is_equipped TINYINT DEFAULT 0,
    purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE CASCADE,
    FOREIGN KEY (equipment_id) REFERENCES equipment(id) ON DELETE CASCADE
);

-- コイン取引履歴テーブル
CREATE TABLE coin_transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    character_id INT NOT NULL,
    amount INT NOT NULL,
    transaction_type VARCHAR(20) NOT NULL,
    source VARCHAR(50),
    study_session_id INT,
    equipment_id VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE CASCADE,
    FOREIGN KEY (study_session_id) REFERENCES study_sessions(id) ON DELETE SET NULL,
    FOREIGN KEY (equipment_id) REFERENCES equipment(id) ON DELETE SET NULL
);

-- 試験予定テーブル
CREATE TABLE exam_schedules (
    id INT AUTO_INCREMENT PRIMARY KEY,
    character_id INT NOT NULL,
    exam_name VARCHAR(200) NOT NULL,
    exam_date DATE NOT NULL,
    category VARCHAR(100),
    description TEXT,
    status VARCHAR(20) DEFAULT 'scheduled',
    reminder_days INT DEFAULT 7,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE CASCADE
);

-- 初期データの挿入
INSERT INTO characters (name, level, total_study_time, experience, coins) VALUES
('学習太郎', 1, 0.0, 0, 100);

-- 装備アイテムの初期データ
INSERT INTO equipment (id, name, category, price, description, color_code) VALUES
('hat_basic', '学習帽', 'accessory', 50, '学習に集中できる帽子', NULL),
('glasses_reading', '読書用メガネ', 'accessory', 75, '長時間の読書に最適', NULL),
('color_blue', 'ブルー', 'color', 30, '爽やかな青色', '#4169E1'),
('color_green', 'グリーン', 'color', 30, '自然な緑色', '#32CD32'),
('color_red', 'レッド', 'color', 30, '情熱的な赤色', '#FF6347'),
('color_purple', 'パープル', 'color', 40, '神秘的な紫色', '#9370DB'),
('color_orange', 'オレンジ', 'color', 35, 'エネルギッシュなオレンジ', '#FF8C00'),
('hat_graduation', '卒業帽', 'accessory', 150, '学習の成果を象徴する帽子', NULL),
('glasses_smart', 'スマートグラス', 'accessory', 200, '未来的なスマートグラス', NULL);