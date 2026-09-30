"""Data-driven renderer for per-vehicle SKU images (main / fitment / selector / contact sheet).

Layouts are the parametric form of the delivered Renault Logan / Land Cruiser designs,
so a new vehicle needs only data (data/vehicles/<slug>/inputs/skus.csv) plus source photos
(assets/inputs/vehicles/<slug>/source/base_<SKU>.png). When a source photo or the brand
logo is missing, a neutral placeholder is used and every affected image gets a DRAFT
watermark so it cannot be mistaken for a deliverable.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from . import layout, themes

W, H = 1086, 1448
NAVY, ORANGE, WHITE = (3, 37, 67), (232, 71, 5), (255, 255, 255)
PALE = (244, 248, 251)
FONT_DIR = Path(os.environ.get("ZONTAR_FONT_DIR") or Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts")


def condensed(size): return ImageFont.truetype(str(FONT_DIR / "impact.ttf"), size)
def bold(size): return ImageFont.truetype(str(FONT_DIR / "arialbd.ttf"), size)
def regular(size): return ImageFont.truetype(str(FONT_DIR / "arial.ttf"), size)


def fit(draw, text, width, start, minimum=18, condensed_font=True):
    make = condensed if condensed_font else bold
    for size in range(start, minimum, -1):
        f = make(size)
        if draw.textbbox((0, 0), text, font=f)[2] <= width:
            return f
    return make(minimum)


def cover(image, width, height, focus=0.5):
    scale = max(width / image.width, height / image.height)
    resized = image.resize((round(image.width * scale), round(image.height * scale)), Image.Resampling.LANCZOS)
    left = max(0, (resized.width - width) // 2)
    top = max(0, min(resized.height - height, round((resized.height - height) * focus)))
    return resized.crop((left, top, left + width, top + height))


@dataclass
class Sku:
    code: str
    ship_size: str
    body: str
    years: str
    cards: list[tuple[str, str]]
    base_image: str
    vehicle_image: str | None = None


@dataclass
class Job:
    brand: str
    title: str                 # e.g. "VOLKSWAGEN TIGUAN"
    file_prefix: str           # e.g. "VW_Tiguan"
    subtitle: tuple[str, str]  # two Russian lines next to the SIZE box
    skus: list[Sku]
    style: str = "land_cruiser"
    layout_style: str | None = None  # deprecated compatibility alias; prefer `style`
    main_title_lines: tuple[str, str] | None = None  # optional larger two-line main-image heading
    drafts: list[str] = field(default_factory=list)
    layout_audits: dict[str, dict] = field(default_factory=dict)


# --- inputs with fallbacks ---------------------------------------------------------
def _logo(job: Job):
    p = layout.brand_logo()
    if p.exists():
        logo = Image.open(p).convert("RGBA")
        alpha = logo.getchannel("A").point(lambda v: 255 if v > 45 else 0)
        return logo.crop(alpha.getbbox())
    job.drafts.append("brand logo missing: text wordmark used")
    return None


def add_logo(job: Job, logo, image, x, y, width):
    if logo is None:
        d = ImageDraw.Draw(image)
        f = fit(d, job.brand, width, 64, 20, condensed_font=False)
        d.text((x, y + 8), job.brand, font=f, fill=NAVY)
        return
    lg = logo.resize((width, round(width * logo.height / logo.width)), Image.Resampling.LANCZOS)
    px = lg.load()
    for yy in range(lg.height):
        for xx in range(lg.width):
            r, g, b, a = px[xx, yy]
            if not a:
                continue
            if max(r, g, b) < 110:
                px[xx, yy] = (10, 20, 28, a)
            elif b > r * 1.3:
                px[xx, yy] = (32, 120, 222, a)
    image.alpha_composite(lg, (x, y))


def add_logo_light(job: Job, logo, image, x, y, width):
    """White/blue logo treatment for dark photographic themes."""
    if logo is None:
        d = ImageDraw.Draw(image)
        f = fit(d, job.brand, width, 64, 20, condensed_font=False)
        d.text((x, y + 8), job.brand, font=f, fill=WHITE)
        return
    lg = logo.resize((width, round(width * logo.height / logo.width)), Image.Resampling.LANCZOS)
    px = lg.load()
    for yy in range(lg.height):
        for xx in range(lg.width):
            r, g, b, a = px[xx, yy]
            if not a:
                continue
            if max(r, g, b) < 110:
                px[xx, yy] = (255, 255, 255, a)
            elif b > r * 1.3:
                px[xx, yy] = (90, 177, 255, a)
    image.alpha_composite(lg, (x, y))


def _placeholder(label: str) -> Image.Image:
    im = Image.new("RGB", (W, H), (214, 222, 229))
    d = ImageDraw.Draw(im)
    for y in range(H):
        t = y / H
        d.line((0, y, W, y), fill=(round(226 - 60 * t), round(232 - 55 * t), round(238 - 50 * t)))
    # generic covered-SUV silhouette
    d.rounded_rectangle((120, 700, 980, 1060), radius=90, fill=(150, 156, 162))
    d.rounded_rectangle((250, 560, 860, 760), radius=70, fill=(158, 164, 170))
    for cx in (300, 800):
        d.ellipse((cx - 85, 990, cx + 85, 1160), fill=(40, 44, 48))
    d.text((W // 2, 1180), "ИСХОДНОЕ ФОТО НЕ ГОТОВО", font=bold(40), fill=(70, 80, 90), anchor="mm")
    d.text((W // 2, 1230), label, font=regular(30), fill=(70, 80, 90), anchor="mm")
    return im


def source_photo(job: Job, v: layout.Vehicle, name: str) -> Image.Image:
    p = v.source / name
    if p.exists():
        return Image.open(p).convert("RGB")
    job.drafts.append(f"source photo missing: {name}")
    return _placeholder(f"source/{name}")


def vehicle_photo(job: Job, v: layout.Vehicle, sku: Sku) -> Image.Image:
    """Use the optional clean vehicle image, falling back to the SKU base scene."""
    name = sku.vehicle_image or sku.base_image
    path = v.source / name
    if path.exists():
        image = Image.open(path)
        return image.convert("RGBA") if "A" in image.getbands() else image.convert("RGB")
    return source_photo(job, v, name)


def watermark(image: Image.Image) -> Image.Image:
    layer = Image.new("RGBA", (W * 2, H * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    f = condensed(120)
    for y in range(0, H * 2, 330):
        for x in range(-200, W * 2, 620):
            d.text((x, y), "DRAFT", font=f, fill=(232, 71, 5, 70))
    layer = layer.rotate(30, resample=Image.Resampling.BICUBIC).crop((W // 2, H // 2, W // 2 + W, H // 2 + H))
    out = image.convert("RGBA")
    out.alpha_composite(layer)
    return out


def _icons():
    sprite = Image.open(layout.brand_icons()).convert("RGBA")
    icons = []
    for i in range(4):
        icon = sprite.crop((round(sprite.width * i / 4), 0, round(sprite.width * (i + 1) / 4), sprite.height))
        a = icon.getchannel("A").point(lambda v: 255 if v > 70 else 0)
        icons.append(icon.crop(a.getbbox()))
    return icons


def _check(dr, cx, cy, r=21):
    dr.ellipse((cx - r, cy - r, cx + r, cy + r), fill=NAVY)
    dr.line((cx - 10, cy, cx, cy + 10), fill=WHITE, width=5)
    dr.line((cx, cy + 10, cx + 12, cy - 10), fill=WHITE, width=5)


def _vertical_gradient(size, top, bottom):
    """Small deterministic RGBA gradient used by the editorial layouts."""
    width, height = size
    out = Image.new("RGBA", size)
    px = out.load()
    for y in range(height):
        t = y / max(1, height - 1)
        color = tuple(round(top[i] * (1 - t) + bottom[i] * t) for i in range(4))
        for x in range(width):
            px[x, y] = color
    return out


def _horizontal_gradient(size, left, right):
    width, height = size
    out = Image.new("RGBA", size)
    dr = ImageDraw.Draw(out)
    for x in range(width):
        t = x / max(1, width - 1)
        color = tuple(round(left[i] * (1 - t) + right[i] * t) for i in range(4))
        dr.line((x, 0, x, height), fill=color)
    return out


def _rounded_photo(image, size, radius=22, focus=0.5):
    photo = cover(image, *size, focus).convert("RGBA")
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size[0] - 1, size[1] - 1), radius=radius, fill=255)
    photo.putalpha(mask)
    return photo


def _contain_rgba(image, size):
    """Contain an RGBA asset without cropping and keep its transparent margins."""
    width, height = size
    image = image.convert("RGBA")
    alpha_box = image.getchannel("A").getbbox()
    if alpha_box:
        image = image.crop(alpha_box)
    scale = min(width / image.width, height / image.height)
    resized = image.resize((round(image.width * scale), round(image.height * scale)), Image.Resampling.LANCZOS)
    out = Image.new("RGBA", size, (0, 0, 0, 0))
    out.alpha_composite(resized, ((width - resized.width) // 2, (height - resized.height) // 2))
    return out


def _layout_audit(items: list[dict]) -> dict:
    """Measure ink area and contrast as a reproducible proxy for visual weight."""
    total = sum(item["weight"] for item in items)
    left = sum(item["weight"] * max(0, min(item["bbox"][2], W / 2) - item["bbox"][0]) /
               max(1, item["bbox"][2] - item["bbox"][0]) for item in items)
    right = total - left
    center_x = sum(item["weight"] * (item["bbox"][0] + item["bbox"][2]) / 2 for item in items) / total
    groups: dict[str, list[dict]] = {}
    for item in items:
        groups.setdefault(item["name"], []).append(item)
    boxes = {name: (min(i["bbox"][0] for i in parts), min(i["bbox"][1] for i in parts),
                    max(i["bbox"][2] for i in parts), max(i["bbox"][3] for i in parts))
             for name, parts in groups.items()}
    overlaps = []
    for n, (name, a) in enumerate(boxes.items()):
        for other, b in list(boxes.items())[n + 1:]:
            if min(a[2], b[2]) > max(a[0], b[0]) and min(a[3], b[3]) > max(a[1], b[1]):
                overlaps.append(f"{name}/{other}")
    out_of_bounds = [name for name, box in boxes.items()
                     if box[0] < 0 or box[1] < 0 or box[2] > W or box[3] > H]
    ratio = left / right if right else float("inf")
    return {
        "method": "painted pixel area × luminance contrast; photo background excluded",
        "elements": {name: {"bbox": list(boxes[name]),
                            "weight_pct": round(100 * sum(i["weight"] for i in parts) / total, 1),
                            "tier": parts[0]["tier"]} for name, parts in groups.items()},
        "left_right_ratio": round(ratio, 3),
        "center_x_fraction": round(center_x / W, 3),
        "overlaps": overlaps,
        "out_of_bounds": out_of_bounds,
        "passed": 0.75 <= ratio <= 1.33 and 0.45 <= center_x / W <= 0.55
                  and not overlaps and not out_of_bounds,
    }


# --- layouts -----------------------------------------------------------------------
def main_image(job, v, logo, icons, sku: Sku) -> Image.Image:
    drafts_before = len(job.drafts)
    base = cover(source_photo(job, v, sku.base_image), W, H, 0.42).convert("RGBA")
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    mask = Image.new("L", (W, H), 0)
    p = mask.load()
    header_solid = 320
    header_end = 465
    for y in range(header_end):
        a = 247 if y <= header_solid else round(247 * (1 - (y - header_solid) / (header_end - header_solid)) ** 1.35)
        for x in range(W):
            p[x, y] = max(0, a)
    layer.paste((248, 250, 252, 255), (0, 0, W, H))
    layer.putalpha(mask.filter(ImageFilter.GaussianBlur(7)))
    base.alpha_composite(layer)
    dr = ImageDraw.Draw(base)
    audit_items: list[dict] = []

    def luminance(color):
        return (0.2126 * color[0] + 0.7152 * color[1] + 0.0722 * color[2]) / 255

    def draw_text(name, xy, value, font, fill, tier, background=(248, 250, 252)):
        dr.text(xy, value, font=font, fill=fill)
        if job.main_title_lines:
            ink = sum(font.getmask(value)) / 255
            audit_items.append({"name": name, "bbox": dr.textbbox(xy, value, font=font),
                                "weight": ink * abs(luminance(fill) - luminance(background)),
                                "tier": tier, "font_px": font.size})

    def draw_box(name, bbox, fill, tier):
        dr.rounded_rectangle(bbox, radius=14, fill=fill)
        if job.main_title_lines:
            audit_items.append({"name": name, "bbox": bbox,
                                "weight": (bbox[2] - bbox[0]) * (bbox[3] - bbox[1]) *
                                          abs(luminance(fill) - luminance((248, 250, 252))),
                                "tier": tier})

    if job.main_title_lines:
        add_logo(job, logo, base, 849, 28, 187)
        if logo is not None:
            logo_height = round(187 * logo.height / logo.width)
            resized_alpha = logo.getchannel("A").resize((187, logo_height), Image.Resampling.LANCZOS)
            audit_items.append({"name": "brand", "bbox": (849, 28, 1036, 28 + logo_height),
                                "weight": sum(resized_alpha.getdata()) / 255 * 0.65, "tier": "image"})
    else:
        add_logo(job, logo, base, 849, 28, 187)
    if job.main_title_lines:
        draw_text("title", (34, 40), job.title, condensed(76), NAVY, "large")
        body_y, years_y, size_y = 140, 136, 243
    else:
        dr.text((34, 40), job.title, font=fit(dr, job.title, 785, 76, 50), fill=NAVY)
        body_y, years_y, size_y = 140, 136, 243
    body_font = condensed(50) if job.main_title_lines else fit(dr, sku.body, 655, 54, 34)
    draw_text("variant", (34, body_y), sku.body, body_font, ORANGE, "medium")
    if job.main_title_lines:
        year_left, year_width, year_height, year_font_size = 720, 331, 79, 50
    else:
        year_left, year_width, year_height, year_font_size = 720, 331, 79, 49
    draw_box("years", (year_left, years_y, year_left + year_width, years_y + year_height), ORANGE, "medium")
    yf = condensed(50) if job.main_title_lines else fit(dr, sku.years, year_width - 40, year_font_size, 30)
    year_text_bb = dr.textbbox((0, 0), sku.years, font=yf)
    draw_text("years", (year_left + (year_width - (year_text_bb[2] - year_text_bb[0])) // 2, years_y + 9),
              sku.years, yf, WHITE, "medium", ORANGE)
    sw = 365
    draw_box("size", (34, size_y, 34 + sw, size_y + 90), NAVY, "medium")
    size_font = condensed(50) if job.main_title_lines else fit(dr, f"SIZE: {sku.code}", sw - 50, 58, 43)
    size_bb = dr.textbbox((0, 0), f"SIZE: {sku.code}", font=size_font)
    draw_text("size", (59, size_y + 9), f"SIZE: {sku.code}", size_font,
              WHITE, "medium", NAVY)
    if job.main_title_lines:
        dx = 34 + sw + 27
        dr.line((dx, size_y + 6, dx, size_y + 85), fill=NAVY, width=4)
        for i, line in enumerate(job.subtitle):
            draw_text("subtitle", (dx + 28, 247 + 40 * i), line, condensed(30), NAVY, "small")
    else:
        dx = 34 + sw + 27
        dr.line((dx, size_y + 6, dx, size_y + 85), fill=NAVY, width=4)
        for i, line in enumerate(job.subtitle):
            dr.text((dx + 28, 247 + 40 * i), line, font=fit(dr, line, 610, 34, 27), fill=NAVY)
    dr.rectangle((0, 1220, W, H), fill=NAVY)
    labels = [("ЗАЩИТА", "ОТ ДОЖДЯ"), ("ЗАЩИТА", "ОТ СНЕГА"), ("ЗАЩИТА", "ОТ СОЛНЦА"), ("ВСЕСЕЗОННЫЙ", "ЧЕХОЛ")]
    footer_items: list[dict] = []
    for i, (l1, l2) in enumerate(labels):
        x = i * 271
        ic = icons[i]
        s = min(58 / ic.width, 58 / ic.height)
        ic = ic.resize((round(ic.width * s), round(ic.height * s)), Image.Resampling.LANCZOS)
        icon_y = 1248 + (58 - ic.height) // 2
        base.alpha_composite(ic, (x + 22, icon_y))
        for value, text_y in ((l1, 1242), (l2, 1270)):
            font = bold(18)
            dr.text((x + 91, text_y), value, font=font, fill=WHITE)
            if job.main_title_lines:
                footer_items.append({"name": f"feature_{i + 1}",
                                     "bbox": dr.textbbox((x + 91, text_y), value, font=font),
                                     "weight": sum(font.getmask(value)) / 255 *
                                               abs(luminance(WHITE) - luminance(NAVY)), "tier": "small"})
        if job.main_title_lines:
            footer_items.append({"name": f"feature_{i + 1}",
                                 "bbox": (x + 22, icon_y, x + 22 + ic.width, icon_y + ic.height),
                                 "weight": sum(ic.getchannel("A").getdata()) / 255 * 0.7,
                                 "tier": "image"})
        if i < 3:
            dr.line((x + 270, 1238, x + 270, 1323), fill=(118, 151, 177), width=2)
    if job.main_title_lines:
        dr.line((70, 1336, 1016, 1336), fill=(118, 151, 177), width=2)
        legal_lines = [(1352, f"Материалы принадлежат бренду {job.brand}.", 27),
                       (1390, "За товары сторонних продавцов бренд ответственности не несёт.", 25)]
    else:
        legal_lines = [(1350, f"Материалы принадлежат бренду {job.brand}.", 18),
                       (1379, "За товары сторонних продавцов бренд ответственности не несёт.", 17)]
    for y, t, s in legal_lines:
        f = regular(s)
        bb = dr.textbbox((0, 0), t, font=f)
        pos = ((W - (bb[2] - bb[0])) // 2, y)
        dr.text(pos, t, font=f, fill=(220, 230, 238))
        if job.main_title_lines:
            footer_items.append({"name": f"legal_{1 if y == legal_lines[0][0] else 2}",
                                 "bbox": dr.textbbox(pos, t, font=f),
                                 "weight": sum(f.getmask(t)) / 255 *
                                           abs(luminance((220, 230, 238)) - luminance(NAVY)), "tier": "small"})
    if job.main_title_lines:
        audit = _layout_audit(audit_items)
        audit["reference"] = "toyota_land_cruiser/LandCruiser_L_主图_1086x1448.png"
        audit["reference_balance_window"] = {
            "left_right_ratio": [1.55, 2.05], "center_x_fraction": [0.38, 0.44]
        }
        audit["capsule_text_height_ratio"] = {
            "years": round((year_text_bb[3] - year_text_bb[1]) / year_height, 3),
            "size": round((size_bb[3] - size_bb[1]) / 90, 3),
            "accepted": [0.44, 0.58],
        }
        audit["header_font_tiers_px"] = {"small": 30, "medium": 50, "large": 76}
        actual_tiers = {tier: sorted({item["font_px"] for item in audit_items
                                      if item["tier"] == tier and "font_px" in item})
                        for tier in audit["header_font_tiers_px"]}
        audit["actual_header_font_px"] = actual_tiers
        audit["typography_passed"] = all(actual_tiers[tier] == [size]
                                         for tier, size in audit["header_font_tiers_px"].items())
        audit["reference_balance_passed"] = (
            1.55 <= audit["left_right_ratio"] <= 2.05
            and 0.38 <= audit["center_x_fraction"] <= 0.44
            and not audit["overlaps"] and not audit["out_of_bounds"]
        )
        audit["capsule_proportion_passed"] = all(
            0.44 <= audit["capsule_text_height_ratio"][name] <= 0.58
            for name in ("years", "size")
        )
        audit["footer"] = _layout_audit(footer_items)
        audit["passed"] = (audit["reference_balance_passed"] and audit["footer"]["passed"]
                           and audit["typography_passed"] and audit["capsule_proportion_passed"])
        job.layout_audits[sku.code] = audit
        if not audit["passed"]:
            raise ValueError(f"main layout audit failed for {sku.code}: {audit}")
    return watermark(base) if len(job.drafts) > drafts_before or _logo_missing(logo) else base


def fitment_image(job, v, logo, sku: Sku) -> Image.Image:
    drafts_before = len(job.drafts)
    img = cover(vehicle_photo(job, v, sku), W, H, 0.43).convert("RGBA")
    cards_bottom = 490 + len(sku.cards) * 93 + 20
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rectangle((0, 0, W, max(730, cards_bottom)), fill=(247, 250, 252, 238))
    img.alpha_composite(overlay)
    dr = ImageDraw.Draw(img)
    add_logo(job, logo, img, 856, 24, 176)
    dr.text((55, 37), "КАК ВЫБРАТЬ", font=condensed(61), fill=NAVY)
    dr.text((55, 103), "СВОЙ ВАРИАНТ", font=condensed(61), fill=ORANGE)
    dr.rounded_rectangle((57, 205, 796, 355), radius=24, fill=NAVY)
    dr.text((84, 225), "РАЗМЕР", font=condensed(62), fill=WHITE)
    dr.text((570, 211), sku.code, font=condensed(76), fill=ORANGE)
    dr.text((60, 400), "ПОДХОДИТ ДЛЯ:", font=condensed(34), fill=NAVY)
    dr.rounded_rectangle((60, 452, 838, 458), radius=3, fill=ORANGE)
    for i, (model, years) in enumerate(sku.cards):
        y = 490 + i * 93
        dr.rounded_rectangle((58, y, 1028, y + 78), radius=13, fill=WHITE, outline=(215, 222, 228), width=2)
        _check(dr, 97, y + 39)
        dr.text((137, y + 20), model, font=fit(dr, model, 620, 31, 20, False), fill=NAVY)
        yf = bold(28)
        bb = dr.textbbox((0, 0), years, font=yf)
        dr.text((1003 - (bb[2] - bb[0]), y + 21), years, font=yf, fill=ORANGE)
    dr.rectangle((0, 1297, W, H), fill=NAVY)
    dr.rectangle((0, 1297, W, 1303), fill=ORANGE)
    dr.ellipse((48, 1324, 118, 1394), outline=ORANGE, width=4)
    dr.text((76, 1325), "!", font=bold(54), fill=WHITE)
    dr.text((143, 1318), "ПЕРЕД ПОКУПКОЙ ПРОВЕРЬТЕ", font=bold(31), fill=WHITE)
    dr.text((143, 1354), "МОДЕЛЬ, КУЗОВ И ГОД ВЫПУСКА", font=fit(dr, "МОДЕЛЬ, КУЗОВ И ГОД ВЫПУСКА", 860, 31, 24, False), fill=WHITE)
    return watermark(img) if len(job.drafts) > drafts_before or _logo_missing(logo) else img


def selector_image(job, v, logo) -> Image.Image:
    drafts_before = len(job.drafts)
    sel = Image.new("RGBA", (W, H), (*PALE, 255))
    dr = ImageDraw.Draw(sel)
    add_logo(job, logo, sel, 858, 26, 174)
    dr.text((54, 36), "ВЫБЕРИТЕ СВОЙ", font=condensed(54), fill=NAVY)
    dr.text((54, 99), job.title, font=fit(dr, job.title, 780, 58, 36), fill=ORANGE)
    dr.text((57, 178), "КУЗОВ · ГОД ВЫПУСКА · РАЗМЕР", font=bold(27), fill=NAVY)
    dr.rounded_rectangle((57, 222, 1017, 228), radius=3, fill=ORANGE)
    n = len(job.skus)
    slot = (1240 - 270) // n
    for i, sku in enumerate(job.skus):
        y = 270 + i * slot
        h = slot - 30
        dr.rounded_rectangle((52, y, 1034, y + h), radius=20, fill=WHITE, outline=(216, 224, 230), width=2)
        thumb = cover(vehicle_photo(job, v, sku), 430, h - 30, 0.45)
        sel.alpha_composite(thumb.convert("RGBA"), (584, y + 15))
        dr = ImageDraw.Draw(sel)
        _check(dr, 98, y + 57, 22)
        dr.text((139, y + 38), sku.body, font=fit(dr, sku.body, 420, 34, 22), fill=NAVY)
        for j, (model, years) in enumerate(sku.cards[:4]):
            dr.text((76, y + 100 + j * 44), f"{model}  {years}", font=fit(dr, f"{model}  {years}", 480, 26, 16, False), fill=NAVY)
        dr.rounded_rectangle((76, y + h - 95, 300, y + h - 20), radius=14, fill=NAVY)
        st = f"SIZE {sku.code}"
        sf = fit(dr, st, 200, 50, 30)
        bb = dr.textbbox((0, 0), st, font=sf)
        dr.text((76 + (224 - (bb[2] - bb[0])) // 2, y + h - 88), st, font=sf, fill=WHITE)
    dr.rectangle((0, 1272, W, H), fill=NAVY)
    dr.rectangle((0, 1272, W, 1278), fill=ORANGE)
    dr.text((64, 1310), "ПЕРЕД ЗАКАЗОМ СВЕРЬТЕ", font=bold(35), fill=WHITE)
    dr.text((64, 1352), "КУЗОВ И ГОД ВЫПУСКА", font=bold(35), fill=WHITE)
    return watermark(sel) if len(job.drafts) > drafts_before or _logo_missing(logo) else sel


def editorial_main_image(job, v, logo, icons, sku: Sku) -> Image.Image:
    """Full-bleed product-first layout inspired by the strongest marketplace cards."""
    drafts_before = len(job.drafts)
    base = cover(source_photo(job, v, sku.base_image), W, H, 0.44).convert("RGBA")
    base.alpha_composite(_vertical_gradient((W, 470), (3, 25, 45, 242), (3, 25, 45, 0)), (0, 0))
    dr = ImageDraw.Draw(base)

    # A single compact header: product family, variant and brand.
    dr.text((48, 42), job.title, font=fit(dr, job.title, 735, 76, 50), fill=WHITE)
    dr.text((50, 137), sku.body, font=fit(dr, sku.body, 760, 48, 31), fill=(255, 101, 32))
    dr.rounded_rectangle((820, 30, 1040, 120), radius=18, fill=(255, 255, 255, 242))
    add_logo(job, logo, base, 842, 48, 176)

    # Size is the one dominant conversion cue; year remains secondary.
    dr.rounded_rectangle((48, 218, 315, 330), radius=20, fill=ORANGE)
    size_text = f"SIZE {sku.code}"
    sf = fit(dr, size_text, 225, 67, 42)
    bb = dr.textbbox((0, 0), size_text, font=sf)
    dr.text((48 + (267 - (bb[2] - bb[0])) // 2, 235), size_text, font=sf, fill=WHITE)
    dr.rounded_rectangle((333, 218, 672, 330), radius=20, fill=(3, 37, 67, 225), outline=(255, 255, 255, 95), width=2)
    dr.text((358, 235), "МОДЕЛЬНЫЕ ГОДЫ", font=bold(20), fill=(190, 208, 222))
    yf = fit(dr, sku.years, 290, 47, 31)
    dr.text((358, 267), sku.years, font=yf, fill=WHITE)
    dr.text((50, 354), "ВСЕСЕЗОННЫЙ ЧЕХОЛ ДЛЯ КРОССОВЕРА", font=bold(25), fill=WHITE)

    # Quiet bottom rail keeps the product photo dominant.
    dr.rectangle((0, 1228, W, H), fill=NAVY)
    dr.rectangle((0, 1228, W, 1235), fill=ORANGE)
    labels = [("ДОЖДЬ", "ОБЫЧНЫЕ ОСАДКИ"), ("СНЕГ", "ЛЁГКИЙ СНЕГ"),
              ("СОЛНЦЕ", "НА СТОЯНКЕ"), ("4 СЕЗОНА", "ПОВСЕДНЕВНО")]
    for i, (headline, caption) in enumerate(labels):
        x = i * 271
        ic = icons[i]
        scale = min(55 / ic.width, 55 / ic.height)
        ic = ic.resize((round(ic.width * scale), round(ic.height * scale)), Image.Resampling.LANCZOS)
        base.alpha_composite(ic, (x + 24, 1270 + (55 - ic.height) // 2))
        dr.text((x + 92, 1266), headline, font=bold(20), fill=WHITE)
        dr.text((x + 92, 1297), caption, font=bold(14), fill=(183, 204, 220))
        if i < 3:
            dr.line((x + 270, 1258, x + 270, 1337), fill=(88, 128, 158), width=2)
    disclaimer = f"Материалы принадлежат бренду {job.brand}.  За товары сторонних продавцов бренд ответственности не несёт."
    df = fit(dr, disclaimer, 980, 16, 13, False)
    dr.text((W // 2, 1392), disclaimer, font=df, fill=(190, 207, 220), anchor="mm")
    return watermark(base) if len(job.drafts) > drafts_before or _logo_missing(logo) else base


def editorial_fitment_image(job, v, logo, sku: Sku) -> Image.Image:
    """Compact compatibility board over a recognizable, uninterrupted vehicle scene."""
    drafts_before = len(job.drafts)
    img = cover(source_photo(job, v, sku.base_image), W, H, 0.46).convert("RGBA")
    img.alpha_composite(_vertical_gradient((W, 410), (2, 27, 49, 245), (2, 27, 49, 25)), (0, 0))
    dr = ImageDraw.Draw(img)

    dr.text((50, 40), "ПОДБЕРИТЕ ЧЕХОЛ", font=condensed(67), fill=WHITE)
    dr.text((52, 121), "ПО МОДЕЛИ И ГОДУ ВЫПУСКА", font=bold(27), fill=(255, 112, 45))
    dr.rounded_rectangle((820, 30, 1040, 120), radius=18, fill=(255, 255, 255, 242))
    add_logo(job, logo, img, 842, 48, 176)

    card_top = 230
    card_h = 248 + len(sku.cards) * 82
    card_bottom = card_top + card_h
    dr.rounded_rectangle((45, card_top, 1041, card_bottom), radius=28,
                         fill=(247, 250, 252, 239), outline=(255, 255, 255, 220), width=3)
    dr.rounded_rectangle((70, card_top + 28, 310, card_top + 140), radius=19, fill=ORANGE)
    st = f"SIZE {sku.code}"
    sf = fit(dr, st, 205, 64, 40)
    bb = dr.textbbox((0, 0), st, font=sf)
    dr.text((70 + (240 - (bb[2] - bb[0])) // 2, card_top + 45), st, font=sf, fill=WHITE)
    dr.text((342, card_top + 35), sku.body, font=fit(dr, sku.body, 650, 43, 27), fill=NAVY)
    dr.text((342, card_top + 88), sku.years, font=bold(29), fill=ORANGE)
    dr.text((72, card_top + 170), "СОВМЕСТИМЫЕ ВЕРСИИ", font=bold(23), fill=(79, 99, 116))
    dr.rectangle((72, card_top + 207, 1014, card_top + 212), fill=ORANGE)
    for i, (model, years) in enumerate(sku.cards):
        y = card_top + 232 + i * 82
        dr.rounded_rectangle((70, y, 1015, y + 65), radius=13, fill=WHITE, outline=(213, 222, 229), width=2)
        _check(dr, 104, y + 32, 18)
        dr.text((137, y + 17), model, font=fit(dr, model, 640, 27, 18, False), fill=NAVY)
        yf = bold(23)
        bb = dr.textbbox((0, 0), years, font=yf)
        dr.text((988 - (bb[2] - bb[0]), y + 18), years, font=yf, fill=ORANGE)

    # Connect the information board to the product instead of cutting it in half.
    tag_y = min(1115, card_bottom + 34)
    dr.rounded_rectangle((49, tag_y, 615, tag_y + 72), radius=16, fill=(3, 37, 67, 225))
    dr.text((76, tag_y + 18), "ВАШ ВАРИАНТ", font=bold(22), fill=(185, 205, 220))
    dr.text((270, tag_y + 8), f"SIZE {sku.code}", font=condensed(43), fill=WHITE)
    dr.rectangle((0, 1297, W, H), fill=NAVY)
    dr.rectangle((0, 1297, W, 1304), fill=ORANGE)
    dr.ellipse((48, 1330, 112, 1394), outline=ORANGE, width=4)
    dr.text((73, 1328), "!", font=bold(48), fill=WHITE)
    dr.text((138, 1323), "ПЕРЕД ПОКУПКОЙ СВЕРЬТЕ", font=bold(30), fill=WHITE)
    dr.text((138, 1360), "МОДЕЛЬ, КУЗОВ И ГОД ВЫПУСКА", font=fit(dr, "МОДЕЛЬ, КУЗОВ И ГОД ВЫПУСКА", 875, 30, 24, False), fill=WHITE)
    return watermark(img) if len(job.drafts) > drafts_before or _logo_missing(logo) else img


def editorial_selector_image(job, v, logo) -> Image.Image:
    """Two-card comparison with large photos and a short left-to-right reading path."""
    drafts_before = len(job.drafts)
    bg = cover(source_photo(job, v, job.skus[0].base_image), W, H, 0.48).filter(ImageFilter.GaussianBlur(18)).convert("RGBA")
    bg.alpha_composite(Image.new("RGBA", (W, H), (2, 27, 49, 218)))
    dr = ImageDraw.Draw(bg)
    dr.text((48, 38), "ВЫБЕРИТЕ СВОЙ", font=condensed(58), fill=WHITE)
    dr.text((49, 107), job.title, font=fit(dr, job.title, 760, 62, 40), fill=(255, 101, 32))
    dr.text((51, 177), "КУЗОВ  ·  ГОД ВЫПУСКА  ·  РАЗМЕР", font=bold(25), fill=(207, 222, 233))
    dr.rounded_rectangle((820, 30, 1040, 120), radius=18, fill=(255, 255, 255, 242))
    add_logo(job, logo, bg, 842, 48, 176)

    n = len(job.skus)
    slot = 430 if n == 2 else min(330, 940 // n)
    for i, sku in enumerate(job.skus):
        y = 250 + i * (slot + 26)
        dr.rounded_rectangle((42, y, 1044, y + slot), radius=26, fill=(248, 250, 252, 246), outline=(255, 255, 255, 230), width=3)
        photo = _rounded_photo(source_photo(job, v, sku.base_image), (452, slot - 32), 18, 0.47)
        bg.alpha_composite(photo, (58, y + 16))
        dr = ImageDraw.Draw(bg)
        dr.rounded_rectangle((534, y + 22, 760, y + 106), radius=16, fill=ORANGE)
        st = f"SIZE {sku.code}"
        sf = fit(dr, st, 196, 52, 34)
        bb = dr.textbbox((0, 0), st, font=sf)
        dr.text((534 + (226 - (bb[2] - bb[0])) // 2, y + 35), st, font=sf, fill=WHITE)
        dr.text((782, y + 38), sku.years, font=fit(dr, sku.years, 230, 31, 23, False), fill=NAVY)
        dr.text((535, y + 130), sku.body, font=fit(dr, sku.body, 474, 35, 23), fill=NAVY)
        dr.rectangle((535, y + 181, 1013, y + 186), fill=ORANGE)
        for j, (model, years) in enumerate(sku.cards[:4]):
            line = f"{model}  {years}"
            dr.text((540, y + 208 + j * 43), line, font=fit(dr, line, 465, 24, 16, False), fill=(20, 54, 81))

    footer_y = 250 + n * (slot + 26) + 4
    dr.rounded_rectangle((43, footer_y, 1043, footer_y + 118), radius=22, fill=(3, 37, 67, 235), outline=(255, 101, 32), width=3)
    dr.text((69, footer_y + 20), "1", font=condensed(55), fill=ORANGE)
    dr.text((112, footer_y + 28), "НАЙДИТЕ КУЗОВ", font=bold(24), fill=WHITE)
    dr.text((397, footer_y + 20), "2", font=condensed(55), fill=ORANGE)
    dr.text((440, footer_y + 28), "СВЕРЬТЕ ГОД", font=bold(24), fill=WHITE)
    dr.text((711, footer_y + 20), "3", font=condensed(55), fill=ORANGE)
    dr.text((754, footer_y + 28), "ВЫБЕРИТЕ SIZE", font=bold(24), fill=WHITE)
    dr.text((69, footer_y + 78), "ПЕРЕД ЗАКАЗОМ ПРОВЕРЬТЕ СОВМЕСТИМОСТЬ", font=bold(22), fill=(188, 207, 221))
    return watermark(bg) if len(job.drafts) > drafts_before or _logo_missing(logo) else bg


def logan_reference_fitment_image(job, v, logo, sku: Sku) -> Image.Image:
    """Logan-style fitment layout with separate information and vehicle zones."""
    drafts_before = len(job.drafts)
    source = source_photo(job, v, sku.base_image)
    img = cover(source, W, H, 0.48).filter(ImageFilter.GaussianBlur(10)).convert("RGBA")
    img.alpha_composite(Image.new("RGBA", (W, H), (247, 250, 252, 205)))
    dr = ImageDraw.Draw(img)
    dr.rectangle((0, 0, W, 18), fill=ORANGE)
    add_logo(job, logo, img, 842, 35, 190)

    dr.text((54, 48), job.title, font=fit(dr, job.title, 735, 76, 48), fill=NAVY)
    dr.text((56, 139), sku.body, font=fit(dr, sku.body, 735, 54, 32), fill=ORANGE)
    dr.rounded_rectangle((56, 220, 454, 326), radius=18, fill=NAVY)
    dr.text((82, 233), "РАЗМЕР", font=condensed(51), fill=WHITE)
    code_font = fit(dr, sku.code, 115, 67, 44)
    code_box = dr.textbbox((0, 0), sku.code, font=code_font)
    dr.text((420 - (code_box[2] - code_box[0]), 225), sku.code, font=code_font, fill=ORANGE)
    dr.rounded_rectangle((478, 220, 879, 326), radius=18, fill=ORANGE)
    yf = fit(dr, sku.years, 350, 49, 34)
    years_box = dr.textbbox((0, 0), sku.years, font=yf)
    dr.text((478 + (401 - (years_box[2] - years_box[0])) // 2, 242), sku.years, font=yf, fill=WHITE)
    dr.text((57, 370), "ТОЧНАЯ ПРОВЕРКА СОВМЕСТИМОСТИ", font=bold(29), fill=NAVY)
    dr.rectangle((57, 415, 1028, 421), fill=ORANGE)

    panel_top = 449
    row_h = 52
    panel_bottom = panel_top + 26 + len(sku.cards) * row_h
    dr.rounded_rectangle((55, panel_top, 1030, panel_bottom), radius=22,
                         fill=(255, 255, 255, 244), outline=(207, 219, 228), width=2)
    for i, (model, years) in enumerate(sku.cards):
        y = panel_top + 16 + i * row_h
        _check(dr, 91, y + 19, 18)
        dr.text((128, y + 4), model, font=fit(dr, model, 670, 26, 18, False), fill=NAVY)
        years_font = bold(22)
        years_box = dr.textbbox((0, 0), years, font=years_font)
        dr.text((1002 - (years_box[2] - years_box[0]), y + 6), years, font=years_font, fill=ORANGE)

    has_cutout = bool(sku.vehicle_image and (v.source / sku.vehicle_image).exists())
    if has_cutout:
        # Match the delivered Logan structure: scene only as a faint backdrop,
        # then a large transparent uncovered vehicle on top of it.
        stage_top = panel_bottom + 8
        dr.ellipse((90, 1090, 1015, 1278), fill=(17, 49, 74, 28))
        vehicle = _contain_rgba(vehicle_photo(job, v, sku), (1040, 570))
        img.alpha_composite(vehicle, (23, stage_top))
        dr = ImageDraw.Draw(img)
        dr.rounded_rectangle((58, 1180, 1028, 1285), radius=19,
                             fill=(255, 255, 255, 235), outline=(207, 219, 228), width=2)
        dr.text((82, 1201), "МОДЕЛЬ", font=condensed(30), fill=ORANGE)
        dr.text((82, 1237), job.title, font=fit(dr, job.title, 620, 32, 24, False), fill=NAVY)
        dr.rounded_rectangle((801, 1196, 997, 1270), radius=13, fill=NAVY)
        size_text = f"SIZE {sku.code}"
        size_font = fit(dr, size_text, 170, 45, 30)
        size_box = dr.textbbox((0, 0), size_text, font=size_font)
        dr.text((801 + (196 - (size_box[2] - size_box[0])) // 2, 1206),
                size_text, font=size_font, fill=WHITE)
    else:
        # Safe fallback when no transparent vehicle source has been approved yet.
        stage_top = panel_bottom + 24
        stage_bottom = 1302
        dr.rounded_rectangle((55, stage_top, 1030, stage_bottom), radius=24,
                             fill=WHITE, outline=(207, 219, 228), width=2)
        photo = _rounded_photo(vehicle_photo(job, v, sku), (951, stage_bottom - stage_top - 24), 18, 0.62)
        img.alpha_composite(photo, (67, stage_top + 12))

    dr = ImageDraw.Draw(img)
    dr.rectangle((0, 1320, W, H), fill=NAVY)
    dr.rectangle((0, 1320, W, 1327), fill=ORANGE)
    dr.ellipse((48, 1350, 112, 1414), outline=ORANGE, width=4)
    dr.text((73, 1348), "!", font=bold(48), fill=WHITE)
    dr.text((138, 1343), "ПЕРЕД ЗАКАЗОМ СВЕРЬТЕ", font=bold(30), fill=WHITE)
    dr.text((138, 1380), "КУЗОВ И ГОД ВЫПУСКА", font=bold(30), fill=WHITE)
    return watermark(img) if len(job.drafts) > drafts_before or _logo_missing(logo) else img


def logan_reference_selector_image(job, v, logo) -> Image.Image:
    """Logan-style pale comparison board with copy and photography kept apart."""
    drafts_before = len(job.drafts)
    img = Image.new("RGBA", (W, H), (*PALE, 255))
    dr = ImageDraw.Draw(img)
    dr.rectangle((0, 0, W, 18), fill=ORANGE)
    add_logo(job, logo, img, 850, 32, 184)
    dr.text((50, 45), "ВЫБЕРИТЕ", font=condensed(63), fill=NAVY)
    dr.text((50, 116), "СВОЙ ВАРИАНТ", font=condensed(63), fill=ORANGE)
    dr.text((54, 198), "КУЗОВ", font=bold(25), fill=NAVY)
    dr.text((175, 198), "•", font=bold(25), fill=ORANGE)
    dr.text((207, 198), "ГОД ВЫПУСКА", font=bold(25), fill=NAVY)
    dr.text((437, 198), "•", font=bold(25), fill=ORANGE)
    dr.text((468, 198), "РАЗМЕР", font=bold(25), fill=NAVY)
    dr.rectangle((53, 240, 1032, 247), fill=ORANGE)

    for i, sku in enumerate(job.skus):
        y = 282 + i * 475
        dr.rounded_rectangle((44, y, 1042, y + 438), radius=26, fill=WHITE,
                             outline=(201, 215, 225), width=3)
        dr.rounded_rectangle((62, y + 22, 286, y + 126), radius=18, fill=NAVY)
        dr.text((82, y + 37), "SIZE", font=condensed(35), fill=WHITE)
        code_font = fit(dr, sku.code, 90, 67, 44)
        dr.text((190, y + 23), sku.code, font=code_font, fill=ORANGE)
        dr.text((62, y + 151), sku.body, font=fit(dr, sku.body, 375, 40, 24), fill=NAVY)
        dr.rounded_rectangle((62, y + 205, 352, y + 270), radius=12, fill=(239, 244, 247))
        years_font = bold(31)
        years_box = dr.textbbox((0, 0), sku.years, font=years_font)
        dr.text((62 + (290 - (years_box[2] - years_box[0])) // 2, y + 219), sku.years,
                font=years_font, fill=NAVY)
        for j, (model, years) in enumerate(sku.cards[:4]):
            line = f"{model}  {years}"
            dr.text((64, y + 292 + j * 31), line, font=fit(dr, line, 370, 19, 14, False), fill=(58, 80, 98))

        vehicle = vehicle_photo(job, v, sku)
        if sku.vehicle_image and (v.source / sku.vehicle_image).exists():
            vehicle = _contain_rgba(vehicle, (650, 402))
            img.alpha_composite(vehicle, (374, y + 18))
        else:
            photo = _rounded_photo(vehicle, (570, 402), 18, 0.58)
            img.alpha_composite(photo, (454, y + 18))
        dr = ImageDraw.Draw(img)

    dr.rectangle((0, 1260, W, H), fill=NAVY)
    dr.rectangle((0, 1260, W, 1267), fill=ORANGE)
    dr.text((54, 1294), "1", font=condensed(58), fill=ORANGE)
    dr.text((102, 1296), "СВЕРЬТЕ КУЗОВ", font=bold(27), fill=WHITE)
    dr.text((407, 1294), "2", font=condensed(58), fill=ORANGE)
    dr.text((455, 1296), "СВЕРЬТЕ ГОД", font=bold(27), fill=WHITE)
    dr.text((738, 1294), "3", font=condensed(58), fill=ORANGE)
    dr.text((786, 1296), "ВЫБЕРИТЕ SIZE", font=bold(27), fill=WHITE)
    dr.text((55, 1380), "S = TIGUAN STANDARD     •     M = TIGUAN ALLSPACE / L",
            font=fit(dr, "S = TIGUAN STANDARD     •     M = TIGUAN ALLSPACE / L", 975, 29, 20, False), fill=WHITE)
    return watermark(img) if len(job.drafts) > drafts_before or _logo_missing(logo) else img


def rav4_v6_main_image(job, v, logo, icons, sku: Sku) -> Image.Image:
    """RAV4 V6 theme: high-contrast typography integrated into full-bleed photography."""
    drafts_before = len(job.drafts)
    img = cover(source_photo(job, v, sku.base_image), W, H, 0.48).convert("RGBA")
    img.alpha_composite(_vertical_gradient((W, 510), (4, 24, 44, 225), (4, 24, 44, 0)), (0, 0))
    img.alpha_composite(_vertical_gradient((W, 398), (4, 24, 44, 0), (4, 24, 44, 245)), (0, 1050))
    dr = ImageDraw.Draw(img)
    add_logo_light(job, logo, img, 840, 37, 198)
    dr.text((48, 43), job.title, font=fit(dr, job.title, 760, 72, 47, False), fill=WHITE)
    dr.text((49, 132), sku.body, font=fit(dr, sku.body, 760, 38, 24, False), fill=(244, 91, 22))
    dr.rounded_rectangle((50, 192, 374, 266), radius=12, fill=(244, 91, 22, 242))
    yf = fit(dr, sku.years, 278, 42, 28)
    dr.text((73, 204), sku.years, font=yf, fill=WHITE)
    dr.rounded_rectangle((50, 290, 315, 370), radius=12, fill=(4, 24, 44, 240))
    dr.text((73, 301), f"SIZE: {sku.code}", font=fit(dr, f"SIZE: {sku.code}", 220, 44, 29), fill=WHITE)
    dr.rectangle((0, 1222, W, H), fill=(4, 24, 44, 248))
    labels = [("ЗАЩИТА", "ОТ ДОЖДЯ"), ("ЗАЩИТА", "ОТ СНЕГА"),
              ("ЗАЩИТА", "ОТ СОЛНЦА"), ("ДЛЯ ПАРКОВКИ", "В ЛЮБОЙ СЕЗОН")]
    for i, (line1, line2) in enumerate(labels):
        x = i * 271
        icon = icons[i]
        scale = min(62 / icon.width, 62 / icon.height)
        icon = icon.resize((round(icon.width * scale), round(icon.height * scale)), Image.Resampling.LANCZOS)
        img.alpha_composite(icon, (x + 24, 1250 + (62 - icon.height) // 2))
        dr.text((x + 97, 1244), line1, font=bold(18), fill=WHITE)
        dr.text((x + 97, 1272), line2, font=bold(18), fill=WHITE)
        if i < 3:
            dr.line((x + 270, 1240, x + 270, 1326), fill=(113, 144, 168), width=2)
    notice = f"Материалы принадлежат бренду {job.brand}."
    dr.text((W // 2, 1350), notice, font=regular(18), fill=(215, 228, 237), anchor="ma")
    dr.text((W // 2, 1378), "За товары сторонних продавцов бренд ответственности не несёт.",
            font=regular(17), fill=(215, 228, 237), anchor="ma")
    return watermark(img) if len(job.drafts) > drafts_before or _logo_missing(logo) else img


def rav4_v6_fitment_image(job, v, logo, sku: Sku) -> Image.Image:
    drafts_before = len(job.drafts)
    img = cover(vehicle_photo(job, v, sku), W, H, 0.54).convert("RGBA")
    img.alpha_composite(_vertical_gradient((W, 450), (4, 24, 44, 230), (4, 24, 44, 0)), (0, 0))
    img.alpha_composite(_vertical_gradient((W, H - 620), (4, 24, 44, 20), (4, 24, 44, 245)), (0, 620))
    dr = ImageDraw.Draw(img)
    add_logo_light(job, logo, img, 842, 27, 195)
    dr.text((45, 37), job.title, font=fit(dr, job.title, 760, 72, 47), fill=WHITE)
    dr.text((49, 126), sku.body, font=fit(dr, sku.body, 750, 29, 20, False), fill=(255, 132, 72))
    dr.text((49, 175), sku.years, font=bold(38), fill=WHITE)
    dr.line((48, 790, 1038, 790), fill=(255, 255, 255, 180), width=2)
    dr.text((49, 805), "ПОДХОДИТ ДЛЯ", font=bold(49), fill=WHITE)
    dr.rounded_rectangle((804, 803, 1038, 872), radius=11, fill=(244, 91, 22, 245))
    dr.text((830, 815), f"SIZE {sku.code}", font=fit(dr, f"SIZE {sku.code}", 180, 42, 28), fill=WHITE)
    rows = sku.cards or [(sku.body, sku.years)]
    y0, available, gap = 895, 430, 4
    row_h = max(44, (available - gap * (len(rows) - 1)) // len(rows))
    for i, (model, years) in enumerate(rows):
        y = y0 + i * (row_h + gap)
        if y + row_h > 1325:
            break
        dr.rounded_rectangle((46, y, 1040, y + row_h), radius=8, fill=(8, 39, 70, 205))
        dr.rectangle((46, y, 54, y + row_h), fill=(244, 91, 22))
        line = f"{model}  ·  {years}"
        font = fit(dr, line, 920, min(38, row_h - 16), 18, False)
        dr.text((81, y + (row_h - font.size) // 2 - 3), line, font=font, fill=WHITE)
    dr.text((W // 2, 1362), "СВЕРЬТЕ КУЗОВ И ГОД ПЕРЕД ЗАКАЗОМ", font=bold(30), fill=WHITE, anchor="ma")
    return watermark(img) if len(job.drafts) > drafts_before or _logo_missing(logo) else img


def rav4_v6_selector_image(job, v, logo) -> Image.Image:
    drafts_before = len(job.drafts)
    canvas = Image.new("RGBA", (W, H), (4, 24, 44, 255))
    dr = ImageDraw.Draw(canvas)
    dr.text((45, 25), f"ВЫБЕРИТЕ СВОЙ {job.title}",
            font=fit(dr, f"ВЫБЕРИТЕ СВОЙ {job.title}", 770, 55, 34), fill=WHITE)
    dr.text((48, 93), "КУЗОВ · ГОД ВЫПУСКА · КОД", font=bold(28), fill=(196, 218, 234))
    add_logo_light(job, logo, canvas, 842, 21, 192)
    n = len(job.skus)
    panel_h = min(393, (1205 - 16 * max(0, n - 1)) // max(1, n))
    start_y = 165
    for i, sku in enumerate(job.skus):
        y = start_y + i * (panel_h + 8)
        panel = cover(vehicle_photo(job, v, sku), W, panel_h, 0.52).convert("RGBA")
        panel.alpha_composite(_horizontal_gradient((W, panel_h), (4, 24, 44, 250), (4, 24, 44, 45)))
        canvas.alpha_composite(panel, (0, y))
        dr = ImageDraw.Draw(canvas)
        dr.rectangle((0, y, 13, y + panel_h), fill=(244, 91, 22))
        dr.text((45, y + 19), job.title, font=fit(dr, job.title, 600, 42, 28), fill=WHITE)
        dr.text((45, y + 67), sku.body, font=fit(dr, sku.body, 650, 28, 18, False), fill=(255, 140, 83))
        dr.text((45, y + 109), sku.years, font=bold(39), fill=WHITE)
        yy = y + 165
        for model, years in sku.cards[:5]:
            line = f"{model}  {years}"
            dr.text((47, yy), line, font=fit(dr, line, 650, 23, 15, False), fill=WHITE)
            yy += 32
            if yy > y + panel_h - 55:
                break
        pill_h = 72
        dr.rounded_rectangle((853, y + panel_h - pill_h - 18, 1030, y + panel_h - 18),
                             radius=13, fill=(244, 91, 22, 240))
        sf = fit(dr, sku.code, 120, 52, 30)
        dr.text((941, y + panel_h - pill_h - 7), sku.code, font=sf, fill=WHITE, anchor="ma")
    dr.text((W // 2, 1400), "СВЕРЬТЕ МОДЕЛЬ, КУЗОВ И ГОД", font=bold(26), fill=WHITE, anchor="ma")
    return watermark(canvas) if len(job.drafts) > drafts_before or _logo_missing(logo) else canvas


def _logo_missing(logo) -> bool:
    return logo is None


def contact_sheet(paths: list[Path], out: Path, cols: int = 3) -> None:
    tw, th = 326, 435
    rows = (len(paths) + cols - 1) // cols
    sheet = Image.new("RGB", (tw * cols + 40, th * rows + 30), (232, 237, 241))
    for i, p in enumerate(paths):
        sheet.paste(Image.open(p).convert("RGB").resize((tw, th), Image.Resampling.LANCZOS),
                    (10 + (i % cols) * tw, 10 + (i // cols) * th))
    sheet.save(out)


def render_vehicle(job: Job, v: layout.Vehicle) -> dict:
    """Render main + fitment per SKU, one shared selector and a contact sheet into the package."""
    v.ensure_dirs()
    logo = _logo(job)
    icons = _icons()
    style = themes.resolve_style(job.layout_style or job.style)
    if style == "editorial":
        render_main = editorial_main_image
        render_fitment = editorial_fitment_image
        render_selector = editorial_selector_image
    elif style == "renault_logan":
        render_main = main_image
        render_fitment = logan_reference_fitment_image
        render_selector = logan_reference_selector_image
    elif style == "toyota_rav4_v6":
        render_main = rav4_v6_main_image
        render_fitment = rav4_v6_fitment_image
        render_selector = rav4_v6_selector_image
    else:
        render_main = main_image
        render_fitment = fitment_image
        render_selector = selector_image
    outputs: list[Path] = []
    for sku in job.skus:
        m = v.main / f"{job.file_prefix}_{sku.code}_主图_1086x1448.png"
        render_main(job, v, logo, icons, sku).convert("RGB").save(m)
        f = v.fitment / f"{job.file_prefix}_{sku.code}_车型适配图_1086x1448.png"
        render_fitment(job, v, logo, sku).convert("RGB").save(f)
        outputs += [m, f]
    codes = "_".join(s.code for s in job.skus)
    s = v.selector / f"{job.file_prefix}_{codes}_SKU共用选择图_1086x1448.png"
    render_selector(job, v, logo).convert("RGB").save(s)
    outputs.append(s)
    contact_sheet(outputs, v.preview / f"{job.file_prefix}_{len(outputs)}图总览.png")
    report = {"style": style, "images": [layout.key_of(p) for p in outputs],
              "drafts": sorted(set(job.drafts))}
    if job.layout_audits:
        report["main_layout_audit"] = job.layout_audits
    # Read by `run.py status`; lives next to (not inside) the package so it never ships in the zip.
    (v.package.parent / "render_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report
