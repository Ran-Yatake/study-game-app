import math

def calculate_experience(study_minutes: float) -> int:
    """学習時間（分）から経験値を計算"""
    # 1分 = 10経験値
    return int(study_minutes * 10)

def calculate_level(experience: int) -> int:
    """経験値からレベルを計算"""
    # レベル計算式: level = floor(sqrt(exp / 100)) + 1
    # レベル1: 0-99exp, レベル2: 100-399exp, レベル3: 400-899exp...
    if experience < 100:
        return 1
    return int(math.sqrt(experience / 100)) + 1

def get_character_appearance(level: int) -> dict:
    """レベルに応じたキャラクターの見た目を取得"""
    appearances = {
        1: {"color": "#8B4513", "size": "small", "accessories": []},  # 茶色、小さい
        2: {"color": "#32CD32", "size": "small", "accessories": ["hat"]},  # 緑、帽子
        3: {"color": "#4169E1", "size": "medium", "accessories": ["hat", "book"]},  # 青、本
        4: {"color": "#FF6347", "size": "medium", "accessories": ["hat", "book", "glasses"]},  # 赤、眼鏡
        5: {"color": "#FFD700", "size": "large", "accessories": ["crown", "book", "glasses", "robe"]},  # 金、王冠
    }
    
    if level <= 5:
        return appearances[level]
    else:
        # レベル5以上は金色でサイズ大、全アクセサリー
        return appearances[5]

def get_next_level_exp(current_level: int) -> int:
    """次のレベルに必要な経験値を取得"""
    if current_level >= 5:
        return (current_level ** 2) * 100
    return (current_level ** 2) * 100
