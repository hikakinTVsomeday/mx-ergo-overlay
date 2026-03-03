"""Chrome middle button (c82) の完全なJSON構造をダンプ"""
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

profile = data.get("profile-application_id_google_chrome", {})
assignments = profile.get("assignments", [])

for assign in assignments:
    slot = assign.get("slotId", "")
    suffix = slot.rsplit("_", 1)[-1] if "_" in slot else slot
    
    # ミドルボタンと右チルトの完全ダンプ
    if suffix in ("c82", "c93"):
        name = {"c82": "MIDDLE BUTTON", "c93": "RIGHT TILT"}[suffix]
        print(f"\n{'='*70}")
        print(f"CHROME - {name} (slot: {suffix}) - FULL RAW JSON")
        print(f"{'='*70}")
        print(json.dumps(assign, indent=2, ensure_ascii=False))
