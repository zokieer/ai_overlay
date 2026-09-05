from __future__ import annotations
from typing import Iterator
from google import genai
from google.genai import types
from . import config


class Gemini:
    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.model = model or config.MODEL
        self.client = genai.Client(api_key=api_key or config.API_KEY)

    def _config(self) -> types.GenerateContentConfig:
        kwargs: dict = {"system_instruction": config.SYSTEM_INSTRUCTION}

        if config.MAX_OUTPUT_TOKENS is not None:
            kwargs["max_output_tokens"] = config.MAX_OUTPUT_TOKENS
        if config.TEMPERATURE is not None:
            kwargs["temperature"] = config.TEMPERATURE
        if config.THINKING_BUDGET is not None:
            kwargs["thinking_config"] = types.ThinkingConfig(
                thinking_budget=config.THINKING_BUDGET
            )
        elif config.THINKING_LEVEL:
            kwargs["thinking_config"] = types.ThinkingConfig(
                thinking_level = config.THINKING_LEVEL
            )

        return types.GenerateContentConfig(**kwargs)

    def _contents(self, png: bytes, prompt: str | None) -> list:
        return [
            types.Part.from_bytes(data=png, mime_type="image/png"),
            prompt or config.USER_PROMPT,
        ]

    def generate(self, png: bytes, prompt: str | None = None) -> tuple[str, str]:

        resp = self.client.models.generate_content(
            model=self.model,
            contents=self._contents(png, prompt),
            config=self._config(),
        )
        text = (getattr(resp, "text", None) or "").strip()
        return text, finish_warning(resp, text)

    def stream(self, png: bytes, prompt: str | None = None) -> Iterator[str]:
        """Yield tung doan text tra ve. Giu lai phong khi can dung lai."""
        for chunk in self.client.models.generate_content_stream(
            model=self.model,
            contents=self._contents(png, prompt),
            config=self._config(),
        ):
            text = getattr(chunk, "text", None)
            if text:
                yield text


_FINISH_NOTES = {
    "MAX_TOKENS": ("Cau tra loi bi CAT vi cham gioi han token cua model.\n"
                   "App khong dat gioi han rieng; neu van bi cat, dat "
                   "MAX_OUTPUT_TOKENS trong config.py de ep cao hon, hoac chon "
                   "model co han muc dau ra lon hon."),
    "SAFETY": "Cau tra loi bi bo loc an toan chan lai.",
    "RECITATION": "Bi chan vi trung lap noi dung co ban quyen.",
    "PROHIBITED_CONTENT": "Noi dung bi cam, API tu choi tra loi.",
    "BLOCKLIST": "Noi dung nam trong danh sach chan.",
    "SPII": "Anh co the chua thong tin ca nhan nhay cam nen bi chan.",
}


def finish_warning(resp, text: str) -> str:
    try:
        reason = resp.candidates[0].finish_reason
    except (AttributeError, IndexError, TypeError):
        return "" if text else "API khong tra ve noi dung nao."

    name = getattr(reason, "name", None) or str(reason or "")
    if name in ("STOP", "FINISH_REASON_UNSPECIFIED", "None", ""):
        return "" if text else "API tra ve cau tra loi rong."
    return _FINISH_NOTES.get(name, f"Ket thuc bat thuong: {name}")


def explain_error(exc: Exception, model: str) -> str:
    msg = str(exc).lower()
    if "not found" in msg or "404" in msg:
        return (f"Model '{model}' khong ton tai hoac tai khoan chua duoc bat.\n"
                f"Sua bien MODEL trong config.py.")
    if "api key" in msg or "401" in msg or "unauthenticated" in msg or "permission" in msg:
        return "API key sai hoac khong co quyen. Kiem tra API_KEY trong local_config.py."
    if "429" in msg or "quota" in msg or "resource_exhausted" in msg:
        return "Het quota hoac bi gioi han toc do. Cho mot lat roi thu lai."
    if "deadline" in msg or "timeout" in msg or "connect" in msg:
        return "Khong ket noi duoc toi API. Kiem tra mang."
    return ""
