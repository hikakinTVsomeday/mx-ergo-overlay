"""settings.db のアサインメントを正しく分類して出力"""
import sqlite3, os, json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DB_PATH = os.path.join(os.environ["LOCALAPPDATA"], "LogiOptionsPlus", "settings.db")
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("SELECT file FROM data LIMIT 1")
raw = cursor.fetchone()[0]
conn.close()
if isinstance(raw, bytes): raw = raw.decode("utf-8")
data = json.loads(raw)

SLOT_NAMES = {
    "c253": "精度モード(DPI)",
    "c82":  "ミドルボタン",
    "c83":  "戻るボタン",
    "c86":  "進むボタン",
    "c91":  "ミドル左チルト",
    "c93":  "ミドル右チルト",
    "thumb_wheel_adapter": "サムホイール",
}

for pkey in data.get("profile_keys", []):
    profile = data.get(pkey, {})
    assignments = profile.get("assignments", [])
    print(f"\n{'='*60}")
    print(f"プロファイル: {pkey}")
    print(f"{'='*60}")
    
    for assign in assignments:
        slot = assign.get("slotId", "")
        if "radial-menu" in slot or "mouse_settings" in slot or "mouse_scroll_wheel" in slot:
            continue
        
        suffix = slot.rsplit("_", 1)[-1] if "_" in slot else slot
        btn_name = SLOT_NAMES.get(suffix, suffix)
        
        card = assign.get("card", {})
        card_id = card.get("id", "")
        selected = card.get("selected", "")
        is_gesture = "one_of_gesture_button" in card_id
        
        print(f"\n  📍 {btn_name} (slot: {suffix})")
        print(f"     card_id: {card_id}")
        print(f"     ジェスチャーボタン: {'✅ YES' if is_gesture else '❌ NO'}")
        
        if is_gesture:
            print(f"     選択中モード: {selected or '(未設定=custom_gesture)'}")
            nested = card.get("nestedCards", {})
            # selected がなければ custom_gesture を使う
            mode = nested.get(selected, nested.get("custom_gesture", {})) if selected else nested.get("custom_gesture", {})
            if isinstance(mode, dict):
                inner = mode.get("nestedCards", {})
                for d in ["click", "up", "down", "left", "right"]:
                    if d in inner:
                        m = inner[d].get("macro", {})
                        action = m.get("actionName", "")
                        if not action:
                            action = m.get("system", {}).get("action", m.get("mouse", {}).get("action", ""))
                        if not action or action == "keyboard_none":
                            action = "—"
                        label = {"click":"● クリック","up":"↑ 上","down":"↓ 下","left":"← 左","right":"→ 右"}
                        print(f"       {label.get(d, d)}: {action}")
        else:
            macro = card.get("macro", {})
            action = macro.get("actionName", "")
            if not action:
                action = macro.get("system", {}).get("action", macro.get("mouse", {}).get("action", ""))
            if not action:
                name = card.get("name", "")
                action = name.replace("ASSIGNMENT_NAME_", "") if name else card_id
            print(f"     アクション: {action}")
