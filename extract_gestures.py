"""settings.db の JSON からジェスチャー設定を抽出する"""
import sqlite3
import os
import json

DB_PATH = os.path.join(os.environ["LOCALAPPDATA"], "LogiOptionsPlus", "settings.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("SELECT file FROM data LIMIT 1")
row = cursor.fetchone()
conn.close()

if row:
    raw = row[0]
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    data = json.loads(raw)

    # JSON のトップレベルキーを表示
    print("=== Top-level keys ===")
    for k in sorted(data.keys()):
        v = data[k]
        t = type(v).__name__
        if isinstance(v, (dict, list)):
            print(f"  {k}: {t} (len={len(v)})")
        else:
            s = str(v)
            if len(s) > 100:
                s = s[:100] + "..."
            print(f"  {k}: {t} = {s}")
    
    # gesture 関連のキーを探す
    print("\n=== Keys containing 'gesture' or 'button' ===")
    def find_keys(obj, path=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                full = f"{path}.{k}" if path else k
                if any(word in k.lower() for word in ["gesture", "button", "action", "swipe"]):
                    s = str(v)
                    if len(s) > 200:
                        s = s[:200] + "..."
                    print(f"  {full}: {s}")
                find_keys(v, full)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                find_keys(item, f"{path}[{i}]")
    
    find_keys(data)

    # devices 関連も探す
    print("\n=== Keys containing 'device' ===")
    def find_device_keys(obj, path=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                full = f"{path}.{k}" if path else k
                if "device" in k.lower():
                    s = str(v)
                    if len(s) > 300:
                        s = s[:300] + "..."
                    print(f"  {full}: {s}")
                find_device_keys(v, full)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                find_device_keys(item, f"{path}[{i}]")
    
    find_device_keys(data)
