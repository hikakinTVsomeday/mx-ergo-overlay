"""
overlay_ui.py - ジェスチャー・チートシート・オーバーレイUI
各ボタンのアクション一覧をリスト形式で表示する。
ジェスチャーボタン（押しっぱ+方向）と単発ボタンを区別して表示。
"""

import tkinter as tk
from typing import List, Optional

from PIL import Image, ImageTk

from read_settings import ButtonAction


# ── テーマ ───────────────────────────────────────────────
BG_COLOR = "#1a1b2e"
HEADER_BG = "#242540"
ACCENT_COLOR = "#7c8aff"
TEXT_COLOR = "#e8e8f0"
DIM_TEXT = "#6666aa"
APP_NAME_COLOR = "#c0c4ff"
BORDER_COLOR = "#2d2e4a"
SEP_COLOR = "#333455"
BTN_NAME_COLOR = "#9fa4e0"
ACTION_COLOR = "#e0e0f0"

# 方向ごとのカラー
DIR_STYLE = {
    "click": ("click",  "#ff9800"),
    "up":    ("UP",     "#66bb6a"),
    "down":  ("DOWN",   "#ef5350"),
    "left":  ("LEFT",   "#42a5f5"),
    "right": ("RIGHT",  "#ab47bc"),
}

OVERLAY_ALPHA = 0.93
FADE_STEPS = 6
FADE_INTERVAL_MS = 18

FONT_TITLE = ("Segoe UI", 12, "bold")
FONT_BTN = ("Segoe UI", 10, "bold")
FONT_ACTION = ("Segoe UI", 10)
FONT_DIR = ("Segoe UI", 9)
FONT_SMALL = ("Segoe UI", 8)


class OverlayUI:
    """全ボタンのアクションを表示するオーバーレイ。"""

    def __init__(self, root: tk.Tk):
        self._root = root
        self._win: Optional[tk.Toplevel] = None
        self._icon_photo: Optional[ImageTk.PhotoImage] = None
        self._current_alpha = 0.0
        self._fade_after_id: Optional[str] = None
        self._visible = False

    def show(self, app_name: str, buttons: List[ButtonAction],
             icon: Optional[Image.Image] = None):
        if self._visible:
            self.hide_immediate()
        self._build_window(app_name, buttons, icon)
        self._position_window()
        self._visible = True
        self._fade_in()

    def hide(self):
        if not self._visible:
            return
        self._visible = False
        self._fade_out()

    def hide_immediate(self):
        self._cancel_fade()
        self._visible = False
        if self._win:
            self._win.destroy()
            self._win = None

    @property
    def visible(self) -> bool:
        return self._visible

    # ── ウィンドウ構築 ────────────────────────────────────

    def _build_window(self, app_name: str, buttons: List[ButtonAction],
                      icon: Optional[Image.Image]):
        win = tk.Toplevel(self._root)
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        win.attributes("-alpha", 0.0)
        win.configure(bg=BG_COLOR)
        self._win = win

        outer = tk.Frame(win, bg=BORDER_COLOR, padx=2, pady=2)
        outer.pack()

        container = tk.Frame(outer, bg=BG_COLOR, padx=16, pady=12)
        container.pack()

        # ── ヘッダー ──
        header = tk.Frame(container, bg=HEADER_BG, padx=12, pady=8)
        header.pack(fill="x", pady=(0, 10))

        hdr_inner = tk.Frame(header, bg=HEADER_BG)
        hdr_inner.pack()

        if icon:
            try:
                resized = icon.resize((28, 28), Image.LANCZOS)
                self._icon_photo = ImageTk.PhotoImage(resized)
                tk.Label(hdr_inner, image=self._icon_photo, bg=HEADER_BG).pack(
                    side="left", padx=(0, 8))
            except Exception:
                pass

        tk.Label(hdr_inner, text=app_name, font=FONT_TITLE,
                 fg=APP_NAME_COLOR, bg=HEADER_BG).pack(side="left")

        # ── ボタンリスト ──
        first = True
        for btn in buttons:
            # 空のボタンはスキップ
            if not btn.is_gesture and not btn.simple_action:
                continue

            if not first:
                tk.Frame(container, bg=SEP_COLOR, height=1).pack(
                    fill="x", padx=4, pady=3)
            first = False

            self._build_button_entry(container, btn)

    def _build_button_entry(self, parent: tk.Frame, btn: ButtonAction):
        row = tk.Frame(parent, bg=BG_COLOR)
        row.pack(fill="x", padx=2, pady=2)

        # ボタン名ラベル
        tk.Label(
            row, text=btn.button_name,
            font=FONT_BTN, fg=BTN_NAME_COLOR, bg=BG_COLOR,
            width=14, anchor="w",
        ).pack(side="left", padx=(0, 8))

        # アクション部分
        action_frame = tk.Frame(row, bg=BG_COLOR)
        action_frame.pack(side="left", fill="x", expand=True)

        if btn.is_gesture:
            if btn.has_any_direction():
                # ジェスチャー: 方向アクションを表示
                for attr, (label, color) in DIR_STYLE.items():
                    value = getattr(btn, f"gesture_{attr}", "")
                    if value:
                        line = tk.Frame(action_frame, bg=BG_COLOR)
                        line.pack(anchor="w")
                        tk.Label(
                            line, text=f" {label} ",
                            font=FONT_DIR, fg=color, bg=BG_COLOR,
                            width=6, anchor="w",
                        ).pack(side="left")
                        tk.Label(
                            line, text=value,
                            font=FONT_ACTION, fg=ACTION_COLOR, bg=BG_COLOR,
                        ).pack(side="left")
            else:
                # ジェスチャーボタンだがクリックのみ
                action_text = btn.gesture_click or "(--)"
                tk.Label(
                    action_frame, text=action_text,
                    font=FONT_ACTION, fg=ACTION_COLOR, bg=BG_COLOR,
                ).pack(anchor="w")
        else:
            # 単発アクション
            tk.Label(
                action_frame, text=btn.simple_action,
                font=FONT_ACTION, fg=ACTION_COLOR, bg=BG_COLOR,
            ).pack(anchor="w")

    # ── 位置 ─────────────────────────────────────────────

    def _position_window(self):
        win = self._win
        win.update_idletasks()
        w = win.winfo_reqwidth()
        h = win.winfo_reqheight()
        sw = win.winfo_screenwidth()
        sh = win.winfo_screenheight()
        win.geometry(f"+{(sw - w) // 2}+{(sh - h) // 2}")

    # ── フェード ─────────────────────────────────────────

    def _cancel_fade(self):
        if self._fade_after_id:
            self._root.after_cancel(self._fade_after_id)
            self._fade_after_id = None

    def _fade_in(self):
        self._cancel_fade()
        self._current_alpha = 0.0
        self._fade_step(target=OVERLAY_ALPHA, delta=OVERLAY_ALPHA / FADE_STEPS)

    def _fade_out(self):
        self._cancel_fade()
        self._fade_step(target=0.0, delta=-(self._current_alpha / FADE_STEPS))

    def _fade_step(self, target: float, delta: float):
        if not self._win:
            return
        self._current_alpha += delta
        done = False
        if delta > 0 and self._current_alpha >= target:
            self._current_alpha = target
            done = True
        elif delta < 0 and self._current_alpha <= target:
            self._current_alpha = 0.0
            done = True
        try:
            self._win.attributes("-alpha", max(0.0, self._current_alpha))
        except tk.TclError:
            return
        if done:
            if target == 0.0 and self._win:
                self._win.destroy()
                self._win = None
        else:
            self._fade_after_id = self._root.after(
                FADE_INTERVAL_MS, self._fade_step, target, delta)
