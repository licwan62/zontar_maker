"""Locked Ozon main-image typography master: "灰色无耳首图 固定排版母版".

Spec: data/backgrounds/05_灰色无耳首图_固定排版母版提示词.md
Style reference: assets/archive/samples/首图模板.png (LADA PRIORA, 1086 × 1448)

Every box below was measured from the reference image and is part of the template:
positions, cap heights, panel shapes and the footer structure never move. Per vehicle only
``HeroFields`` change; per background only the text palette changes (``palette_for``).
The model name and the Russian strip are squeezed narrower to fit their width limit; a
model name too long even at MODEL_MIN_SQUEEZE drops cap height (reported) but stays the
largest line on the page.
"""
from __future__ import annotations

from dataclasses import dataclass

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageStat

from . import layout
from .render import FONT_DIR, H, W, cover

ORANGE = (253, 87, 1)
NAVY = (3, 37, 67)
PANEL = (4, 24, 42)
WHITE = (255, 255, 255)
MUTED = (222, 228, 234)

HEAVY = "ariblk.ttf"      # heading, headline, strip, years, code (narrowed per element below)
CONDENSED = "impact.ttf"  # small lines: support line, footer labels
TEXT = "arial.ttf"        # footer disclaimer

# (x, top-of-caps y, cap height, max width, horizontal squeeze) measured from the reference;
# squeeze narrows Arial Black to the reference glyph widths.
HEADING = (53, 63, 42, 290, 0.70)
HEADING_RULE = (17, 97, 107, 7)         # gap after heading, top y, length, thickness
MODEL = (52, 140, 126, 982, 0.57)
MODEL_MIN_SQUEEZE = 0.50                 # below this, long names lose cap height instead
STRIP = (51, 293, 605, 357)              # min width; grows with the text up to STRIP_MAX_RIGHT
STRIP_MAX_RIGHT = 1034
STRIP_TEXT = (72, 310, 36, None, 0.75)   # x = STRIP left + 21, vertically centred in STRIP
YEARS = (53, 375, 38, 560, 0.87)
BADGE = (49, 438, 380, 591)
BADGE_LABEL = (75, 467, 46, 100, 0.60)
BADGE_CODE = (181, 436, 105, 186, 0.74)  # "КОД" + code are centred as one group in BADGE
SUPPORT = (54, 604, 26, 330, 1.0)
LOGO = (768, 25, 273)                    # x, y, width
FOOTER = (36, 1213, 1050, 1408)
FOOTER_ROW = (1246, 1321)                # icon/label band; separators span it
FOOTER_ICON_H = 68
FOOTER_ICON_W = 70
FOOTER_LABEL_CAP = 22
FOOTER_LABEL_SQUEEZE = 0.92
FOOTER_COL_PAD = 12                      # min inner padding per column
FOOTER_LABEL_GAP = 30                    # baseline-to-baseline of the two label lines
DISCLAIMER = (1343, 1373, 21)            # line 1 top, line 2 top, font size

FUNCTIONS = (("ЗАЩИТА", "ОТ ДОЖДЯ"), ("ЗАЩИТА", "ОТ СНЕГА"),
             ("ЗАЩИТА", "ОТ СОЛНЦА"), ("ВСЕСЕЗОННЫЙ", "ЧЕХОЛ"))
DISCLAIMER_LINES = ("Материалы принадлежат бренду Tozaroa.",
                    "За товары сторонних продавцов бренд ответственности не несёт.")


@dataclass(frozen=True)
class HeroFields:
    model_latin: str      # {MODEL_LATIN}      e.g. "LADA PRIORA"
    model_ru_search: str  # {MODEL_RU_SEARCH}  e.g. "ЛАДА ПРИОРА"
    body_ru: str          # {BODY_RU}          e.g. "СЕДАН"
    years: str            # {YEARS}            e.g. "2007–2018"
    size_code: str        # {SIZE_CODE}        e.g. "3M"


@dataclass(frozen=True)
class Palette:
    name: str
    text: tuple[int, int, int]
    halo: tuple[int, int, int, int]  # soft shadow (dark bg) or glow (light bg) behind free text
    logo_outline: tuple[int, int, int, int] | None
    accent: tuple[int, int, int]
    panel: tuple[int, int, int]


MIDNIGHT_ORANGE = Palette("midnight_orange", WHITE, (0, 0, 0, 195),
                          (255, 255, 255, 170), ORANGE, PANEL)
ARCTIC_BLUE = Palette("arctic_blue", NAVY, (255, 255, 255, 235),
                      None, (0, 105, 210), (2, 31, 57))
FOREST_GOLD = Palette("forest_gold", (22, 54, 45), (255, 250, 235, 235),
                      None, (210, 139, 22), (20, 49, 42))

PALETTES = {palette.name: palette for palette in (MIDNIGHT_ORANGE, ARCTIC_BLUE, FOREST_GOLD)}
# Compatibility aliases for callers that imported the old two-state names.
DARK_BG = MIDNIGHT_ORANGE
LIGHT_BG = ARCTIC_BLUE


def palette_for(background: Image.Image) -> Palette:
    """Choose among dark, cold-light and warm-light palettes without moving the layout."""
    header = background.convert("RGB").crop((0, 40, 820, 610))
    red, green, blue = ImageStat.Stat(header).mean
    luminance = 0.2126 * red + 0.7152 * green + 0.0722 * blue
    if luminance <= 150:
        return MIDNIGHT_ORANGE
    return FOREST_GOLD if red - blue > 12 else ARCTIC_BLUE


def palette_by_name(name: str) -> Palette:
    """Return a stable named theme for deliberate art direction."""
    try:
        return PALETTES[name]
    except KeyError as exc:
        raise ValueError(f"unknown hero palette {name!r}; choose from {', '.join(PALETTES)}") from exc


def _font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_DIR / name), size)


def _cap_size(name: str, cap: int) -> int:
    """Font size whose capital 'H' is `cap` px tall."""
    probe = 200
    box = _font(name, probe).getbbox("H")
    return max(6, round(probe * cap / (box[3] - box[1])))


def _text(text: str, font: str, cap: int, fill, squeeze: float = 1.0, max_width: int | None = None) -> Image.Image:
    """Tight RGBA layer: caps exactly `cap` px tall, width squeezed and capped at max_width."""
    f = _font(font, _cap_size(font, cap))
    cap_top = f.getbbox("H")[1]
    box = f.getbbox(text)
    layer = Image.new("RGBA", (box[2] - box[0] + 4, f.getbbox("HЙ,")[3] - cap_top + 4), (0, 0, 0, 0))
    ImageDraw.Draw(layer).text((2 - box[0], 2 - cap_top), text, font=f, fill=fill)
    layer = layer.crop((0, 0, layer.width, layer.height))
    width = layer.width * squeeze
    if max_width and width > max_width:
        width = max_width
    if round(width) != layer.width:
        layer = layer.resize((max(1, round(width)), layer.height), Image.Resampling.LANCZOS)
    return layer  # (2, 2) in the layer is the cap-top-left anchor


def _place(canvas: Image.Image, layer: Image.Image, x: int, cap_top: int, halo=None) -> tuple[int, int, int, int]:
    x, y = x - 2, cap_top - 2
    if halo:
        # The halo must expand beyond the tight glyph layer. Filtering the original
        # alpha directly clips the blur at all four layer edges and creates hard boxes.
        pad = 18
        a = Image.new("L", (layer.width + pad * 2, layer.height + pad * 2), 0)
        a.paste(layer.getchannel("A"), (pad, pad))
        a = a.filter(ImageFilter.MaxFilter(7)).filter(ImageFilter.GaussianBlur(5))
        shadow = Image.new("RGBA", a.size, halo[:3] + (0,))
        shadow.putalpha(a.point(lambda v: v * halo[3] // 255))
        canvas.alpha_composite(shadow, (x + 2 - pad, y + 4 - pad))
    canvas.alpha_composite(layer, (x, y))
    return (x, y, x + layer.width, y + layer.height)


def _panel(canvas, box, radius, fill, border=None, border_width=0):
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).rounded_rectangle(box, radius=radius, fill=fill, outline=border, width=border_width)
    canvas.alpha_composite(layer)


def _logo(canvas: Image.Image, palette: Palette) -> None:
    """Original transparent logo, no card. Dark backgrounds get only a thin soft outline."""
    x, y, width = LOGO
    path = layout.brand_logo()
    if not path.exists():
        _place(canvas, _text("Tozaroa", HEAVY, 52, palette.text), x, y + 10, palette.halo)
        return
    logo = Image.open(path).convert("RGBA")
    logo = logo.crop(logo.getchannel("A").point(lambda v: 255 if v > 45 else 0).getbbox())
    logo = logo.resize((width, round(width * logo.height / logo.width)), Image.Resampling.LANCZOS)
    if palette.logo_outline:
        pad = 8
        a = Image.new("L", (logo.width + 2 * pad, logo.height + 2 * pad), 0)
        a.paste(logo.getchannel("A"), (pad, pad))
        a = a.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(2.5))
        outline = Image.new("RGBA", a.size, palette.logo_outline[:3] + (0,))
        outline.putalpha(a.point(lambda v: v * palette.logo_outline[3] // 255))
        canvas.alpha_composite(outline, (x - pad, y - pad))
    canvas.alpha_composite(logo, (x, y))


def _icons() -> list[Image.Image]:
    sprite = Image.open(layout.brand_icons()).convert("RGBA")
    out = []
    for i in range(4):
        icon = sprite.crop((round(sprite.width * i / 4), 0, round(sprite.width * (i + 1) / 4), sprite.height))
        icon = icon.crop(icon.getchannel("A").point(lambda v: 255 if v > 70 else 0).getbbox())
        scale = min(FOOTER_ICON_H / icon.height, FOOTER_ICON_W / icon.width)
        out.append(icon.resize((round(icon.width * scale), round(icon.height * scale)), Image.Resampling.LANCZOS))
    return out


def _footer(canvas: Image.Image, palette: Palette) -> list[tuple[str, tuple]]:
    boxes = []
    _panel(canvas, FOOTER, 28, palette.panel + (238,), palette.accent, 4)
    x0, x1 = FOOTER[0] + 4, FOOTER[2] - 4
    top, bottom = FOOTER_ROW
    col = (x1 - x0) / 4
    dr = ImageDraw.Draw(canvas)
    for i, (icon, lines) in enumerate(zip(_icons(), FUNCTIONS)):
        if i:
            sx = round(x0 + col * i)
            dr.line((sx, top, sx, bottom), fill=(255, 255, 255, 200), width=2)
        gap = 16
        room = col - icon.width - gap - 2 * FOOTER_COL_PAD
        natural = max(_text(t, CONDENSED, FOOTER_LABEL_CAP, WHITE).width - 4 for t in lines)
        squeeze = min(FOOTER_LABEL_SQUEEZE, room / natural)
        labels = [_text(t, CONDENSED, FOOTER_LABEL_CAP, WHITE, squeeze) for t in lines]
        label_w = max(l.width for l in labels) - 4
        group = icon.width + gap + label_w
        gx = round(x0 + col * i + (col - group) / 2)
        cy = (top + bottom) / 2
        canvas.alpha_composite(icon, (gx, round(cy - icon.height / 2)))
        label_top = round(cy - (FOOTER_LABEL_GAP + FOOTER_LABEL_CAP) / 2)
        for j, label in enumerate(labels):
            boxes.append((f"footer_{i}_{j}", _place(canvas, label, gx + icon.width + gap, label_top + j * FOOTER_LABEL_GAP)))
    f = _font(TEXT, DISCLAIMER[2])
    for line, y in zip(DISCLAIMER_LINES, DISCLAIMER[:2]):
        w = dr.textlength(line, font=f)
        dr.text(((W - w) / 2, y), line, font=f, fill=MUTED)
    return boxes


def render_hero(background: Image.Image, fields: HeroFields, palette: Palette | None = None) -> tuple[Image.Image, dict]:
    """Draw the locked template over a 3:4 background (scene, or scene with composited car).

    Returns the RGB image and a small report (palette, element boxes, squeeze factors).
    """
    canvas = cover(background.convert("RGB"), W, H).convert("RGBA")
    palette = palette or palette_for(canvas)
    boxes: dict[str, tuple] = {}

    x, y, cap, maxw, sq = HEADING
    boxes["heading"] = _place(canvas, _text("ЧЕХОЛ ДЛЯ", HEAVY, cap, palette.text, sq, maxw), x, y, palette.halo)
    gap, top, length, thick = HEADING_RULE
    rx = boxes["heading"][2] - 2 + gap
    ImageDraw.Draw(canvas).rectangle((rx, top, rx + length, top + thick - 1), fill=palette.accent)

    x, y, cap, maxw, sq = MODEL
    natural = _text(fields.model_latin.upper(), HEAVY, cap, palette.text).width - 4
    model_cap = cap if natural * MODEL_MIN_SQUEEZE <= maxw else max(60, int(cap * maxw / (natural * MODEL_MIN_SQUEEZE)))
    model = _text(fields.model_latin.upper(), HEAVY, model_cap, palette.text, sq, maxw)
    boxes["model"] = _place(canvas, model, x, y + (cap - model_cap) // 2, palette.halo)

    x, y, cap, _, sq = STRIP_TEXT
    strip_text = _text(f"{fields.model_ru_search} • {fields.body_ru}".upper(), HEAVY, cap, WHITE, sq,
                       STRIP_MAX_RIGHT - STRIP[0] - 2 * (x - STRIP[0]))
    right = max(STRIP[2], STRIP[0] + 2 * (x - STRIP[0]) + strip_text.width - 4)
    _panel(canvas, (STRIP[0], STRIP[1], right, STRIP[3]), 14, palette.accent + (255,))
    boxes["strip"] = (STRIP[0], STRIP[1], right, STRIP[3])
    strip_cy = (STRIP[1] + STRIP[3]) / 2
    _place(canvas, strip_text, x, round(strip_cy - cap / 2))

    x, y, cap, maxw, sq = YEARS
    boxes["years"] = _place(canvas, _text(fields.years, HEAVY, cap, palette.text, sq, maxw), x, y, palette.halo)

    _panel(canvas, BADGE, 28, palette.panel + (235,), palette.accent, 5)
    boxes["badge"] = BADGE
    lx, _, lcap, lmax, lsq = BADGE_LABEL
    cx, _, ccap, cmax, csq = BADGE_CODE
    label = _text("КОД", HEAVY, lcap, WHITE, lsq, lmax)
    code = _text(fields.size_code.upper(), HEAVY, ccap, palette.accent, csq, cmax)
    gap = cx - lx - (label.width - 4)
    group = label.width - 4 + gap + code.width - 4
    gx = round((BADGE[0] + BADGE[2] - group) / 2)
    bcy = (BADGE[1] + BADGE[3]) / 2
    _place(canvas, label, gx, round(bcy - lcap / 2))
    boxes["code"] = _place(canvas, code, gx + label.width - 4 + gap, round(bcy - ccap / 2))

    x, y, cap, maxw, sq = SUPPORT
    boxes["support"] = _place(canvas, _text("ИНДИВИДУАЛЬНЫЙ ПОДБОР", CONDENSED, cap, palette.text, sq, maxw), x, y, palette.halo)

    _logo(canvas, palette)
    boxes["logo"] = (LOGO[0], LOGO[1], LOGO[0] + LOGO[2], LOGO[1] + 80)
    boxes.update(_footer(canvas, palette))

    report = {
        "palette": palette.name,
        "model_width": model.width - 4,
        "model_cap": model_cap,
        "model_squeeze": round((model.width - 4) / (natural * model_cap / MODEL[2]), 3),
        "boxes": {k: list(v) for k, v in boxes.items()},
    }
    return canvas.convert("RGB"), report
