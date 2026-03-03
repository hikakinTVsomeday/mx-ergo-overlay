"""Logi Options+ settings.db からテーブル情報を取得するスクリプト"""
import sqlite3
import os
import json

DB_PATH = os.path.join(os.environ["LOCALAPPDATA"], "LogiOptionsPlus", "settings.db")

print(f"DB path: {DB_PATH}")
print(f"Exists: {os.path.exists(DB_PATH)}")
print()

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# テーブル一覧
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cursor.fetchall()]
print(f"Tables: {tables}")
print()

# 各テーブルのスキーマとサンプルデータ
for table in tables:
    print(f"=== {table} ===")
    cursor.execute(f"PRAGMA table_info({table})")
    columns = cursor.fetchall()
    col_names = [c[1] for c in columns]
    print(f"Columns: {col_names}")

    cursor.execute(f"SELECT count(*) FROM {table}")
    count = cursor.fetchone()[0]
    print(f"Row count: {count}")

    cursor.execute(f"SELECT * FROM {table} LIMIT 3")
    rows = cursor.fetchall()
    for row in rows:
        display = []
        for i, val in enumerate(row):
            s = str(val)
            if len(s) > 200:
                s = s[:200] + "..."
            display.append(f"{col_names[i]}={s}")
        print(f"  {' | '.join(display)}")
    print()

conn.close()
