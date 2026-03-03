"""デバッグ: アプリごとのプロファイル解決をテスト"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from read_settings import load_all_profiles, get_profile_for_app

profiles = load_all_profiles()

print("=== 登録済みプロファイル ===")
for exe, prof in profiles.items():
    print(f"  key='{exe}' -> {prof.app_name} ({len(prof.buttons)} buttons)")

print()
print("=== プロファイル解決テスト ===")
test_apps = ["chrome.exe", "msedge.exe", "zoom.exe", "code.exe", "explorer.exe", "notepad.exe"]
for app in test_apps:
    result = get_profile_for_app(profiles, app)
    print(f"  {app:20s} -> {result.app_name} (key={result.app_exe})")
    for btn in result.buttons:
        if btn.is_gesture and btn.has_any_direction():
            dirs = []
            if btn.gesture_click: dirs.append(f"click={btn.gesture_click}")
            if btn.gesture_up: dirs.append(f"up={btn.gesture_up}")
            if btn.gesture_down: dirs.append(f"down={btn.gesture_down}")
            if btn.gesture_left: dirs.append(f"left={btn.gesture_left}")
            if btn.gesture_right: dirs.append(f"right={btn.gesture_right}")
            print(f"    {btn.button_name}: GESTURE [{', '.join(dirs)}]")
        elif btn.is_gesture:
            print(f"    {btn.button_name}: click={btn.gesture_click or '-'}")
        else:
            print(f"    {btn.button_name}: {btn.simple_action}")

# applications キーも確認
import sqlite3, os, json
DB_PATH = os.path.join(os.environ["LOCALAPPDATA"], "LogiOptionsPlus", "settings.db")
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("SELECT file FROM data LIMIT 1")
raw = cursor.fetchone()[0]
conn.close()
if isinstance(raw, bytes): raw = raw.decode("utf-8")
data = json.loads(raw)

print()
print("=== applications key ===")
apps = data.get("applications", {})
print(json.dumps(apps, indent=2, ensure_ascii=False)[:2000])

print()
print("=== profile_keys ===")
for pk in data.get("profile_keys", []):
    print(f"  {pk}")
    
# 2つのデフォルトプロファイルの違いを確認
print()
print("=== Default profiles check ===")
for pk in data.get("profile_keys", []):
    if "application_id" not in pk:
        profile = data.get(pk, {})
        device_filter = profile.get("deviceFilter", "")
        app_filter = profile.get("applicationFilter", "")
        is_default = profile.get("isDefault", "")
        slot_prefix = profile.get("slotPrefix", "")
        print(f"  {pk}:")
        print(f"    deviceFilter={device_filter}")
        print(f"    applicationFilter={app_filter}")
        print(f"    isDefault={is_default}")
        print(f"    slotPrefix={slot_prefix}")
        print(f"    keys: {list(profile.keys())[:10]}")
