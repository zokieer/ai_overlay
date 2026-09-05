
from __future__ import annotations

import re


_SYMBOLS = {
    # so sanh
    "approx": "≈", "neq": "≠", "ne": "≠", "leq": "≤", "le": "≤",
    "geq": "≥", "ge": "≥", "equiv": "≡", "sim": "∼", "propto": "∝",
    "ll": "≪", "gg": "≫",
    # phep toan
    "times": "×", "div": "÷", "cdot": "·", "pm": "±", "mp": "∓",
    "ast": "∗", "star": "⋆", "circ": "∘", "bullet": "∙",
    # ky hieu lon
    "sum": "Σ", "prod": "Π", "int": "∫", "iint": "∬", "oint": "∮",
    "sqrt": "√", "partial": "∂", "nabla": "∇", "infty": "∞",
    # tap hop / logic
    "in": "∈", "notin": "∉", "subset": "⊂", "subseteq": "⊆",
    "supset": "⊃", "cup": "∪", "cap": "∩", "emptyset": "∅",
    "forall": "∀", "exists": "∃", "neg": "¬", "land": "∧", "lor": "∨",
    # mui ten
    "to": "→", "rightarrow": "→", "leftarrow": "←", "Rightarrow": "⇒",
    "Leftarrow": "⇐", "leftrightarrow": "↔", "Leftrightarrow": "⇔",
    "mapsto": "↦", "uparrow": "↑", "downarrow": "↓",
    # chu Hy Lap thuong
    "alpha": "α", "beta": "β", "gamma": "γ", "delta": "δ",
    "epsilon": "ε", "varepsilon": "ε", "zeta": "ζ", "eta": "η",
    "theta": "θ", "vartheta": "ϑ", "iota": "ι", "kappa": "κ",
    "lambda": "λ", "mu": "μ", "nu": "ν", "xi": "ξ", "pi": "π",
    "rho": "ρ", "sigma": "σ", "tau": "τ", "upsilon": "υ",
    "phi": "φ", "varphi": "φ", "chi": "χ", "psi": "ψ", "omega": "ω",
    # chu Hy Lap hoa
    "Gamma": "Γ", "Delta": "Δ", "Theta": "Θ", "Lambda": "Λ", "Xi": "Ξ",
    "Pi": "Π", "Sigma": "Σ", "Upsilon": "Υ", "Phi": "Φ", "Psi": "Ψ",
    "Omega": "Ω",
    # khac
    "ldots": "…", "dots": "…", "cdots": "⋯", "prime": "′",
    "degree": "°", "angle": "∠", "perp": "⊥", "parallel": "∥",
    "therefore": "∴", "because": "∵", "percent": "%",
}

_SUP = {"0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴", "5": "⁵",
        "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹", "+": "⁺", "-": "⁻",
        "=": "⁼", "(": "⁽", ")": "⁾", "n": "ⁿ", "i": "ⁱ", "a": "ᵃ",
        "b": "ᵇ", "c": "ᶜ", "d": "ᵈ", "e": "ᵉ", "k": "ᵏ", "m": "ᵐ",
        "t": "ᵗ", "x": "ˣ", "y": "ʸ"}

_SUB = {"0": "₀", "1": "₁", "2": "₂", "3": "₃", "4": "₄", "5": "₅",
        "6": "₆", "7": "₇", "8": "₈", "9": "₉", "+": "₊", "-": "₋",
        "=": "₌", "(": "₍", ")": "₎", "a": "ₐ", "e": "ₑ", "h": "ₕ",
        "i": "ᵢ", "j": "ⱼ", "k": "ₖ", "l": "ₗ", "m": "ₘ", "n": "ₙ",
        "o": "ₒ", "p": "ₚ", "r": "ᵣ", "s": "ₛ", "t": "ₜ", "u": "ᵤ",
        "v": "ᵥ", "x": "ₓ"}

# Lenh chi de dinh dang, bo di chi giu noi dung ben trong
_WRAPPERS = ("text", "mathrm", "mathbf", "mathit", "mathsf", "mathtt",
             "textbf", "textit", "textrm", "operatorname", "mbox", "hbox")

_SPACING = re.compile(r"\\(?:quad|qquad|,|;|:|!|\s)")
_LEFTRIGHT = re.compile(r"\\(?:left|right|big|Big|bigg|Bigg)\s*")
_CMD = re.compile(r"\\([A-Za-z]+)")


def _bo_lenh_boc(s: str) -> str:
    """\\text{abc} -> abc. Lap lai de xu ly long nhau tu trong ra ngoai."""
    mau = re.compile(r"\\(?:" + "|".join(_WRAPPERS) + r")\s*\{([^{}]*)\}")
    for _ in range(8):
        s, n = mau.subn(r"\1", s)
        if not n:
            break
    return s


def _can_ngoac(phan: str) -> str:
    """Them ngoac cho tu so/mau so neu no khong phai mot khoi lien."""
    p = phan.strip()
    if not p:
        return p
    if re.fullmatch(r"[\w.,]+", p):     # 155,000 / x / 2.5 -> khong can ngoac
        return p
    if p.startswith("(") and p.endswith(")"):
        return p
    return f"({p})"


def _doi_frac(s: str) -> str:
    """\\frac{a}{b} -> a/b. Lap lai de xu ly phan so long nhau."""
    mau = re.compile(r"\\(?:d|t)?frac\s*\{([^{}]*)\}\s*\{([^{}]*)\}")
    for _ in range(8):
        s, n = mau.subn(lambda m: f"{_can_ngoac(m.group(1))}/{_can_ngoac(m.group(2))}", s)
        if not n:
            break
    return s


def _doi_sqrt(s: str) -> str:
    mau = re.compile(r"\\sqrt\s*\{([^{}]*)\}")
    for _ in range(8):
        s, n = mau.subn(lambda m: f"√{_can_ngoac(m.group(1))}", s)
        if not n:
            break
    return s


def _chuyen_chi_so(noi_dung: str, bang: dict[str, str], dau: str) -> str:
    """Doi sang chi so tren/duoi neu MOI ky tu deu co ban Unicode.

    Neu co du mot ky tu khong doi duoc thi giu nguyen dang a^b - doi mot nua
    se ra chuoi lo cho, kho doc hon la de nguyen.
    """
    if noi_dung and all(c in bang for c in noi_dung):
        return "".join(bang[c] for c in noi_dung)
    return f"{dau}{noi_dung}" if len(noi_dung) == 1 else f"{dau}({noi_dung})"


def _doi_chi_so(s: str) -> str:
    s = re.sub(r"\^\s*\{([^{}]*)\}", lambda m: _chuyen_chi_so(m.group(1), _SUP, "^"), s)
    s = re.sub(r"_\s*\{([^{}]*)\}", lambda m: _chuyen_chi_so(m.group(1), _SUB, "_"), s)
    s = re.sub(r"\^(\w)", lambda m: _chuyen_chi_so(m.group(1), _SUP, "^"), s)
    s = re.sub(r"_(\w)", lambda m: _chuyen_chi_so(m.group(1), _SUB, "_"), s)
    return s


def convert_bare(s: str) -> str:
    """Doi lenh LaTeX lac ra NGOAI cap $...$ (model hay quen dau $).

    KHAC latex_to_unicode: khong doi chi so tren/duoi va khong bo ngoac nhon.
    Ly do: van ban thuong chua ten bien kieu file_name hay total_2, doi chi so
    se thanh fileₙₐₘₑ - hong han.
    """
    if "\\" not in s:
        return s
    s = _LEFTRIGHT.sub("", s)
    s = _bo_lenh_boc(s)
    s = _doi_frac(s)
    s = _doi_sqrt(s)
    return _CMD.sub(lambda m: _SYMBOLS.get(m.group(1), m.group(0)), s)


def latex_to_unicode(s: str) -> str:
    """Doi mot doan LaTeX thanh chu thuong doc duoc."""
    s = _LEFTRIGHT.sub("", s)
    s = _bo_lenh_boc(s)
    s = _doi_frac(s)
    s = _doi_sqrt(s)

    # \approx -> ≈ ... Chi doi lenh co trong bang, lenh la giu nguyen.
    s = _CMD.sub(lambda m: _SYMBOLS.get(m.group(1), m.group(0)), s)

    s = _doi_chi_so(s)
    s = _SPACING.sub(" ", s)
    s = s.replace("\\\\", " ").replace("\\{", "{").replace("\\}", "}")
    s = s.replace("\\%", "%").replace("\\$", "$").replace("\\&", "&")
    s = s.replace("\\_", "_").replace("\\#", "#")

    # Bo ngoac nhon con sot lai cua LaTeX (khong phai ngoac cua nguoi dung)
    s = re.sub(r"(?<!\\)[{}]", "", s)
    return re.sub(r"\s{2,}", " ", s).strip()
