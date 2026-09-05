
from __future__ import annotations

import sys
import traceback
from pathlib import Path

GOC = Path(__file__).resolve().parent
sys.path.insert(0, str(GOC / "src"))

LOG = GOC / "ai_overlay.log"
MB_ICONERROR = 0x10


def _mo_log():
    try:
        f = open(LOG, "w", encoding="utf-8", buffering=1)   # buffering=1: ghi tung dong
        sys.stdout = sys.stderr = f
        return f
    except OSError:
        return None


def _hop_thoai(tieu_de: str, noi_dung: str) -> None:
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(None, noi_dung[:1500], tieu_de, MB_ICONERROR)
    except Exception:
        pass


def main() -> int:
    f = _mo_log()
    try:
        from ai_overlay.app import main as chay
        ma = chay()
        if ma != 0:
            _hop_thoai("AI Overlay khong khoi dong duoc",
                       f"Chuong trinh thoat voi ma {ma}.\n\nXem chi tiet tai:\n{LOG}")
        return ma
    except Exception:
        vet = traceback.format_exc()
        print(vet)
        _hop_thoai("AI Overlay - loi", f"{vet}\n\nGhi day du tai:\n{LOG}")
        return 1
    finally:
        if f is not None:
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
            f.close()


if __name__ == "__main__":
    raise SystemExit(main())
