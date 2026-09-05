from __future__ import annotations
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCREENSHOT_DIR = PROJECT_ROOT / "anhchup"


API_KEY = ""
MODEL = "gemini-3.6-flash"
SYSTEM_INSTRUCTION = (
    "Ban la tro ly quan sat man hinh. Nguoi dung gui anh chup man hinh. "
    "Tra loi NGAN GON, di thang van de, bang tieng Viet. "
    "Khong lan man, khong chao hoi. "
    "Neu anh co cau hoi/bai tap: dua dap an truoc, giai thich sau. "
    "Neu anh co loi (error, traceback): chi ro nguyen nhan va cach sua. "
    "Neu anh co code: neu van de chinh va cach cai thien. "
    "Khong mo ta lai giao dien neu khong duoc hoi. "
    "TUYET DOI KHONG dung LaTeX: khong dung dau $, khong \\frac, \\times, "
    "\\text, \\approx. Viet cong thuc bang ky hieu thuong tren mot dong: "
    "dung x cho nhan, / cho chia, ~= cho xap xi, ^ cho luy thua. "
    "Vi du dung: CPI = 155000 / 100000 = 1.55"
)
USER_PROMPT = "Day la bai tap hien tai cua toi."
MAX_OUTPUT_TOKENS: int | None = None
TEMPERATURE: float | None = None        # 0.0 -> 1.0
THINKING_BUDGET: int | None = None
THINKING_LEVEL: str | None = None       # "low" | "high"


PNG_LEVEL = 6                # 0-9, higher = smaller file
SAVE_SCREENSHOTS = True      # Save screenshot to SCREENSHOT_DIR/
KEEP_LAST_N = 50
HIDE_DELAY = 0.2


FONT_FAMILY = "Segoe UI"
FONT_FAMILY_MONO = "Consolas"
FONT_SIZE = 10
FONT_SIZE_MIN = 7
FONT_SIZE_MAX = 24


OVERLAY_W = 460
OVERLAY_H = 560
OVERLAY_MARGIN = 20
OVERLAY_ANCHOR = "top-right"      # top-left | bottom-right | bottom-left
PAD_X = 4
PAD_Y = 2
LINE_GAP = 2


TRANSPARENT_KEY = "#010203"

COLOR_TEXT = "#ffffff"
COLOR_HEADING = "#8ec7ff"
COLOR_CODE = "#b9f18d"
COLOR_MATH = "#ffd580"      # cong thuc toan doi tu LaTeX sang Unicode
COLOR_DIM = "#b9c0d0"
COLOR_OK = "#9ece6a"
COLOR_BUSY = "#7aa2f7"
COLOR_ERR = "#ff7a8f"
TEXT_OUTLINE = True
OUTLINE_COLOR = "#000000"
TEXT_OPACITY = 1.0
OPACITY_MIN = 0.05
OPACITY_MAX = 1.0
OPACITY_STEP = 0.05
SCROLL_STEP = 120
STREAM_REFRESH_MS = 120


HOTKEY_CAPTURE = "a+s+d"
HOTKEY_TOGGLE = "a+s+f"
HOTKEY_CANCEL = "a+s+c"
HOTKEY_QUIT = "a+s+e"
HOTKEY_SCROLL_UP = "a+s+up"
HOTKEY_SCROLL_DOWN = "a+s+down"
HOTKEY_FONT_UP = "a+s+="
HOTKEY_FONT_DOWN = "a+s+-"
HOTKEY_OPACITY_UP = "ctrl+alt+]"
HOTKEY_OPACITY_DOWN = "ctrl+alt+["
