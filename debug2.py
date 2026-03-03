"""デバッグ: 2つのデフォルトプロファイルの構造比較"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import sqlite3, os, json

DB_PATH = os.path.join(os.environ["LOCALAPPDATA"], "LogiOptionsPlus", "settings.db")
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("SELECT file FROM data LIMIT 1")
raw = cursor.fetchone()[0]
conn.close()
if isinstance(raw, bytes): raw = raw.decode("utf-8")
data = json.loads(raw)

for pk in data.get("profile_keys", []):
    prof = data.get(pk, {})
    print(f"\n=== {pk} ===")
    for k, v in prof.items():
        if k == "assignments":
            print(f"  assignments: {len(v)} items")
        else:
            s = str(v)
            if len(s) > 200: s = s[:200] + "..."
            print(f"  {k}: {s}")
    
    # activeForApplication の内容を確認
    afa = prof.get("activeForApplication", None)
    if afa:
        print(f"  >>> activeForApplication detail:")
        print(f"      {json.dumps(afa, indent=6, ensure_ascii=False)[:500]}")
