"""Static UI anti-slop checker (experimental). Stdlib only, offline.

Flags mechanically detectable "AI slop" tells in CSS, HTML and JSX/TSX text. It reads text only:
it cannot see rendered pixels, judge taste, or verify contrast against images or computed styles.
A clean result means none of these patterns matched, not that the UI is good.
"""
import re
from pathlib import Path

SEV = ("critical", "high", "medium")
EXTS = {".css", ".scss", ".html", ".htm", ".jsx", ".tsx", ".js", ".ts", ".vue", ".svelte"}
PURPLE = r"(?:purple|indigo|violet|#(?:6366f1|8b5cf6|a855f7|7c3aed|6d28d9|4f46e5|9333ea|c084fc|818cf8))"
BLOCK = re.compile(r"([^{}@][^{}]*)\{([^{}]*)\}")


def _px(v, unit):
    v = float(v)
    return v * 16 if unit == "rem" or unit == "em" else v


def _hex(c):
    c = c.lstrip("#")
    if len(c) == 3:
        c = "".join(x * 2 for x in c)
    return tuple(int(c[i:i + 2], 16) / 255 for i in (0, 2, 4))


def _lum(rgb):
    f = lambda x: x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4
    r, g, b = map(f, rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(fg, bg):
    a, b = sorted((_lum(_hex(fg)), _lum(_hex(bg))), reverse=True)
    return (a + 0.05) / (b + 0.05)


def _line(text, pos):
    return text.count("\n", 0, pos) + 1


def _decl(body, prop):
    m = re.search(r"(?:^|;|\s)" + re.escape(prop) + r"\s*:\s*([^;]+)", body, re.I)
    return m.group(1).strip() if m else None


def _css_rules(text, add):
    for m in BLOCK.finditer(text):
        sel, body = m.group(1).strip(), m.group(2)
        ln = _line(text, m.start())
        ff = _decl(body, "font-family")
        if ff:
            first = ff.split(",")[0].strip().strip("'\"").lower()
            if first in ("inter", "roboto", "arial", "system-ui", "-apple-system", "helvetica", "helvetica neue"):
                add("high", "default-font-as-brand", ln, f"{sel}: font-family starts with {first}")
        if re.search(r"background-clip\s*:\s*text|-webkit-background-clip\s*:\s*text", body, re.I) and re.search(r"gradient", body, re.I):
            add("critical", "gradient-text", ln, f"{sel}: gradient text")
        for side in ("left", "right"):
            v = _decl(body, f"border-{side}")
            w = _decl(body, f"border-{side}-width")
            val = v or w
            if val:
                mm = re.match(r"(\d+(?:\.\d+)?)(px|rem|em)", val)
                if mm and _px(mm.group(1), mm.group(2)) > 1 and "none" not in val:
                    add("critical", "side-stripe-border", ln, f"{sel}: border-{side} {val}")
        for g in re.finditer(r"(?:linear|radial|conic)-gradient\([^;]*", body, re.I):
            if re.search(PURPLE, g.group(0), re.I):
                add("high", "purple-gradient", ln, f"{sel}: purple/indigo gradient")
                break
        if re.search(r"backdrop-filter\s*:\s*[^;]*blur|-webkit-backdrop-filter\s*:\s*[^;]*blur", body, re.I):
            add("medium", "glassmorphism", ln, f"{sel}: backdrop-filter blur (fine only if it materially helps)")
        br = _decl(body, "border-radius")
        if br:
            for mm in re.finditer(r"(\d+(?:\.\d+)?)(px|rem|em)", br):
                if _px(mm.group(1), mm.group(2)) >= 24 and _px(mm.group(1), mm.group(2)) < 999:
                    add("high", "large-radius", ln, f"{sel}: border-radius {br}; pill radius only for tags/buttons")
                    break
        bd, sh = _decl(body, "border"), _decl(body, "box-shadow")
        if bd and sh and not re.match(r"(none|0)", bd) and re.match(r"\s*1px", bd):
            for s in re.split(r",(?![^()]*\))", sh):
                nums = re.findall(r"(?<![\w#.])(-?\d*\.?\d+)(?:px)?(?![\w%.])", re.sub(r"(?:rgba?|hsla?)\([^)]*\)", "", s))
                if len(nums) >= 3 and float(nums[2]) >= 16:
                    add("high", "ghost-card", ln, f"{sel}: 1px border plus {nums[2]}px blur shadow")
                    break
        z = _decl(body, "z-index")
        if z and re.match(r"\d{3,}", z) and int(re.match(r"\d+", z).group(0)) >= 999:
            add("medium", "z-index-soup", ln, f"{sel}: z-index {z}")
        ls = _decl(body, "letter-spacing")
        if ls:
            mm = re.match(r"(-\d*\.?\d+)em", ls)
            if mm and float(mm.group(1)) < -0.04:
                add("medium", "tight-tracking", ln, f"{sel}: letter-spacing {ls} below -0.04em")
        fs = _decl(body, "font-size")
        if fs and "clamp(" in fs:
            vals = re.findall(r"(\d+(?:\.\d+)?)(px|rem)", fs)
            if vals and _px(*vals[-1]) > 96:
                add("medium", "display-too-large", ln, f"{sel}: clamp max {vals[-1][0]}{vals[-1][1]} exceeds 6rem")
        for prop in ("transition", "animation", "transition-timing-function", "animation-timing-function"):
            v = _decl(body, prop)
            if v:
                if re.search(r"bounce|elastic", v, re.I):
                    add("high", "bounce-easing", ln, f"{sel}: {prop} {v}")
                for cb in re.finditer(r"cubic-bezier\(([^)]*)\)", v):
                    p = [x.strip() for x in cb.group(1).split(",")]
                    try:
                        if len(p) == 4 and (float(p[1]) > 1.0 or float(p[3]) > 1.0 or float(p[1]) < -0.0001):
                            add("high", "bounce-easing", ln, f"{sel}: overshooting cubic-bezier({cb.group(1)})")
                    except ValueError:
                        pass
        if re.search(r"(?:^|[\s>,.])(?:\.group:hover\s+)?img[^,{]*:hover|:hover\s+img", sel) and re.search(r"transform\s*:[^;]*scale", body, re.I):
            add("high", "hover-scale-image", ln, f"{sel}: image scaled on hover")
        if re.search(r"text-transform\s*:\s*uppercase", body, re.I) and ls and re.match(r"0?\.(?:[1-9])\d*em|\d+px", ls):
            add("medium", "eyebrow-kicker", ln, f"{sel}: tiny uppercase tracked label (ok as one brand system, not above every section)")
        color, bg = _decl(body, "color"), _decl(body, "background") or _decl(body, "background-color")
        if color and bg and re.fullmatch(r"#[0-9a-fA-F]{3}|#[0-9a-fA-F]{6}", color) and re.fullmatch(r"#[0-9a-fA-F]{3}|#[0-9a-fA-F]{6}", bg):
            c = contrast(color, bg)
            if c < 4.5:
                add("high", "low-contrast", ln, f"{sel}: {color} on {bg} is {c:.2f}:1 (needs 4.5:1 for body text, 3:1 for large)")


TW = [
    (r"bg-clip-text", "critical", "gradient-text", "Tailwind bg-clip-text (check for gradient)"),
    (r"\bborder-[lr]-(?:[2-9]|\d{2,})\b", "critical", "side-stripe-border", "Tailwind side border wider than 1px"),
    (r"\brounded-(?:3xl|\[(?:2[4-9]|[3-9]\d)px\])", "high", "large-radius", "Tailwind radius 24px or more"),
    (r"\b(?:from|via|to)-(?:purple|indigo|violet)-\d+", "high", "purple-gradient", "Tailwind purple/indigo gradient stop"),
    (r"\banimate-bounce\b", "high", "bounce-easing", "Tailwind animate-bounce"),
    (r"\bz-\[(?:9{3,}|\d{4,})\]", "medium", "z-index-soup", "Tailwind arbitrary huge z-index"),
    (r"\bbackdrop-blur", "medium", "glassmorphism", "Tailwind backdrop-blur (fine only if it materially helps)"),
    (r"\bgroup-hover:scale-|\bhover:scale-", "medium", "hover-scale", "hover scale (never on <img>; animate card bg/border/shadow)"),
    (r"\bfont-(?:sans)\b.*\bInter\b|font-\[(?:'|\")?Inter", "high", "default-font-as-brand", "Inter as brand face"),
]


def check_text(text, name="<text>"):
    found = []
    text = re.sub(r"/\*.*?\*/", lambda m: re.sub(r"[^\n]", " ", m.group(0)), text, flags=re.S)

    def add(sev, rule, line, msg):
        found.append({"severity": sev, "rule": rule, "file": name, "line": line, "message": msg})

    _css_rules(text, add)
    for pat, sev, rule, msg in TW:
        for m in re.finditer(pat, text):
            add(sev, rule, _line(text, m.start()), msg)
    if re.search(r"@keyframes|animation\s*:|transition\s*:|animate-", text) and not re.search(r"prefers-reduced-motion|motion-reduce|motion-safe", text):
        add("medium", "no-reduced-motion", 1, "animation present with no prefers-reduced-motion alternative in this file")
    seen, out = set(), []
    for f in found:
        k = (f["rule"], f["line"], f["message"])
        if k not in seen:
            seen.add(k); out.append(f)
    return sorted(out, key=lambda f: (SEV.index(f["severity"]), f["file"], f["line"]))


def check_path(path):
    p = Path(path)
    files = [p] if p.is_file() else sorted(x for x in p.rglob("*") if x.is_file() and x.suffix in EXTS
                                          and not any(s in x.parts for s in ("node_modules", ".git", "dist", "build", "third_party")))
    res = []
    for f in files:
        res += check_text(f.read_text(encoding="utf-8", errors="replace"), str(f))
    return res, len(files)
