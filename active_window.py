"""
active_window.py - アクティブウィンドウ検知 & アイコン取得モジュール
最前面ウィンドウの実行ファイル名・タイトル・アイコンを取得する。
"""

import ctypes
import ctypes.wintypes
import os
from dataclasses import dataclass, field
from typing import Optional

import psutil
import win32api
import win32con
import win32gui
import win32process
import win32ui
from PIL import Image


@dataclass
class WindowInfo:
    """アクティブウィンドウの情報。"""
    exe_name: str = ""          # e.g. "chrome.exe"
    exe_path: str = ""          # フルパス
    window_title: str = ""
    icon: Optional[Image.Image] = field(default=None, repr=False)


def get_active_window_info() -> WindowInfo:
    """現在最前面のウィンドウの情報を取得する。"""
    info = WindowInfo()

    try:
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return info

        # ウィンドウタイトル
        info.window_title = win32gui.GetWindowText(hwnd)

        # PID → プロセス情報
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        try:
            proc = psutil.Process(pid)
            info.exe_path = proc.exe()
            info.exe_name = os.path.basename(info.exe_path).lower()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

        # アイコン取得
        info.icon = _extract_icon(hwnd, info.exe_path)

    except Exception:
        pass

    return info


def _extract_icon(hwnd: int, exe_path: str) -> Optional[Image.Image]:
    """ウィンドウまたは実行ファイルからアイコンを抽出し、PIL Image で返す。"""
    icon_size = 32

    # 方法1: ウィンドウメッセージでアイコン取得
    hicon = _icon_from_window_message(hwnd)

    # 方法2: 実行ファイルから抽出
    if not hicon and exe_path:
        hicon = _icon_from_exe(exe_path)

    if not hicon:
        return None

    return _hicon_to_pil(hicon, icon_size)


def _icon_from_window_message(hwnd: int) -> Optional[int]:
    """WM_GETICON でアイコンハンドルを取得。"""
    try:
        hicon = win32gui.SendMessage(hwnd, win32con.WM_GETICON, win32con.ICON_BIG, 0)
        if not hicon:
            hicon = win32gui.SendMessage(hwnd, win32con.WM_GETICON, win32con.ICON_SMALL, 0)
        if not hicon:
            hicon = ctypes.windll.user32.GetClassLongPtrW(hwnd, -14)  # GCL_HICON
        return hicon if hicon else None
    except Exception:
        return None


def _icon_from_exe(exe_path: str) -> Optional[int]:
    """実行ファイルから大アイコンを抽出。"""
    try:
        large_icons, _ = win32gui.ExtractIconEx(exe_path, 0, 1)
        if large_icons:
            return large_icons[0]
    except Exception:
        pass
    return None


def _hicon_to_pil(hicon: int, size: int = 32) -> Optional[Image.Image]:
    """HICON → PIL.Image に変換。"""
    try:
        hdc_screen = win32gui.GetDC(0)
        hdc = win32ui.CreateDCFromHandle(hdc_screen)
        hdc_mem = hdc.CreateCompatibleDC()

        bmp = win32ui.CreateBitmap()
        bmp.CreateCompatibleBitmap(hdc, size, size)
        hdc_mem.SelectObject(bmp)

        # 背景を透明扱い (RGBA で取得するため黒で塗りつぶし)
        hdc_mem.FillSolidRect((0, 0, size, size), 0x00000000)
        win32gui.DrawIconEx(
            hdc_mem.GetHandleOutput(), 0, 0, hicon,
            size, size, 0, None, win32con.DI_NORMAL,
        )

        bmp_info = bmp.GetInfo()
        bmp_bits = bmp.GetBitmapBits(True)

        img = Image.frombuffer(
            "RGBA", (bmp_info["bmWidth"], bmp_info["bmHeight"]),
            bmp_bits, "raw", "BGRA", 0, 1,
        )

        # クリーンアップ
        hdc_mem.DeleteDC()
        win32gui.ReleaseDC(0, hdc_screen)
        win32gui.DestroyIcon(hicon)

        return img.copy()

    except Exception:
        return None
