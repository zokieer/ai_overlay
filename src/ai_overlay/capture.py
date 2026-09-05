from __future__ import annotations
import datetime as _dt
from pathlib import Path
import mss
import mss.tools
from . import config
_MSS = getattr(mss, "MSS", None) or mss.mss


def grab_png() -> tuple[bytes, tuple[int, int]]:
    with _MSS() as sct:
        shot = sct.grab(sct.monitors[0])
        png = mss.tools.to_png(shot.rgb, shot.size, level=config.PNG_LEVEL)
        return png, (shot.size.width, shot.size.height)


def save_png(png: bytes, folder: Path | None = None) -> Path:
    folder = folder or config.SCREENSHOT_DIR
    folder.mkdir(parents=True, exist_ok=True)
    stamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
    path = folder / f"screen_{stamp}.png"
    path.write_bytes(png)
    _prune(folder, config.KEEP_LAST_N)
    return path


def _prune(folder: Path, keep: int) -> None:
    if keep <= 0:
        return
    files = sorted(folder.glob("screen_*.png"), key=lambda p: p.stat().st_mtime)
    for old in files[:-keep]:
        try:
            old.unlink()
        except OSError:
            pass
