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

def calculate_coins(study_minutes: float) -> int:
    """学習時間（分）からコインを計算"""
    # 1分 = 1コイン、ボーナス：30分以上で+10コイン、60分以上で+30コイン
    base_coins = int(study_minutes)
    bonus_coins = 0
    
    if study_minutes >= 30:
        bonus_coins += 10
    if study_minutes >= 60:
        bonus_coins += 20  # 追加で20コイン（合計30コイン）
    
    return base_coins + bonus_coins

def get_available_equipment() -> dict:
    """購入可能な装備一覧を取得"""
    equipment_list = {
        "accessories": [
            {"id": "hat", "name": "帽子", "price": 50, "description": "おしゃれな帽子"},
            {"id": "glasses", "name": "眼鏡", "price": 100, "description": "知的な眼鏡"},
            {"id": "book", "name": "本", "price": 30, "description": "学習の友"},
            {"id": "crown", "name": "王冠", "price": 500, "description": "王者の証"},
            {"id": "robe", "name": "ローブ", "price": 200, "description": "魔法使いのローブ"},
            {"id": "sword", "name": "剣", "price": 300, "description": "勇者の剣"},
            {"id": "shield", "name": "盾", "price": 250, "description": "守護の盾"},
            {"id": "staff", "name": "杖", "price": 400, "description": "魔法の杖"},
        ],
        "colors": [
            {"id": "red", "name": "赤色", "price": 80, "color": "#FF6347"},
            {"id": "blue", "name": "青色", "price": 80, "color": "#4169E1"},
            {"id": "green", "name": "緑色", "price": 80, "color": "#32CD32"},
            {"id": "purple", "name": "紫色", "price": 120, "color": "#9932CC"},
            {"id": "orange", "name": "オレンジ色", "price": 100, "color": "#FF8C00"},
            {"id": "pink", "name": "ピンク色", "price": 150, "color": "#FF69B4"},
        ]
    }
    return equipment_list

def calculate_equipment_bonus(equipment_list: list) -> dict:
    """装備による能力ボーナスを計算"""
    # 装備の種類に応じて経験値ボーナスを付与
    bonus = {
        "experience_multiplier": 1.0,
        "coin_multiplier": 1.0,
        "special_effects": []
    }
    
    equipment_bonuses = {
        "crown": {"experience_multiplier": 1.2, "special_effects": ["王者の威厳"]},
        "robe": {"experience_multiplier": 1.15, "special_effects": ["魔法の加護"]},
        "sword": {"coin_multiplier": 1.1, "special_effects": ["戦士の勇気"]},
        "shield": {"experience_multiplier": 1.1, "special_effects": ["守護の力"]},
        "staff": {"coin_multiplier": 1.15, "special_effects": ["魔法の知識"]},
        "book": {"experience_multiplier": 1.05, "special_effects": ["知識の蓄積"]},
        "glasses": {"experience_multiplier": 1.05, "special_effects": ["集中力向上"]},
    }
    
    for equipment in equipment_list:
        if equipment in equipment_bonuses:
            item_bonus = equipment_bonuses[equipment]
            bonus["experience_multiplier"] *= item_bonus.get("experience_multiplier", 1.0)
            bonus["coin_multiplier"] *= item_bonus.get("coin_multiplier", 1.0)
            bonus["special_effects"].extend(item_bonus.get("special_effects", []))
    
    return bonus
