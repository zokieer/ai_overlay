# AI Overlay

Nhấn một phím tắt để chụp màn hình, gửi cho Gemini và đọc câu trả lời hiện **trực tiếp trên màn hình** — chữ nổi trên nền trong suốt hoàn toàn, chuột xuyên qua được nên không cản trở công việc đang làm.

## Phím tắt

Các tổ hợp `A+S+…` là **giữ ba phím chữ cùng lúc**

| Phím tắt | Chức năng |
|---|---|
| `A` + `S` + `D` | Chụp toàn màn hình, lưu ảnh, gửi Gemini |
| `A` + `S` + `F` | Ẩn / hiện overlay |
| `A` + `S` + `↑` / `↓` | Cuộn nội dung |
| `A` + `S` + `=` / `-` | Tăng / giảm cỡ chữ |
| `Ctrl` + `Alt` + `]` / `[` | Tăng / giảm độ đậm chữ |
| `A` + `S` + `C` | Hủy request đang chạy |
| `A` + `S` + `E` | Thoát |

Đổi phím tắt ở cuối `src/ai_overlay/config.py` (các biến `HOTKEY_*`).

## Cài đặt

```bash
pip install -r requirements.txt
```

API key: mở `src/ai_overlay/config.py`, thay giá trị `API_KEY` (Hardcoded, thông cảm).

## Chạy

### Cách 1 — không hiện cửa sổ terminal (khuyên dùng)

Chuột phải vào **`run.pyw`** → **Open**.

Đuôi `.pyw` được Windows gắn với `pythonw.exe` — trình thông dịch này không tạo cửa sổ console. Overlay hiện lên, không có cửa sổ đen nào đi kèm.

> Nếu Windows hỏi mở bằng gì: chọn **Open with** → **Python** (`pythonw.exe`), tick **Always use this app**. Từ lần sau nháy đúp là chạy.



### Cách 2 — chạy từ terminal

```bash
python main.py
```

## Chỉnh giao diện

Sửa trong `src/ai_overlay/config.py`:

| Biến | Mặc định | Ý nghĩa |
|---|---|---|
| `FONT_SIZE` | `10` | Cỡ chữ (7–24, chỉnh nóng bằng phím tắt) |
| `FONT_FAMILY` | `"Segoe UI"` | Font chữ thường |
| `FONT_FAMILY_MONO` | `"Consolas"` | Font cho khối code |
| `OVERLAY_W` / `OVERLAY_H` | `460` / `560` | Kích thước vùng chữ |
| `OVERLAY_ANCHOR` | `"top-right"` | `"top-left"`, `"bottom-right"`, `"bottom-left"` |
| `COLOR_TEXT` | `"#ffffff"` | Màu chữ thường |
| `COLOR_HEADING` | `"#8ec7ff"` | Màu tiêu đề |
| `COLOR_CODE` | `"#b9f18d"` | Màu code |
| `COLOR_MATH` | `"#ffd580"` | Màu công thức toán |
| `TEXT_OPACITY` | `1.0` | Độ đậm chữ, `0.05`–`1.0` (chỉnh nóng bằng phím tắt) |
| `TEXT_OUTLINE` | `True` | Viền đen quanh chữ để đọc được trên mọi nền |
| `SCROLL_STEP` | `120` | Pixel mỗi lần cuộn |
| `SAVE_SCREENSHOTS` | `True` | Có lưu ảnh vào `anhchup/` không |
| `KEEP_LAST_N` | `50` | Chỉ giữ N ảnh mới nhất (`0` = giữ hết) |
| `HIDE_DELAY` | `0.2` | Giây chờ Windows vẽ lại sau khi ẩn overlay. Overlay lọt vào ảnh chụp thì tăng lên |
| `HOTKEY_*` | | Đổi phím tắt |

## Chỉnh tham số Gemini

Mặc định app **không gửi tham số sinh nội dung nào** lên API — model tự dùng mặc định của chính nó. Chỉ đặt các biến dưới đây khi bạn thực sự muốn ép một giá trị khác.

| Biến | Mặc định | Ý nghĩa khi để `None`               |
|---|---|-------------------------------------|
| `API_KEY` | *(bắt buộc)* | Thiếu thì app dừng ngay, không chạy |
| `MODEL` | `"gemini-3.6-flash"` | Chẳng lẽ ko biết                    |
| `MAX_OUTPUT_TOKENS` | `None` | Biết thì chỉnh, không thì thôi kệ   |
| `TEMPERATURE` | `None` | Biết thì chỉnh, không thì thôi kệ   |
| `THINKING_BUDGET` | `None` | Biết thì chỉnh, không thì thôi kệ   |
| `THINKING_LEVEL` | `None` | Biết thì chỉnh, không thì thôi kệ   |

## Cấu trúc

```
ai_overlay/
├── run.pyw           # chạy không terminal  ← chuột phải > Open
├── main.py           # chạy từ terminal
├── src/ai_overlay/
│   ├── config.py     # mọi thứ chỉnh được nằm đây
│   ├── capture.py    # chụp màn hình, lưu vào anhchup/
│   ├── gemini.py     # gọi API
│   ├── overlay.py    # cửa sổ chữ trong suốt
│   ├── mathfmt.py    # đổi LaTeX sang Unicode
│   └── app.py        # phím tắt, điều phối
└── anhchup/          # ảnh chụp (đã .gitignore)
```
