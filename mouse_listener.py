"""
mouse_listener.py - マウスボタン検知モジュール
MX Ergo S のトリガーボタンクリックでオーバーレイの表示/非表示をトグルする。
"""

import threading
from pynput.mouse import Button, Listener


# config の trigger_button 文字列を pynput の Button にマッピング
BUTTON_MAP = {
    "middle": Button.middle,
    "x1": Button.x1,       # 拡張ボタン1（戻る）
    "x2": Button.x2,       # 拡張ボタン2（進む）
}


class MouseTriggerListener:
    """特定のマウスボタンのクリックでトグルコールバックを呼び出す。"""

    def __init__(self, trigger_button_name: str, on_toggle_cb):
        """
        Args:
            trigger_button_name: "middle", "x1", "x2" のいずれか
            on_toggle_cb: トグル時コールバック (x, y) -> None
        """
        self._trigger = BUTTON_MAP.get(trigger_button_name, Button.middle)
        self._on_toggle_cb = on_toggle_cb
        self._listener: Listener | None = None

    # ── pynput callbacks ──────────────────────────────────

    def _on_click(self, x: int, y: int, button: Button, pressed: bool):
        if button != self._trigger:
            return
        # release (pressed=False) のタイミングでトグル
        if not pressed:
            self._on_toggle_cb(x, y)

    # ── public API ────────────────────────────────────────

    def start(self):
        """リスナーをバックグラウンドスレッドで開始する。"""
        self._listener = Listener(on_click=self._on_click)
        self._listener.daemon = True
        self._listener.start()

    def stop(self):
        """リスナーを停止する。"""
        if self._listener:
            self._listener.stop()
            self._listener = None
