"""
read_settings.py - Logi Options+ settings.db からボタン設定を読み取る

重要: macro の読み取りルール:
  - macro.type == "SYSTEM" → macro.system.action を使う (例: TASK_VIEW, MAXIMIZE)
  - macro.type == "MOUSE"  → macro.mouse.action を使う  (例: MB3)
  - macro.type == "KEYSTROKE" → macro.keystroke を解析する
    - keystroke.modifiers + keystroke.displayCharacter でキー名を組み立てる
    - actionName は "keyboard_none" のことが多く信用できない
  - macro.type == "MEDIA" → macro.media.usage を使う
  - macro.actionName は SYSTEM/MOUSE の場合のみ信頼できる
"""

import json
import os
import sqlite3
from dataclasses import dataclass, field
from typing import Dict, List, Optional


DB_PATH = os.path.join(
    os.environ.get("LOCALAPPDATA", ""), "LogiOptionsPlus", "settings.db"
)

SLOT_BUTTON_MAP = {
    "c253": "精度ボタン",
    "c82":  "ミドルボタン",
    "c83":  "戻るボタン",
    "c86":  "進むボタン",
    "c91":  "左チルト",
    "c93":  "右チルト",
    "thumb_wheel_adapter": "サムホイール",
}

APP_PROFILE_MAP = {
    "application_id_google_chrome": "chrome.exe",
    "application_id_microsoft_edge_chromium": "msedge.exe",
    "application_id_zoom": "zoom.exe",
    "application_id_firefox": "firefox.exe",
    "application_id_excel": "excel.exe",
    "application_id_winword": "winword.exe",
    "application_id_vscode": "code.exe",
    "application_id_teams": "teams.exe",
    "application_id_slack": "slack.exe",
}

# HID modifier codes → 修飾キー名
MODIFIER_MAP = {
    224: "Ctrl",
    225: "Shift",
    226: "Alt",
    227: "Win",
    228: "RCtrl",
    229: "RShift",
    230: "RAlt",
    231: "RWin",
}

# システムアクション → 日本語
SYSTEM_ACTION_LABELS = {
    "TASK_VIEW": "タスクビュー",
    "SWITCH_APPS": "アプリ切替",
    "MAXIMIZE": "最大化",
    "MINIMIZE": "最小化",
    "CHANGE_POINTER_SPEED": "DPI変更",
}

MOUSE_ACTION_LABELS = {
    "MB3": "ミドルクリック",
    "WIN_BACK": "戻る",
    "WIN_FORWARD": "進む",
}

MEDIA_LABELS = {
    "PLAY_PAUSE": "再生/停止",
    "NEXT_TRACK": "次の曲",
    "PREVIOUS_TRACK": "前の曲",
    "VOLUME_UP": "音量UP",
    "VOLUME_DOWN": "音量DOWN",
    "MUTE": "ミュート",
}


@dataclass
class ButtonAction:
    slot_suffix: str = ""
    button_name: str = ""
    is_gesture: bool = False
    gesture_click: str = ""
    gesture_up: str = ""
    gesture_down: str = ""
    gesture_left: str = ""
    gesture_right: str = ""
    simple_action: str = ""

    def has_any_direction(self) -> bool:
        return any([self.gesture_up, self.gesture_down,
                    self.gesture_left, self.gesture_right])

    def is_empty(self) -> bool:
        if self.is_gesture:
            return not (self.gesture_click or self.has_any_direction())
        return not self.simple_action


@dataclass
class AppProfile:
    profile_key: str = ""
    app_exe: str = ""
    app_name: str = ""
    buttons: List[ButtonAction] = field(default_factory=list)


def _read_macro(macro: dict) -> str:
    """macro オブジェクトから人間可読のアクション名を返す"""
    macro_type = macro.get("type", "")

    if macro_type == "SYSTEM":
        action = macro.get("system", {}).get("action", "")
        return SYSTEM_ACTION_LABELS.get(action, action)

    if macro_type == "MOUSE":
        action_name = macro.get("actionName", "")
        mouse_action = macro.get("mouse", {}).get("action", "")
        label = MOUSE_ACTION_LABELS.get(action_name, "")
        if label:
            return label
        return MOUSE_ACTION_LABELS.get(mouse_action, action_name or mouse_action)

    if macro_type == "MEDIA":
        usage = macro.get("media", {}).get("usage", "")
        return MEDIA_LABELS.get(usage, usage)

    if macro_type == "KEYSTROKE":
        keystroke = macro.get("keystroke", {})
        return _read_keystroke(keystroke)

    # フォールバック
    action_name = macro.get("actionName", "")
    if action_name and action_name != "keyboard_none":
        return action_name
    return ""


def _read_keystroke(ks: dict) -> str:
    """keystroke オブジェクトからキー名を組み立てる (例: Ctrl + W)"""
    modifiers = ks.get("modifiers", [])
    display_char = ks.get("displayCharacter", "")
    virtual_key = ks.get("virtualKeyId", "")

    # 修飾キーを名前に変換
    mod_names = []
    for m in modifiers:
        mod_names.append(MODIFIER_MAP.get(m, f"Mod{m}"))

    # キー名を決定
    key_name = display_char
    if not key_name and virtual_key:
        key_name = virtual_key.replace("VK_", "")

    if not key_name and not mod_names:
        return ""

    parts = mod_names + ([key_name] if key_name else [])
    return " + ".join(parts) if parts else ""


def _read_card_action(card: dict) -> str:
    """card の直接の macro または名前からアクションを読む"""
    macro = card.get("macro", {})
    if macro:
        result = _read_macro(macro)
        if result:
            return result

    card_name = card.get("name", "")
    card_id = card.get("id", "")

    if "FORWARD" in card_name or "FORWARD" in card_id:
        return "進む"
    if "BACK" in card_name or "BACK" in card_id:
        return "戻る"
    if "MIDDLE_BUTTON" in card_name:
        return "ミドルクリック"
    if "HORIZONTAL_SCROLL" in card_name:
        return "横スクロール"
    if "CHANGE_POINTER_SPEED" in card_name or "CHANGE_POINTER_SPEED" in card_id:
        return "DPI変更"

    cleaned = card_name.replace("ASSIGNMENT_NAME_", "")
    return cleaned or card_id


def _parse_assignment(assign: dict) -> Optional[ButtonAction]:
    slot_id = assign.get("slotId", "")
    if any(skip in slot_id for skip in
           ["radial-menu", "mouse_settings", "mouse_scroll_wheel"]):
        return None

    suffix = slot_id.rsplit("_", 1)[-1] if "_" in slot_id else slot_id
    button_name = SLOT_BUTTON_MAP.get(suffix, suffix)

    card = assign.get("card", {})
    card_id = card.get("id", "")
    is_gesture_button = "one_of_gesture_button" in card_id

    ba = ButtonAction(
        slot_suffix=suffix,
        button_name=button_name,
        is_gesture=is_gesture_button,
    )

    if is_gesture_button:
        nested = card.get("nestedCards", {})
        selected = card.get("selected", "")
        mode = (nested.get(selected) if selected else None) \
               or nested.get("custom_gesture", {})

        if isinstance(mode, dict):
            inner = mode.get("nestedCards", {})
            for d in ["click", "up", "down", "left", "right"]:
                if d in inner:
                    macro = inner[d].get("macro", {})
                    action = _read_macro(macro)
                    if action:
                        setattr(ba, f"gesture_{d}", action)
    else:
        ba.simple_action = _read_card_action(card)

    return ba


def load_all_profiles(db_path: str = DB_PATH) -> Dict[str, AppProfile]:
    if not os.path.exists(db_path):
        return {}

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT file FROM data LIMIT 1")
    row = cursor.fetchone()
    conn.close()

    if not row:
        return {}

    raw = row[0]
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    data = json.loads(raw)

    profiles: Dict[str, AppProfile] = {}

    for pkey in data.get("profile_keys", []):
        profile_data = data.get(pkey, {})
        if not profile_data:
            continue

        key_suffix = pkey.replace("profile-", "")
        profile_name = profile_data.get("name", "")

        app_exe = ""
        app_name = ""

        for app_id, exe in APP_PROFILE_MAP.items():
            if app_id in key_suffix:
                app_exe = exe
                app_name = app_id.replace("application_id_", "").replace("_", " ").title()
                break

        if not app_exe:
            if profile_name == "PROFILE_NAME_DEFAULT":
                app_exe = "default"
                app_name = "Global"
            elif profile_data.get("baseProfileId"):
                continue
            else:
                app_exe = "default"
                app_name = "Global"

        profile = AppProfile(
            profile_key=pkey, app_exe=app_exe, app_name=app_name,
        )

        for assign in profile_data.get("assignments", []):
            ba = _parse_assignment(assign)
            if ba and not ba.is_empty():
                profile.buttons.append(ba)

        profiles[app_exe] = profile

    return profiles


def get_profile_for_app(
    profiles: Dict[str, AppProfile], exe_name: str
) -> AppProfile:
    if exe_name in profiles:
        return profiles[exe_name]
    return profiles.get("default", AppProfile(app_name="Global", app_exe="default"))


if __name__ == "__main__":
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    profiles = load_all_profiles()
    for exe, prof in profiles.items():
        print(f"\n{'='*50}")
        print(f"{prof.app_name} ({exe})")
        print(f"{'='*50}")
        for btn in prof.buttons:
            if btn.is_gesture:
                print(f"  {btn.button_name}:")
                if btn.gesture_click:
                    print(f"    click : {btn.gesture_click}")
                if btn.gesture_up:
                    print(f"    UP    : {btn.gesture_up}")
                if btn.gesture_down:
                    print(f"    DOWN  : {btn.gesture_down}")
                if btn.gesture_left:
                    print(f"    LEFT  : {btn.gesture_left}")
                if btn.gesture_right:
                    print(f"    RIGHT : {btn.gesture_right}")
            else:
                print(f"  {btn.button_name}: {btn.simple_action}")
