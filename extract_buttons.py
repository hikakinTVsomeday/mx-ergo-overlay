"""settings.db からボタンごとのアサインメント構造を抽出する"""
import sqlite3
import os
import json

DB_PATH = os.path.join(os.environ["LOCALAPPDATA"], "LogiOptionsPlus", "settings.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("SELECT file FROM data LIMIT 1")
row = cursor.fetchone()
conn.close()

raw = row[0]
if isinstance(raw, bytes):
    raw = raw.decode("utf-8")
data = json.loads(raw)

# profile keys を探す
profile_keys = data.get("profile_keys", [])
print(f"Profile keys: {profile_keys}")
print()

# 各プロファイルのassignments構造を調べる
for key in sorted(data.keys()):
    if not key.startswith("profile-"):
        continue
    profile = data[key]
    assignments = profile.get("assignments", [])
    print(f"=== {key} ({len(assignments)} assignments) ===")
    
    for i, assign in enumerate(assignments):
        # ボタンのスロット情報
        slot = assign.get("slotId", "?")
        button_name = assign.get("buttonName", assign.get("displayName", "?"))
        
        # カードの情報
        card = assign.get("card", {})
        card_id = card.get("id", "?")
        card_name = card.get("displayName", card.get("name", "?"))
        
        # マクロ（単純アクション）の場合
        macro = card.get("macro", {})
        macro_action = macro.get("actionName", macro.get("system", {}).get("action", ""))
        
        # ネストカード（ジェスチャー）の場合
        nested = card.get("nestedCards", {})
        selected = card.get("selected", "")
        
        print(f"  [{i}] slot={slot} button={button_name}")
        print(f"       card_id={card_id} card_name={card_name}")
        
        if macro_action:
            print(f"       macro: {macro_action}")
        
        if selected:
            print(f"       selected_gesture: {selected}")
        
        if nested:
            # custom_gesture の中身を見る
            for mode_name, mode_data in nested.items():
                if not isinstance(mode_data, dict):
                    continue
                inner = mode_data.get("nestedCards", {})
                if inner:
                    directions = {}
                    for dir_name in ["click", "up", "down", "left", "right"]:
                        if dir_name in inner:
                            m = inner[dir_name].get("macro", {})
                            action = m.get("actionName", "")
                            if not action:
                                sys_action = m.get("system", {}).get("action", "")
                                mouse_action = m.get("mouse", {}).get("action", "")
                                action = sys_action or mouse_action or "none"
                            directions[dir_name] = action
                    if any(v and v != "keyboard_none" for v in directions.values()):
                        print(f"       {mode_name}: {directions}")
    print()
