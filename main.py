"""
main.py - MX Ergo S ジェスチャー・チートシート・オーバーレイ
settings.db から全ボタンのアクション情報を読み取り、
GUI ウィンドウの ON/OFF ボタンでオーバーレイを表示する。
アクティブアプリの切り替えを自動検知し、オーバーレイ内容を更新する。
"""

import logging
import os
import sys

# pythonw実行時にstdout/stderrがないことによるクラッシュを防ぐ
if sys.stdout is None:
    sys.stdout = open(os.devnull, 'w')
if sys.stderr is None:
    sys.stderr = open(os.devnull, 'w')

import tkinter as tk
from tkinter import font as tkfont

import win32gui

from active_window import get_active_window_info, WindowInfo
from overlay_ui import OverlayUI
from read_settings import load_all_profiles, get_profile_for_app, AppProfile
from tray_icon import TrayIcon

# ── ログ設定 ──────────────────────────────────────────────
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "overlay_debug.log")

logger = logging.getLogger("overlay")
logger.setLevel(logging.DEBUG)

_fh = logging.FileHandler(LOG_FILE, encoding="utf-8", mode="a")
_fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S"))
logger.addHandler(_fh)

def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = handle_exception

# ── 定数 ──────────────────────────────────────────────────

# コントロールウィンドウのテーマ
CTRL_BG = "#1e1f33"
CTRL_FG = "#e0e0f0"
CTRL_ACCENT = "#7c8aff"
CTRL_BTN_ON_BG = "#4caf50"
CTRL_BTN_ON_FG = "#ffffff"
CTRL_BTN_OFF_BG = "#e05555"
CTRL_BTN_OFF_FG = "#ffffff"
CTRL_BTN_HOVER_ON = "#66bb6a"
CTRL_BTN_HOVER_OFF = "#ef6c6c"
CTRL_BORDER = "#2d2e4a"

# アクティブウィンドウ監視間隔 (ms)
POLL_INTERVAL_MS = 500


# ── アプリケーションクラス ────────────────────────────────

class GestureOverlayApp:
    """メインアプリケーション。"""

    def __init__(self):
        # settings.db からプロファイル読み込み
        self._profiles = load_all_profiles()
        if not self._profiles:
            logger.warning("settings.db からプロファイルを読み込めませんでした。")

        self._overlay_visible = False

        # Tkinter ルート
        self._root = tk.Tk()
        self._root.title("MX Ergo Gesture Overlay")
        self._root.resizable(False, False)
        self._root.configure(bg=CTRL_BG)
        self._root.protocol("WM_DELETE_WINDOW", self._on_close)

        # 自分のウィンドウHWND
        self._own_hwnd = None

        # 最後に検知した外部ウィンドウ
        self._last_external_info: WindowInfo = WindowInfo()
        self._last_displayed_exe = ""  # 点滅防止: 最後に表示したexe名

        # オーバーレイUI
        self._overlay = OverlayUI(self._root)

        # システムトレイ
        self._tray = TrayIcon(
            on_reload=self._reload_settings,
            on_quit=self._quit,
        )

        # GUI構築
        self._build_control_window()

    # ── コントロールウィンドウ構築 ─────────────────────────

    def _build_control_window(self):
        root = self._root

        outer = tk.Frame(root, bg=CTRL_BORDER, padx=2, pady=2)
        outer.pack(padx=6, pady=6)

        main_frame = tk.Frame(outer, bg=CTRL_BG, padx=20, pady=16)
        main_frame.pack()

        # タイトル
        title_font = tkfont.Font(family="Segoe UI", size=13, weight="bold")
        tk.Label(
            main_frame,
            text="🖱️  MX Ergo Gesture Overlay",
            font=title_font,
            fg=CTRL_ACCENT,
            bg=CTRL_BG,
        ).pack(pady=(0, 12))

        # 検出中のアプリ
        detect_frame = tk.Frame(main_frame, bg=CTRL_BG)
        detect_frame.pack(pady=(0, 4))

        tk.Label(
            detect_frame,
            text="検出中:",
            font=("Segoe UI", 9),
            fg="#8888aa",
            bg=CTRL_BG,
        ).pack(side="left")

        self._detect_label = tk.Label(
            detect_frame,
            text="—",
            font=("Segoe UI", 9, "bold"),
            fg=CTRL_ACCENT,
            bg=CTRL_BG,
        )
        self._detect_label.pack(side="left", padx=(4, 0))

        # プロファイルマッチ表示
        self._profile_label = tk.Label(
            main_frame,
            text="",
            font=("Segoe UI", 8),
            fg="#6666aa",
            bg=CTRL_BG,
        )
        self._profile_label.pack(pady=(0, 8))

        # ステータス
        status_frame = tk.Frame(main_frame, bg=CTRL_BG)
        status_frame.pack(pady=(0, 12))

        tk.Label(
            status_frame,
            text="オーバーレイ:",
            font=("Segoe UI", 10),
            fg=CTRL_FG,
            bg=CTRL_BG,
        ).pack(side="left")

        self._status_label = tk.Label(
            status_frame,
            text=" OFF",
            font=("Segoe UI", 10, "bold"),
            fg=CTRL_BTN_OFF_BG,
            bg=CTRL_BG,
        )
        self._status_label.pack(side="left")

        # ON/OFF ボタン
        btn_font = tkfont.Font(family="Segoe UI", size=12, weight="bold")
        self._toggle_btn = tk.Button(
            main_frame,
            text="▶  表示する",
            font=btn_font,
            fg=CTRL_BTN_ON_FG,
            bg=CTRL_BTN_ON_BG,
            activeforeground=CTRL_BTN_ON_FG,
            activebackground=CTRL_BTN_HOVER_ON,
            relief="flat",
            cursor="hand2",
            padx=24,
            pady=8,
            command=self._on_toggle,
        )
        self._toggle_btn.pack(pady=(0, 10))
        self._toggle_btn.bind("<Enter>", self._on_btn_enter)
        self._toggle_btn.bind("<Leave>", self._on_btn_leave)

        # 再読み込みボタン
        reload_btn = tk.Button(
            main_frame,
            text="🔄 settings.db 再読み込み",
            font=("Segoe UI", 9),
            fg=CTRL_FG,
            bg="#2d2e4a",
            activeforeground=CTRL_FG,
            activebackground="#3d3e5a",
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=4,
            command=self._reload_settings,
        )
        reload_btn.pack(pady=(0, 4))

        # ウィンドウ位置 (右下寄り)
        root.update_idletasks()
        w = root.winfo_reqwidth()
        h = root.winfo_reqheight()
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        root.geometry(f"+{sw - w - 40}+{sh - h - 80}")

    # ── アクティブウィンドウ監視 ──────────────────────────

    def _poll_active_window(self):
        """定期的にアクティブウィンドウを確認する。"""
        try:
            hwnd = win32gui.GetForegroundWindow()

            # 初回に自分のHWNDを取得
            if self._own_hwnd is None:
                try:
                    self._own_hwnd = int(self._root.wm_frame(), 16)
                    logger.info(f"Own HWND = {self._own_hwnd}")
                except Exception as e:
                    self._own_hwnd = -1
                    logger.warning(f"Failed to get own HWND: {e}")

            # 自分以外のウィンドウの場合のみ追跡
            if hwnd and hwnd != self._own_hwnd:
                info = get_active_window_info()
                logger.debug(f"Poll: hwnd={hwnd} exe={info.exe_name!r} last={self._last_external_info.exe_name!r}")

                if info.exe_name and info.exe_name != self._last_external_info.exe_name:
                    # 新しいアプリに切り替わった
                    logger.info(f"APP CHANGED: {self._last_external_info.exe_name!r} -> {info.exe_name!r}")
                    self._last_external_info = info

                    # 検出ラベル更新
                    profile = get_profile_for_app(self._profiles, info.exe_name)
                    logger.info(f"Profile matched: {profile.app_name} (key={profile.app_exe})")
                    self._detect_label.configure(text=info.exe_name)

                    if profile.app_exe == info.exe_name:
                        self._profile_label.configure(
                            text=f"プロファイル: {profile.app_name}",
                            fg="#66bb6a",
                        )
                    else:
                        self._profile_label.configure(
                            text=f"プロファイル: {profile.app_name} (デフォルト)",
                            fg="#6666aa",
                        )

                    # オーバーレイ表示中なら更新 (点滅防止: exeが変わった時だけ)
                    if self._overlay_visible and info.exe_name != self._last_displayed_exe:
                        logger.info(f"OVERLAY UPDATE: {info.exe_name} (last_displayed={self._last_displayed_exe!r})")
                        self._update_overlay(info)
                    elif self._overlay_visible:
                        logger.debug(f"Overlay visible but same exe already displayed: {self._last_displayed_exe!r}")
            else:
                if hwnd == self._own_hwnd:
                    logger.debug(f"Poll: own window is foreground (hwnd={hwnd})")

        except Exception as e:
            logger.error(f"Poll error: {e}", exc_info=True)

        self._root.after(POLL_INTERVAL_MS, self._poll_active_window)

    # ── ボタンホバー ─────────────────────────────────────

    def _on_btn_enter(self, event):
        color = CTRL_BTN_HOVER_OFF if self._overlay_visible else CTRL_BTN_HOVER_ON
        self._toggle_btn.configure(bg=color)

    def _on_btn_leave(self, event):
        color = CTRL_BTN_OFF_BG if self._overlay_visible else CTRL_BTN_ON_BG
        self._toggle_btn.configure(bg=color)

    # ── トグル ───────────────────────────────────────────

    def _on_toggle(self):
        if self._overlay_visible:
            self._hide_overlay()
        else:
            self._show_overlay()

    def _show_overlay(self):
        info = self._last_external_info
        if not info.exe_name:
            info = get_active_window_info()
            self._last_external_info = info
            logger.info(f"show_overlay: no cached info, fresh detect -> {info.exe_name!r}")

        profile = get_profile_for_app(self._profiles, info.exe_name)
        logger.info(f"SHOW OVERLAY: exe={info.exe_name!r} profile={profile.app_name} buttons={len(profile.buttons)}")

        self._overlay.show(
            app_name=profile.app_name,
            buttons=profile.buttons,
            icon=info.icon,
        )
        self._overlay_visible = True
        self._last_displayed_exe = info.exe_name

        self._toggle_btn.configure(
            text="■  非表示にする",
            bg=CTRL_BTN_OFF_BG,
            activebackground=CTRL_BTN_HOVER_OFF,
        )
        self._status_label.configure(text=" ON", fg=CTRL_BTN_ON_BG)

    def _update_overlay(self, info: WindowInfo):
        """アプリ切り替え時にオーバーレイの中身を更新する。"""
        profile = get_profile_for_app(self._profiles, info.exe_name)

        self._overlay.show(
            app_name=profile.app_name,
            buttons=profile.buttons,
            icon=info.icon,
        )
        self._last_displayed_exe = info.exe_name

    def _hide_overlay(self):
        self._overlay.hide()
        self._overlay_visible = False
        self._last_displayed_exe = ""

        self._toggle_btn.configure(
            text="▶  表示する",
            bg=CTRL_BTN_ON_BG,
            activebackground=CTRL_BTN_HOVER_ON,
        )
        self._status_label.configure(text=" OFF", fg=CTRL_BTN_OFF_BG)

    # ── メニューアクション ────────────────────────────────

    def _reload_settings(self):
        try:
            self._profiles = load_all_profiles()
            logger.info("settings.db を再読み込みしました。")
        except Exception as e:
            logger.error(f"再読み込みに失敗: {e}")

    def _on_close(self):
        self._root.withdraw()

    def _quit(self):
        if self._overlay_visible:
            self._overlay.hide_immediate()
        self._tray.stop()
        self._root.after(0, self._root.destroy)

    # ── 起動 ──────────────────────────────────────────────

    def run(self):
        logger.info("MX Ergo Gesture Overlay を起動しました。")
        logger.info("settings.db から設定を読み込みました。")
        for exe, prof in self._profiles.items():
            logger.info(f"  {prof.app_name} ({exe}): {len(prof.buttons)} ボタン")
        logger.info("ON中はアクティブアプリが変わると自動でジェスチャーが切り替わります。")

        self._root.after(500, self._poll_active_window)
        self._tray.start()
        self._root.mainloop()


# ── エントリーポイント ────────────────────────────────────

if __name__ == "__main__":
    app = GestureOverlayApp()
    app.run()
