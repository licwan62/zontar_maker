"""Data-driven renderer for per-vehicle SKU images (main / fitment / selector / contact sheet).

Layouts are the parametric form of the delivered Renault Logan / Land Cruiser designs,
so a new vehicle needs only data (data/vehicles/<slug>/inputs/skus.csv) plus source photos
(assets/inputs/vehicles/<slug>/source/base_<SKU>.png). When a source photo or the brand
logo is missing, a neutral placeholder is used and every affected image gets a DRAFT
watermark so it cannot be mistaken for a deliverable.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from . import layout

W, H = 1086, 1448
NAVY, ORANGE, WHITE = (3, 37, 67), (232, 71, 5), (255, 255, 255)
PALE = (244, 248, 251)
FONT_DIR = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"


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


@dataclass
class Job:
    brand: str
    title: str                 # e.g. "VOLKSWAGEN TIGUAN"
    file_prefix: str           # e.g. "VW_Tiguan"
    subtitle: tuple[str, str]  # two Russian lines next to the SIZE box
    skus: list[Sku]
    drafts: list[str] = field(default_factory=list)


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


# --- layouts -----------------------------------------------------------------------
def main_image(job, v, logo, icons, sku: Sku) -> Image.Image:
    drafts_before = len(job.drafts)
    base = cover(source_photo(job, v, sku.base_image), W, H, 0.42).convert("RGBA")
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    mask = Image.new("L", (W, H), 0)
    p = mask.load()
    for y in range(465):
        a = 247 if y <= 320 else round(247 * (1 - (y - 320) / 145) ** 1.35)
        for x in range(W):
            p[x, y] = max(0, a)
    layer.paste((248, 250, 252, 255), (0, 0, W, H))
    layer.putalpha(mask.filter(ImageFilter.GaussianBlur(7)))
    base.alpha_composite(layer)
    dr = ImageDraw.Draw(base)
    add_logo(job, logo, base, 849, 28, 187)
    dr.text((34, 40), job.title, font=fit(dr, job.title, 785, 76, 50), fill=NAVY)
    dr.text((34, 140), sku.body, font=fit(dr, sku.body, 655, 54, 34), fill=ORANGE)
    dr.rounded_rectangle((720, 136, 1051, 215), radius=14, fill=ORANGE)
    yf = fit(dr, sku.years, 291, 49, 30)
    bb = dr.textbbox((0, 0), sku.years, font=yf)
    dr.text((720 + (331 - (bb[2] - bb[0])) // 2, 145), sku.years, font=yf, fill=WHITE)
    sw = 365
    dr.rounded_rectangle((34, 243, 34 + sw, 333), radius=14, fill=NAVY)
    dr.text((59, 252), f"SIZE: {sku.code}", font=fit(dr, f"SIZE: {sku.code}", sw - 50, 58, 43), fill=WHITE)
    dx = 34 + sw + 27
    dr.line((dx, 249, dx, 328), fill=NAVY, width=4)
    for i, line in enumerate(job.subtitle):
        dr.text((dx + 28, 247 + 40 * i), line, font=fit(dr, line, 610, 34, 27), fill=NAVY)
    dr.rectangle((0, 1220, W, H), fill=NAVY)
    labels = [("ЗАЩИТА", "ОТ ДОЖДЯ"), ("ЗАЩИТА", "ОТ СНЕГА"), ("ЗАЩИТА", "ОТ СОЛНЦА"), ("ВСЕСЕЗОННЫЙ", "ЧЕХОЛ")]
    for i, (l1, l2) in enumerate(labels):
        x = i * 271
        ic = icons[i]
        s = min(58 / ic.width, 58 / ic.height)
        ic = ic.resize((round(ic.width * s), round(ic.height * s)), Image.Resampling.LANCZOS)
        base.alpha_composite(ic, (x + 22, 1248 + (58 - ic.height) // 2))
        dr.text((x + 91, 1242), l1, font=bold(18), fill=WHITE)
        dr.text((x + 91, 1270), l2, font=bold(18), fill=WHITE)
        if i < 3:
            dr.line((x + 270, 1238, x + 270, 1323), fill=(118, 151, 177), width=2)
    for y, t, s in [(1350, f"Материалы принадлежат бренду {job.brand}.", 18),
                    (1379, "За товары сторонних продавцов бренд ответственности не несёт.", 17)]:
        f = regular(s)
        bb = dr.textbbox((0, 0), t, font=f)
        dr.text(((W - (bb[2] - bb[0])) // 2, y), t, font=f, fill=(220, 230, 238))
    return watermark(base) if len(job.drafts) > drafts_before or _logo_missing(logo) else base


def fitment_image(job, v, logo, sku: Sku) -> Image.Image:
    drafts_before = len(job.drafts)
    img = cover(source_photo(job, v, sku.base_image), W, H, 0.43).convert("RGBA")
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
        thumb = cover(source_photo(job, v, sku.base_image), 430, h - 30, 0.45)
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
    outputs: list[Path] = []
    for sku in job.skus:
        m = v.main / f"{job.file_prefix}_{sku.code}_主图_1086x1448.png"
        main_image(job, v, logo, icons, sku).convert("RGB").save(m)
        f = v.fitment / f"{job.file_prefix}_{sku.code}_车型适配图_1086x1448.png"
        fitment_image(job, v, logo, sku).convert("RGB").save(f)
        outputs += [m, f]
    codes = "_".join(s.code for s in job.skus)
    s = v.selector / f"{job.file_prefix}_{codes}_SKU共用选择图_1086x1448.png"
    selector_image(job, v, logo).convert("RGB").save(s)
    outputs.append(s)
    contact_sheet(outputs, v.preview / f"{job.file_prefix}_{len(outputs)}图总览.png")
    return {"images": [str(p) for p in outputs], "drafts": sorted(set(job.drafts))}
