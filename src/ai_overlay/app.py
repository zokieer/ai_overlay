from __future__ import annotations

import ctypes
import queue
import sys
import threading
import time
import tkinter as tk
from pathlib import Path
import keyboard
from . import capture, config
from .gemini import Gemini, explain_error
from .overlay import Overlay


def enable_dpi_awareness() -> None:
    if sys.platform != "win32":
        return
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PER_MONITOR_AWARE
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


WELCOME = (
    f"{config.HOTKEY_CAPTURE.upper()}  chup + hoi\n"
    f"{config.HOTKEY_TOGGLE.upper()}  an/hien\n"
    f"{config.HOTKEY_SCROLL_UP.upper()} / {config.HOTKEY_SCROLL_DOWN.upper()}  cuon\n"
    f"{config.HOTKEY_FONT_UP.upper()} / {config.HOTKEY_FONT_DOWN.upper()}  co chu\n"
    f"{config.HOTKEY_OPACITY_UP.upper()} / {config.HOTKEY_OPACITY_DOWN.upper()}  do dam chu\n"
    f"{config.HOTKEY_QUIT.upper()}  thoat"
)


class App:
    def __init__(self, register_hotkeys: bool = True, root: tk.Tk | None = None):
        self._owns_root = root is None
        if self._owns_root:
            enable_dpi_awareness()
            root = tk.Tk()
            root.withdraw()
        self.root = root
        self._alive = True
        self.ui_q: queue.Queue = queue.Queue()
        self.overlay = Overlay(self.root)
        self.gemini = Gemini()
        self.gen = 0                  # bo dem request, dung de huy request cu
        self.busy = False
        if register_hotkeys:
            self._register_hotkeys()
        self.root.after(30, self._pump)
        self.overlay.show()
        self.overlay.set_status(f"San sang - {config.MODEL}", config.COLOR_OK)
        self.overlay.set_text(WELCOME)

    def post(self, fn, *args) -> None:
        self.ui_q.put((fn, args))

    def _pump(self) -> None:
        if not self._alive:
            return
        try:
            while True:
                fn, args = self.ui_q.get_nowait()
                try:
                    fn(*args)
                except Exception as exc:      # loi UI khong duoc lam chet vong lap
                    print("UI error:", exc, file=sys.stderr)
        except queue.Empty:
            pass
        self.root.after(30, self._pump)

    def _register_hotkeys(self) -> None:
        pairs = [
            (config.HOTKEY_CAPTURE, lambda: self.post(self.capture)),
            (config.HOTKEY_TOGGLE, lambda: self.post(self.overlay.toggle)),
            (config.HOTKEY_CANCEL, lambda: self.post(self.cancel)),
            (config.HOTKEY_QUIT, lambda: self.post(self.quit)),
            (config.HOTKEY_SCROLL_UP, lambda: self.post(self.overlay.scroll, -config.SCROLL_STEP)),
            (config.HOTKEY_SCROLL_DOWN, lambda: self.post(self.overlay.scroll, config.SCROLL_STEP)),
            (config.HOTKEY_FONT_UP, lambda: self.post(self._font, 1)),
            (config.HOTKEY_FONT_DOWN, lambda: self.post(self._font, -1)),
            (config.HOTKEY_OPACITY_UP,
             lambda: self.post(self.overlay.change_opacity, config.OPACITY_STEP)),
            (config.HOTKEY_OPACITY_DOWN,
             lambda: self.post(self.overlay.change_opacity, -config.OPACITY_STEP)),
        ]
        for combo, cb in pairs:
            try:
                keyboard.add_hotkey(combo, cb, suppress=False)
            except Exception as exc:
                print(f"Khong dang ky duoc phim tat {combo}: {exc}", file=sys.stderr)

    def _font(self, delta: int) -> None:
        self.overlay.change_font_size(delta)

    def capture(self) -> None:
        if self.busy:
            self.overlay.set_status("Dang xu ly, cho chut...", config.COLOR_DIM)
            return

        was_visible = self.overlay.visible
        if was_visible:
            self.overlay.hide()
            self.root.update()
            time.sleep(config.HIDE_DELAY)

        try:
            png, size = capture.grab_png()
            saved = capture.save_png(png) if config.SAVE_SCREENSHOTS else None
        except Exception as exc:
            self.overlay.show()
            self.overlay.set_status("Loi chup man hinh", config.COLOR_ERR)
            self.overlay.set_text(str(exc))
            return

        self.overlay.show()
        self.gen += 1
        self.busy = True

        info = f"{size[0]}x{size[1]} - {len(png) // 1024} KB"
        if saved:
            info += f" - {saved.name}"
        self.overlay.set_status(f"Dang cho tra loi... {info}", config.COLOR_BUSY)
        self.overlay.set_text("")
        threading.Thread(target=self._worker, args=(self.gen, png), daemon=True).start()

    def _worker(self, gen: int, png: bytes) -> None:
        t0 = time.time()
        try:
            text, warning = self.gemini.generate(png)
            if gen == self.gen:
                self.post(self._on_done, gen, text, warning, time.time() - t0)
        except Exception as exc:
            if gen == self.gen:
                self.post(self._on_error, gen, exc)

    def _on_done(self, gen: int, text: str, warning: str, elapsed: float) -> None:
        if gen != self.gen:
            return
        self.busy = False
        body = text or "(API khong tra ve chu nao)"
        if warning:
            body += f"\n\n{warning}"
        self.overlay.set_text(body)
        self.overlay.set_status(f"Xong ({elapsed:.1f}s)",
                                config.COLOR_ERR if warning else config.COLOR_OK)

    def _on_error(self, gen: int, exc: Exception) -> None:
        if gen != self.gen:
            return
        self.busy = False
        hint = explain_error(exc, config.MODEL)
        body = f"{type(exc).__name__}: {exc}"
        if hint:
            body += f"\n\n{hint}"
        self.overlay.set_status("Loi", config.COLOR_ERR)
        self.overlay.set_text(body)

    def cancel(self) -> None:
        self.gen += 1
        self.busy = False
        self.overlay.set_status("Da huy", config.COLOR_DIM)

    def quit(self) -> None:
        self._alive = False
        self.gen += 1                 # cac worker con lai se tu thoat
        self.busy = False
        try:
            keyboard.unhook_all()
        except Exception:
            pass
        try:
            self.overlay.win.destroy()
            if self._owns_root:
                self.root.quit()
                self.root.destroy()
        except tk.TclError:
            pass

    def run(self) -> None:
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.quit()


def main() -> int:
    if len(config.API_KEY)<10:
        print("API Key not found.")
        return 1
    print(f"AI Overlay dang chay - model {config.MODEL}")
    print(f"Anh chup luu tai: {config.SCREENSHOT_DIR}")
    print(WELCOME)
    App().run()
    return 0
