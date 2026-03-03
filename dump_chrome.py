"""Chrome profile の全ジェスチャーボタンの生データをダンプ"""
import sys, io, sqlite3, os, json
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
    "c253": "DPI button",
    "c82":  "Middle button",
    "c83":  "Back button (mouse4)",
    "c86":  "Forward button (mouse5)",
    "c91":  "Left tilt",
    "c93":  "Right tilt",
    "thumb_wheel_adapter": "Thumb wheel",
}

profile = data.get("profile-application_id_google_chrome", {})
assignments = profile.get("assignments", [])

print("=" * 70)
print("CHROME PROFILE - RAW GESTURE DATA")
print("=" * 70)

for assign in assignments:
    slot = assign.get("slotId", "")
    if "radial-menu" in slot or "mouse_settings" in slot or "mouse_scroll_wheel" in slot:
        continue
    
    suffix = slot.rsplit("_", 1)[-1] if "_" in slot else slot
    btn_name = SLOT_NAMES.get(suffix, suffix)
    
    card = assign.get("card", {})
    card_id = card.get("id", "")
    is_gesture = "one_of_gesture_button" in card_id
    selected = card.get("selected", "(empty)")
    
    print(f"\n--- {btn_name} (slot suffix: {suffix}) ---")
    print(f"  card_id: {card_id}")
    print(f"  is_gesture_button: {is_gesture}")
    
    if is_gesture:
        print(f"  selected mode: {selected}")
        nested = card.get("nestedCards", {})
        
        # Show ALL available gesture modes
        for mode_name in sorted(nested.keys()):
            mode_data = nested[mode_name]
            if not isinstance(mode_data, dict):
                print(f"  [{mode_name}]: {mode_data}")
                continue
            inner = mode_data.get("nestedCards", {})
            if not inner:
                print(f"  [{mode_name}]: (no nestedCards)")
                continue
            
            actions = {}
            for d in ["click", "up", "down", "left", "right"]:
                if d in inner:
                    m = inner[d].get("macro", {})
                    a = m.get("actionName", "")
                    if not a:
                        a = m.get("system", {}).get("action", "")
                    if not a:
                        a = m.get("mouse", {}).get("action", "")
                    actions[d] = a or "(none)"
                    
            print(f"  [{mode_name}]:")
            for d in ["click", "up", "down", "left", "right"]:
                if d in actions:
                    print(f"    {d:6s}: {actions[d]}")
    else:
        # Simple action
        macro = card.get("macro", {})
        a = macro.get("actionName", "")
        if not a:
            a = macro.get("system", {}).get("action", "")
        if not a:
            a = macro.get("mouse", {}).get("action", "")
        card_name = card.get("name", "")
        print(f"  simple action: {a or card_name or card_id}")
