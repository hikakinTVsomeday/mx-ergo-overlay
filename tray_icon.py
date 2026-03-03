"""
tray_icon.py - システムトレイ常駐モジュール
pystray でシステムトレイにアイコンを表示し、メニューで操作を提供する。
"""

import threading
from typing import Callable, Optional

from PIL import Image, ImageDraw
from pystray import Icon, Menu, MenuItem


def _create_default_icon() -> Image.Image:
    """pystray 用のデフォルトトレイアイコン (シンプルな十字) を生成。"""
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 円形の背景
    draw.ellipse([4, 4, size - 4, size - 4], fill=(90, 100, 220, 255))

    # 十字
    cx, cy = size // 2, size // 2
    arm = 16
    thickness = 4
    # 縦棒
    draw.rectangle(
        [cx - thickness // 2, cy - arm, cx + thickness // 2, cy + arm],
        fill=(255, 255, 255, 255),
    )
    # 横棒
    draw.rectangle(
        [cx - arm, cy - thickness // 2, cx + arm, cy + thickness // 2],
        fill=(255, 255, 255, 255),
    )

    return img


class TrayIcon:
    """システムトレイアイコンを管理する。"""

    def __init__(self, on_reload: Callable, on_quit: Callable):
        self._on_reload = on_reload
        self._on_quit = on_quit
        self._icon: Optional[Icon] = None
        self._thread: Optional[threading.Thread] = None

    def start(self):
        """トレイアイコンをバックグラウンドスレッドで開始する。"""
        menu = Menu(
            MenuItem("設定を再読み込み", self._handle_reload),
            Menu.SEPARATOR,
            MenuItem("終了", self._handle_quit),
        )

        self._icon = Icon(
            name="MX Ergo Overlay",
            icon=_create_default_icon(),
            title="MX Ergo Gesture Overlay",
            menu=menu,
        )

        self._thread = threading.Thread(target=self._icon.run, daemon=True)
        self._thread.start()

    def stop(self):
        """トレイアイコンを停止する。"""
        if self._icon:
            try:
                self._icon.stop()
            except Exception:
                pass
            self._icon = None

    def _handle_reload(self, icon, item):
        self._on_reload()

    def _handle_quit(self, icon, item):
        self._on_quit()
