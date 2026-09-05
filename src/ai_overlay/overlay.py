"""Overlay khong nen: chi co chu noi tren man hinh, chuot xuyen qua hoan toan.

DOC FILE NAY THEO 3 PHAN, tu de den kho:

1. parse_blocks()  - bien markdown thanh danh sach dong co kieu.
   Moi dong tra ve (kieu_dong, cac_doan, thut_le). "cac_doan" la danh sach
   (chu, kieu_chu) vi mot dong co the tron nhieu kieu:
       "Dat **total** = 0"  ->  [("Dat ", ""), ("total", "b"), (" = 0", "")]

2. Dung cua so trong suot (__init__ ... _apply_ex_style)
   Windows co "mau khoa": moi pixel mang dung mau do thanh trong suot tuyet doi.
   Nen cua so dat mau config.TRANSPARENT_KEY roi khai bao -transparentcolor,
   nen chi con chu hien ra.

3. Ve chu (_layout ... redraw)
   Tk khong cho tron nhieu font trong MOT o van ban, ma mot cau tra loi lai co
   ca chu thuong, chu dam va chu code tren cung mot dong. Nen phai tu tinh vi tri
   tung tu: do be ngang, xuong hang khi tran le phai, roi ve tung doan mot.
   Vi nen trong suot nen chu co the nam tren bat ky mau gi -> moi doan duoc ve
   them 8 ban mau den lech 1px de tao vien, giup doc duoc tren moi nen.
"""

from __future__ import annotations

import ctypes
import re
import sys
import tkinter as tk
from tkinter import font as tkfont

from . import config, mathfmt

# 8 huong lech 1px de tao vien chu
_OUTLINE_OFFSETS = ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, -1), (-1, 1), (1, 1))

_FENCE_RE = re.compile(r"(```.*?```)", re.S)

# Thu tu quan trong: cong thuc toan truoc, roi code, roi dam/nghieng.
# Trong $...$ co day dau _ va * ma markdown se hieu nham thanh nghieng/dam.
_INLINE_RE = re.compile(
    r"\$\$(?P<m1>.+?)\$\$"                            # $$ ... $$
    r"|\\\[(?P<m2>.+?)\\\]"                           # \[ ... \]
    r"|\\\((?P<m3>.+?)\\\)"                           # \( ... \)
    r"|\$(?P<m4>[^\s$][^$\n]*[^\s$]|[^\s$])\$"        # $ ... $
    r"|`(?P<c>[^`]+)`"                                # `code`
    r"|\*\*(?P<b1>.+?)\*\*"                           # **dam**
    r"|__(?P<b2>.+?)__"
    r"|\*(?P<i>.+?)\*",                               # *nghieng*
    re.S,
)
# (ten_nhom, kieu_chu). "m" = cong thuc toan.
_GROUPS = (("m1", "m"), ("m2", "m"), ("m3", "m"), ("m4", "m"),
           ("c", "c"), ("b1", "b"), ("b2", "b"), ("i", "i"))
_HR_RE = re.compile(r"^\s*([-*_])\s*(?:\1\s*){2,}$")
_BULLET_RE = re.compile(r"^[-*+]\s+")
_NUM_RE = re.compile(r"^\d+[.)]\s+")
_TOKEN_RE = re.compile(r"\S+|\s+")

# kieu chu trong mot doan: "" thuong | "b" dam | "i" nghieng | "c" code
Run = tuple[str, str]
Block = tuple[str, list[Run], int]


def split_runs(text: str) -> list[Run]:
    """Tach mot dong thanh cac doan co kieu khac nhau.

    >>> split_runs("Dat **total** = `0`")
    [('Dat ', ''), ('total', 'b'), (' = ', ''), ('0', 'c')]
    >>> split_runs(r"Ket qua $\\text{CPI} \\approx 2.22$")
    [('Ket qua ', ''), ('CPI ≈ 2.22', 'm')]
    """
    runs: list[Run] = []
    pos = 0
    for m in _INLINE_RE.finditer(text):
        if m.start() > pos:
            runs.append((mathfmt.convert_bare(text[pos:m.start()]), ""))
        for ten, kieu in _GROUPS:
            noi_dung = m.group(ten)
            if noi_dung is not None:
                if kieu == "m":
                    noi_dung = mathfmt.latex_to_unicode(noi_dung)
                runs.append((noi_dung, kieu))
                break
        pos = m.end()
    if pos < len(text):
        runs.append((mathfmt.convert_bare(text[pos:]), ""))
    return runs


def strip_inline(text: str) -> str:
    """Bo cac dau markdown noi dong, tra ve chu tran."""
    return "".join(t for t, _ in split_runs(text))


def parse_blocks(md: str) -> list[Block]:
    """Chuyen markdown thanh danh sach (kieu_dong, cac_doan, thut_le_pixel).

    kieu_dong: "h1" | "h2" | "body" | "bullet" | "quote" | "code" | "hr"
    """
    blocks: list[Block] = []
    for part in _FENCE_RE.split(md):
        # --- khoi code ``` ... ``` : giu nguyen tung dong, khong dich inline ---
        if part.startswith("```"):
            code = re.sub(r"^```[^\n]*\n?|```$", "", part, flags=re.S).rstrip("\n")
            for line in code.splitlines() or [""]:
                blocks.append(("code", [(line, "")] if line else [], 10))
            continue

        for raw in part.splitlines():
            line = raw.rstrip()
            stripped = line.lstrip()
            cap = (len(line) - len(stripped)) // 2      # cap long nhau cua danh sach

            if not stripped:
                blocks.append(("body", [], 0))
            elif _HR_RE.match(stripped):
                blocks.append(("hr", [], 0))
            elif stripped.startswith("#"):
                muc = len(stripped) - len(stripped.lstrip("#"))
                noi_dung = stripped.lstrip("#").strip()
                blocks.append(("h1" if muc <= 2 else "h2", split_runs(noi_dung), 0))
            elif stripped.startswith(">"):
                blocks.append(("quote", split_runs(stripped.lstrip("> ").strip()), 10))
            elif _BULLET_RE.match(stripped):
                noi_dung = _BULLET_RE.sub("", stripped)
                blocks.append(("bullet", [("• ", "")] + split_runs(noi_dung),
                               8 + cap * 12))
            elif (m := _NUM_RE.match(stripped)):
                blocks.append(("bullet", [(m.group(0), "")] + split_runs(stripped[m.end():]),
                               8 + cap * 12))
            else:
                blocks.append(("body", split_runs(stripped), 0))
    return blocks


class Overlay:
    """Cua so chu trong suot, luon noi len tren, chuot xuyen qua."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.font_size = config.FONT_SIZE
        self.opacity = max(config.OPACITY_MIN, min(config.TEXT_OPACITY, config.OPACITY_MAX))
        self.scroll_y = 0
        self.content_h = 0
        self._content_top = config.PAD_Y   # y bat dau noi dung, ngay duoi thanh trang thai
        self._blocks: list[Block] = []
        self._status = ("San sang", config.COLOR_OK)

        w = tk.Toplevel(root)
        self.win = w
        w.overrideredirect(True)
        w.attributes("-topmost", True)
        w.configure(bg=config.TRANSPARENT_KEY)
        self._transparent_ok = self._enable_transparency()

        self.width, self.height = config.OVERLAY_W, config.OVERLAY_H
        w.geometry(f"{self.width}x{self.height}+{self._x()}+{self._y()}")

        self.canvas = tk.Canvas(
            w, bg=config.TRANSPARENT_KEY, highlightthickness=0, bd=0,
            width=self.width, height=self.height,
        )
        self.canvas.pack(fill="both", expand=True)

        self._build_fonts()

        w.withdraw()
        self.visible = False
        w.after(60, self._apply_ex_style)

    # ---------------------------------------------------------------- setup
    def _enable_transparency(self) -> bool:
        ok = True
        try:
            self.win.attributes("-transparentcolor", config.TRANSPARENT_KEY)
        except tk.TclError:
            ok = False    # Khong phai Windows: khong co -transparentcolor
        self._transparent_ok = ok
        self._apply_opacity()
        return ok

    def _apply_opacity(self) -> None:
        """Windows gop duoc LWA_COLORKEY + LWA_ALPHA, nen alpha chi lam mo phan
        duoc ve, con vung mang mau khoa van trong suot tuyet doi.

        Tren nen khac khong co mau khoa, alpha lam mo ca nen -> ha them mot chut
        de nen do khong che mat noi dung ben duoi.
        """
        alpha = self.opacity if self._transparent_ok else self.opacity * 0.85
        self.win.attributes("-alpha", max(0.05, min(alpha, 1.0)))

    def _x(self) -> int:
        if "left" in config.OVERLAY_ANCHOR:
            return config.OVERLAY_MARGIN
        return self.win.winfo_screenwidth() - self.width - config.OVERLAY_MARGIN

    def _y(self) -> int:
        if "bottom" in config.OVERLAY_ANCHOR:
            return self.win.winfo_screenheight() - self.height - config.OVERLAY_MARGIN
        return config.OVERLAY_MARGIN

    def _do_rong(self, font: tkfont.Font, tok: str) -> int:
        """font.measure() co cache.

        Moi lan goi measure() la mot lenh gui xuong Tcl. Mot lan ve lai co the
        can hang nghin lan do, va cuon thi ve lai lien tuc voi dung nhung tu do
        -> khong cache thi cuon giat thay ro o van ban dai.
        """
        khoa = (font.name, tok)
        w = self._cache_rong.get(khoa)
        if w is None:
            w = self._cache_rong[khoa] = font.measure(tok)
        return w

    def _cao_dong(self, font: tkfont.Font) -> int:
        """font.metrics('linespace') co cache."""
        h = self._cache_cao.get(font.name)
        if h is None:
            h = self._cache_cao[font.name] = font.metrics("linespace")
        return h

    def _build_fonts(self) -> None:
        """Tao san moi bien the font. Goi lai moi khi doi co chu."""
        self._cache_rong: dict[tuple[str, str], int] = {}
        self._cache_cao: dict[str, int] = {}
        s = self.font_size
        ff, fm = config.FONT_FAMILY, config.FONT_FAMILY_MONO
        self.f_body = tkfont.Font(family=ff, size=s)
        self.f_bold = tkfont.Font(family=ff, size=s, weight="bold")
        self.f_italic = tkfont.Font(family=ff, size=s, slant="italic")
        self.f_h1 = tkfont.Font(family=ff, size=s + 2, weight="bold")
        self.f_h2 = tkfont.Font(family=ff, size=s + 1, weight="bold")
        self.f_code = tkfont.Font(family=fm, size=max(s - 1, 6))
        self.f_status = tkfont.Font(family=ff, size=max(s - 2, 6), weight="bold")

        thuong = {"": self.f_body, "b": self.f_bold, "i": self.f_italic,
                  "c": self.f_code, "m": self.f_body}
        chi_code = dict.fromkeys(("", "b", "i", "c", "m"), self.f_code)
        self._font_sets = {
            "body": thuong,
            "bullet": thuong,
            "quote": {"": self.f_italic, "b": self.f_bold, "i": self.f_italic,
                      "c": self.f_code, "m": self.f_italic},
            "code": chi_code,
            "h1": dict.fromkeys(("", "b", "i", "m"), self.f_h1) | {"c": self.f_code},
            "h2": dict.fromkeys(("", "b", "i", "m"), self.f_h2) | {"c": self.f_code},
            "status": dict.fromkeys(("", "b", "i", "c", "m"), self.f_status),
        }
        self._colors = {
            "h1": config.COLOR_HEADING,
            "h2": config.COLOR_HEADING,
            "body": config.COLOR_TEXT,
            "bullet": config.COLOR_TEXT,
            "quote": config.COLOR_DIM,
            "code": config.COLOR_CODE,
        }

    def _apply_ex_style(self) -> None:
        """Click-through + khong hien trong Alt+Tab + khong bao gio nhan focus."""
        if sys.platform != "win32":
            return
        GWL_EXSTYLE = -20
        WS_EX_TRANSPARENT = 0x00000020
        WS_EX_TOOLWINDOW = 0x00000080
        WS_EX_LAYERED = 0x00080000
        WS_EX_NOACTIVATE = 0x08000000
        try:
            user32 = ctypes.windll.user32
            hwnd = user32.GetParent(self.win.winfo_id()) or self.win.winfo_id()
            style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            style |= (WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW
                      | WS_EX_LAYERED | WS_EX_NOACTIVATE)
            user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
        except Exception:
            pass

    # ------------------------------------------------------------- hien/an
    def show(self) -> None:
        self.win.deiconify()
        self.win.attributes("-topmost", True)
        # Dat lai style NGAY lap tuc, khong qua after(): neu cham du chi vai chuc
        # mili giay thi cua so se cuop mat trang thai hover cua ung dung ben duoi.
        self.win.update_idletasks()
        self._apply_ex_style()
        self.visible = True

    def hide(self) -> None:
        self.win.withdraw()
        self.visible = False

    def toggle(self) -> None:
        self.hide() if self.visible else self.show()

    # ------------------------------------------------------------ noi dung
    @property
    def status_text(self) -> str:
        return self._status[0]

    @property
    def plain_text(self) -> str:
        """Toan bo noi dung dang van ban tran - tien cho test va debug."""
        return "\n".join("".join(t for t, _ in runs) for _, runs, _ in self._blocks)

    def set_status(self, text: str, color: str = config.COLOR_DIM) -> None:
        self._status = (text, color)
        self.redraw()

    def set_text(self, md: str, reset_scroll: bool = True) -> None:
        self._blocks = parse_blocks(md)
        if reset_scroll:
            self.scroll_y = 0
        self.redraw()

    def clear(self) -> None:
        self._blocks = []
        self.scroll_y = 0
        self.redraw()

    # ------------------------------------------------------------- cuon/co
    def scroll_limit(self) -> int:
        """Cuon xuong duoc toi da bao nhieu pixel. 0 = noi dung vua man."""
        khung = self.height - self._content_top - config.PAD_Y
        return max(0, self.content_h - khung)

    def scroll_hint(self) -> str:
        """Chu nho ghep vao thanh trang thai, cho biet con noi dung o duoi hay khong.

        Khong co no thi khong the phan biet 'cuon hong' voi 'het chu roi'.
        """
        limit = self.scroll_limit()
        if limit <= 0:
            return ""
        if self.scroll_y <= 0:
            return "   v con nua"
        if self.scroll_y >= limit:
            return "   ^ het"
        return f"   v {round(self.scroll_y / limit * 100)}%"

    def scroll(self, delta: int) -> None:
        self.scroll_y = max(0, min(self.scroll_y + delta, self.scroll_limit()))
        self.redraw()

    def change_font_size(self, delta: int) -> None:
        new = max(config.FONT_SIZE_MIN, min(self.font_size + delta, config.FONT_SIZE_MAX))
        if new == self.font_size:
            return
        self.font_size = new
        self._build_fonts()
        self.set_status(f"Co chu: {new}", config.COLOR_DIM)

    def change_opacity(self, delta: float) -> None:
        # lam tron 2 chu so: cong don so thuc nhieu lan se troi (0.15000000000000002)
        new = round(max(config.OPACITY_MIN, min(self.opacity + delta, config.OPACITY_MAX)), 2)
        if abs(new - self.opacity) < 1e-9:
            return
        self.opacity = new
        self._apply_opacity()
        self.set_status(f"Do dam chu: {round(new * 100)}%", config.COLOR_DIM)

    # ---------------------------------------------------------------- ve
    def _layout(self, y: int, runs: list[Run], style: str, indent: int,
                mau_chinh: str) -> tuple[list[list], int]:
        """Tinh vi tri tung tu, tu xuong hang khi tran le phai.

        Tk khong tron duoc nhieu font trong mot o van ban, nen phai tu do be
        ngang tung tu roi xep. Tra ve (danh_sach_dat, y_cua_dong_ke_tiep).
        """
        fonts = self._font_sets.get(style, self._font_sets["body"])
        x0 = config.PAD_X + indent
        le_phai = max(x0 + 20, self.width - config.PAD_X)

        dat: list[list] = []
        x = x0
        cao = 0                       # chieu cao dong hien tai (font cao nhat tren dong)
        for text, kind in runs:
            font = fonts.get(kind) or fonts[""]
            if style == "code":
                mau = mau_chinh
            elif kind == "c":
                mau = config.COLOR_CODE
            elif kind == "m":
                mau = config.COLOR_MATH
            else:
                mau = mau_chinh
            rong_dong = self._cao_dong(font)
            for tok in _TOKEN_RE.findall(text):
                w = self._do_rong(font, tok)
                if x + w > le_phai and x > x0:        # tran -> xuong hang
                    x = x0
                    y += cao or rong_dong
                    cao = 0
                    if tok.isspace():
                        continue                      # khong mo dong moi bang dau cach
                cao = max(cao, rong_dong)
                dat.append([x, y, tok, font, mau])
                x += w
        if cao == 0:
            cao = self._cao_dong(fonts[""])
        return dat, y + cao + config.LINE_GAP

    def _gop(self, dat: list[list]) -> list[list]:
        """Gop cac tu lien nhau cung font/mau/dong thanh mot o van ban.

        Khong gop thi moi tu tao ra 9 doi tuong tren canvas (1 chu + 8 vien),
        mot cau tra loi dai se cham thay ro.
        """
        ra: list[list] = []
        for x, y, tok, font, mau in dat:
            if ra:
                px, py, ptok, pfont, pmau = ra[-1]
                if (py == y and pfont is font and pmau == mau
                        and abs(px + self._do_rong(pfont, ptok) - x) < 0.6):
                    ra[-1][2] = ptok + tok
                    continue
            ra.append([x, y, tok, font, mau])
        return ra

    def _ve(self, dat: list[list]) -> None:
        for x, y, tok, font, mau in self._gop(dat):
            if not tok.strip():
                continue                              # khong can ve dau cach
            if config.TEXT_OUTLINE:
                for dx, dy in _OUTLINE_OFFSETS:
                    self.canvas.create_text(x + dx, y + dy, text=tok, font=font,
                                            fill=config.OUTLINE_COLOR, anchor="nw")
            self.canvas.create_text(x, y, text=tok, font=font, fill=mau, anchor="nw")

    def _draw_runs(self, y: int, runs: list[Run], style: str, indent: int,
                   mau: str | None = None) -> int:
        mau = mau or self._colors.get(style, config.COLOR_TEXT)
        dat, y_sau = self._layout(y, runs, style, indent, mau)
        # Van phai TINH layout cho moi dong (de biet content_h chinh xac), nhung
        # chi VE nhung dong nam trong tam nhin. Ve la phan dat tien: moi doan chu
        # tao ra 9 doi tuong canvas.
        if y_sau >= 0 and y <= self.height:
            self._ve(dat)
        return y_sau

    def _draw_hr(self, y: int) -> int:
        """Duong ke ngang cho `---`. Ve them ban den lech 1px de co vien."""
        y += 5
        x1, x2 = config.PAD_X, self.width - config.PAD_X
        self.canvas.create_line(x1, y + 1, x2, y + 1, fill=config.OUTLINE_COLOR)
        self.canvas.create_line(x1, y, x2, y, fill=config.COLOR_DIM)
        return y + 7

    def redraw(self) -> None:
        self.canvas.delete("all")
        status_text, status_color = self._status

        # Chieu cao thanh trang thai do bang font chu khong bang bbox: thanh nay
        # luon dung mot dong nen so do on dinh, va ta can biet no TRUOC khi ve
        # noi dung.
        top = config.PAD_Y
        if status_text:
            top += self._cao_dong(self.f_status) + config.LINE_GAP + 2
        self._content_top = top

        # Chi phan noi dung moi cuon. Thanh trang thai duoc GHIM o tren.
        y = top - self.scroll_y
        for style, runs, indent in self._blocks:
            if style == "hr":
                y = self._draw_hr(y)
            elif not runs:                      # dong trong
                y += self._cao_dong(self.f_body) // 2
            else:
                y = self._draw_runs(y, runs, style, indent)
        self.content_h = y + self.scroll_y - top

        # Ve thanh trang thai SAU CUNG, vi hai ly do:
        #   1. scroll_hint() can content_h vua tinh xong o tren - ve truoc thi
        #      chi bao tre mot nhip (hien so cua lan ve truoc do).
        #   2. ve sau = nam tren cung, khong bi noi dung cuon len de mat.
        if status_text:
            self._draw_runs(config.PAD_Y, [(status_text + self.scroll_hint(), "")],
                            "status", 0, mau=status_color)
