from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pathlib import Path
import shutil, zipfile

import sys; from pathlib import Path as _P; sys.path.insert(0, str(_P(__file__).resolve().parents[2] / "src"))
from zontar import layout, pack
v = layout.vehicle("toyota_land_cruiser").ensure_dirs()
src, main_dir, fit_dir, selector_dir, preview_dir = v.source, v.main, v.fitment, v.selector, v.preview
W, H = 1086, 1448
navy = (3, 37, 67)
orange = (232, 71, 5)
white = (255, 255, 255)
ice = (243, 247, 250)
heading_font = r"C:\Windows\Fonts\arialbd.ttf"
display_font = r"C:\Windows\Fonts\ariblk.ttf"
condensed_font = r"C:\Windows\Fonts\impact.ttf"
body_font = r"C:\Windows\Fonts\arialbd.ttf"
regular_font = r"C:\Windows\Fonts\arial.ttf"

backup = layout.backup_before_overwrite([main_dir, fit_dir, selector_dir, preview_dir], "toyota_land_cruiser_redesign")

def font(size, regular=False):
    return ImageFont.truetype(regular_font if regular else heading_font, size)

def heavy(size):
    return ImageFont.truetype(display_font, size)

def condensed(size):
    return ImageFont.truetype(condensed_font, size)

def fit_condensed(draw, value, max_width, start_size, minimum=18):
    size = start_size
    while size > minimum:
        f = condensed(size)
        if draw.textbbox((0, 0), value, font=f)[2] <= max_width:
            return f
        size -= 1
    return condensed(minimum)

def fit_heavy(draw, value, max_width, start_size, minimum=18):
    size = start_size
    while size > minimum:
        f = heavy(size)
        if draw.textbbox((0, 0), value, font=f)[2] <= max_width:
            return f
        size -= 1
    return heavy(minimum)

def fit_font(draw, value, max_width, start_size, minimum=18, regular=False):
    size = start_size
    while size > minimum:
        f = font(size, regular)
        if draw.textbbox((0, 0), value, font=f)[2] <= max_width:
            return f
        size -= 1
    return font(minimum, regular)

def cover(image, width, height, focus=0.5):
    scale = max(width / image.width, height / image.height)
    resized = image.resize((round(image.width * scale), round(image.height * scale)), Image.Resampling.LANCZOS)
    left = max(0, (resized.width - width) // 2)
    top = max(0, min(resized.height - height, round((resized.height - height) * focus)))
    return resized.crop((left, top, left + width, top + height))

logo = Image.open(layout.brand_logo()).convert("RGBA")
alpha = logo.getchannel("A").point(lambda value: 255 if value > 45 else 0)
logo = logo.crop(alpha.getbbox())

def add_logo(image, x, y, width, dark=False):
    scaled = logo.resize((width, round(width * logo.height / logo.width)), Image.Resampling.LANCZOS)
    pixels = scaled.load()
    for yy in range(scaled.height):
        for xx in range(scaled.width):
            r, g, b, a = pixels[xx, yy]
            if not a:
                continue
            if max(r, g, b) < 110:
                pixels[xx, yy] = ((10, 20, 28, a) if dark else (255, 255, 255, a))
            elif b > r * 1.3:
                pixels[xx, yy] = (32, 120, 222, a) if dark else (90, 177, 255, a)
    image.alpha_composite(scaled, (x, y))

winter = cover(Image.open(src / "winter_master_background.png").convert("RGB"), W, H, 0.42)

def blend_header(photo):
    header = winter.convert("RGBA")
    mask = Image.new("L", (W, H), 0)
    p = mask.load()
    for y in range(0, 465):
        if y <= 320:
            a = 247
        else:
            a = round(247 * (1 - (y - 320) / 145) ** 1.35)
        for x in range(W):
            p[x, y] = max(0, min(250, a))
    header.putalpha(mask.filter(ImageFilter.GaussianBlur(7)))
    photo.alpha_composite(header)

sprite = Image.open(layout.brand_icons()).convert("RGBA")
icons = []
for i in range(4):
    x0, x1 = round(sprite.width * i / 4), round(sprite.width * (i + 1) / 4)
    icon = sprite.crop((x0, 0, x1, sprite.height))
    a = icon.getchannel("A").point(lambda value: 255 if value > 70 else 0)
    icons.append(icon.crop(a.getbbox()))

data = {
    "S": {"body": "70 SERIES · 3 ДВЕРИ", "years": "1984–2026", "cards": [("LAND CRUISER 71", "2007–2026"), ("70 SERIES · КОРОТКАЯ БАЗА", "1984–2007")]},
    "M": {"body": "60/80 SERIES · 5 ДВЕРЕЙ", "years": "1980–1994", "cards": [("LAND CRUISER 60 SERIES", "1980–1990"), ("LAND CRUISER 80 SERIES", "1989–1994")]},
    "L": {"body": "76 · 80/100/200/300", "years": "1995–2026", "cards": [("LAND CRUISER 76", "2007–2026"), ("80 SERIES · РЕСТАЙЛИНГ", "1995–1997"), ("100 SERIES / CYGNUS", "1998–2007"), ("200 SERIES / ARCTIC TRUCKS", "2007–2021"), ("300 SERIES / ARCTIC TRUCKS", "2021–2026")]},
    "XL": {"body": "78 · ДЛИННАЯ БАЗА", "years": "1984–2026", "cards": [("LAND CRUISER 78", "2007–2026"), ("70 SERIES · ДЛИННАЯ БАЗА", "1984–2007")]},
}

for code, values in data.items():
    # Main-image master v4: compact integrated header with condensed automotive typography.
    photo = cover(Image.open(src / f"base_{code}.png").convert("RGB"), W, H, 0.48).convert("RGBA")
    blend_header(photo)
    draw = ImageDraw.Draw(photo)
    add_logo(photo, 849, 28, 187, dark=True)
    title = "TOYOTA LAND CRUISER"
    draw.text((34, 40), title, font=fit_condensed(draw, title, 785, 70, 55), fill=navy)

    body_font_fit = fit_condensed(draw, values["body"], 665, 53, 35)
    draw.text((34, 140), values["body"], font=body_font_fit, fill=orange)
    year_x = 720
    draw.rounded_rectangle((year_x, 136, 1051, 215), radius=14, fill=orange)
    years_font = fit_condensed(draw, values["years"], 291, 49, 37)
    year_box = draw.textbbox((0, 0), values["years"], font=years_font)
    draw.text((year_x + (331 - (year_box[2] - year_box[0])) // 2, 145), values["years"], font=years_font, fill=white)

    size_width = 340 if code != "XL" else 365
    draw.rounded_rectangle((34, 243, 34 + size_width, 333), radius=14, fill=navy)
    draw.text((59, 252), f"SIZE: {code}", font=fit_condensed(draw, f"SIZE: {code}", size_width - 50, 58, 43), fill=white)
    divider_x = 34 + size_width + 27
    draw.line((divider_x, 249, divider_x, 328), fill=navy, width=4)
    descriptor_x = divider_x + 28
    draw.text((descriptor_x, 247), "ВСЕСЕЗОННЫЙ ЧЕХОЛ", font=fit_condensed(draw, "ВСЕСЕЗОННЫЙ ЧЕХОЛ", 610, 34, 27), fill=navy)
    draw.text((descriptor_x, 287), "ДЛЯ ВНЕДОРОЖНИКА", font=fit_condensed(draw, "ДЛЯ ВНЕДОРОЖНИКА", 610, 34, 27), fill=navy)

    draw.rectangle((0, 1220, W, H), fill=navy)
    labels = [("ЗАЩИТА", "ОТ ДОЖДЯ"), ("ЗАЩИТА", "ОТ СНЕГА"), ("ЗАЩИТА", "ОТ СОЛНЦА"), ("ВСЕСЕЗОННЫЙ", "ЧЕХОЛ")]
    for i, (line1, line2) in enumerate(labels):
        x = i * 271
        icon = icons[i]
        scale = min(58 / icon.width, 58 / icon.height)
        icon = icon.resize((round(icon.width * scale), round(icon.height * scale)), Image.Resampling.LANCZOS)
        photo.alpha_composite(icon, (x + 22, 1248 + (58 - icon.height) // 2))
        draw.text((x + 91, 1242), line1, font=font(18), fill=white)
        draw.text((x + 91, 1270), line2, font=font(18), fill=white)
        if i < 3:
            draw.line((x + 270, 1238, x + 270, 1323), fill=(118, 151, 177), width=2)
    notice1 = "Материалы принадлежат бренду Tozaroa."
    notice2 = "За товары сторонних продавцов бренд ответственности не несёт."
    for y, value, size in [(1350, notice1, 18), (1379, notice2, 17)]:
        box = draw.textbbox((0, 0), value, font=font(size, True))
        draw.text(((W - (box[2] - box[0])) // 2, y), value, font=font(size, True), fill=(220, 230, 238))
    photo.convert("RGB").save(main_dir / f"LandCruiser_{code}_主图_1086x1448.png", quality=96)

    # Fitment-image master based on the supplied reference: light winter canvas, dominant size banner, check-card list, vehicle below.
    image = winter.convert("RGBA")
    vehicle = Image.open(src / f"vehicle_{code}.png").convert("RGB")
    vehicle_panel = cover(vehicle, W, 660, 0.70).convert("RGBA")
    vehicle_mask = Image.new("L", (W, 660), 255)
    mp = vehicle_mask.load()
    for y in range(105):
        a = round(255 * (y / 105) ** 1.2)
        for x in range(W):
            mp[x, y] = a
    vehicle_panel.putalpha(vehicle_mask.filter(ImageFilter.GaussianBlur(3)))
    image.alpha_composite(vehicle_panel, (0, 748))
    draw = ImageDraw.Draw(image)
    add_logo(image, 856, 24, 176, dark=True)
    draw.text((55, 37), "КАК ВЫБРАТЬ", font=heavy(61), fill=navy)
    draw.text((55, 103), "СВОЙ ВАРИАНТ", font=heavy(61), fill=orange)
    draw.rounded_rectangle((57, 205, 796, 355), radius=24, fill=navy)
    draw.text((84, 225), "РАЗМЕР", font=heavy(62), fill=white)
    code_font = heavy(76)
    draw.text((570, 211), code, font=code_font, fill=orange)
    draw.text((60, 400), "ПОДХОДИТ ДЛЯ:", font=heavy(34), fill=navy)
    draw.rounded_rectangle((60, 452, 838, 458), radius=3, fill=orange)

    cards = values["cards"]
    card_h = 61 if len(cards) >= 5 else 72
    gap = 8
    y0 = 480
    for index, (model, years) in enumerate(cards):
        y = y0 + index * (card_h + gap)
        draw.rounded_rectangle((58, y, 850, y + card_h), radius=13, fill=(255, 255, 255, 235), outline=(215, 222, 228), width=2)
        cy = y + card_h // 2
        draw.ellipse((76, cy - 21, 118, cy + 21), fill=navy)
        draw.line((88, cy, 98, cy + 10), fill=white, width=5)
        draw.line((98, cy + 10, 110, cy - 10), fill=white, width=5)
        model_font = fit_font(draw, model, 490, 30 if len(cards) < 5 else 25, 19)
        draw.text((137, y + (card_h - model_font.size) // 2 - 3), model, font=model_font, fill=navy)
        year_font = font(28 if len(cards) < 5 else 24)
        year_box = draw.textbbox((0, 0), years, font=year_font)
        draw.text((825 - (year_box[2] - year_box[0]), y + (card_h - year_font.size) // 2 - 2), years, font=year_font, fill=orange)

    draw.rectangle((0, 1297, W, H), fill=navy)
    draw.rectangle((0, 1297, W, 1303), fill=orange)
    draw.ellipse((48, 1324, 118, 1394), outline=orange, width=4)
    draw.text((76, 1325), "!", font=font(54), fill=white)
    draw.text((143, 1318), "ПЕРЕД ПОКУПКОЙ ПРОВЕРЬТЕ", font=font(31), fill=white)
    draw.text((143, 1354), "МОДЕЛЬ, СЕРИЮ, КУЗОВ И ГОД", font=fit_font(draw, "МОДЕЛЬ, СЕРИЮ, КУЗОВ И ГОД", 860, 31, 24), fill=white)
    image.convert("RGB").save(fit_dir / f"LandCruiser_{code}_车型适配图_1086x1448.png", quality=96)

# Shared selector in the same light winter master language.
selector = winter.convert("RGBA")
draw = ImageDraw.Draw(selector)
add_logo(selector, 858, 26, 174, dark=True)
draw.text((54, 36), "ВЫБЕРИТЕ СВОЙ", font=heavy(54), fill=navy)
draw.text((54, 99), "LAND CRUISER", font=heavy(58), fill=orange)
draw.text((57, 178), "СЕРИЯ · ГОД ВЫПУСКА · РАЗМЕР", font=font(27), fill=navy)
draw.rounded_rectangle((57, 222, 1017, 228), radius=3, fill=orange)

card_y = 256
for index, code in enumerate(["S", "M", "L", "XL"]):
    values = data[code]
    y = card_y + index * 249
    draw.rounded_rectangle((52, y, 1034, y + 225), radius=20, fill=(255, 255, 255, 238), outline=(216, 224, 230), width=2)
    thumb = cover(Image.open(src / f"vehicle_{code}.png").convert("RGB"), 330, 205, 0.69)
    thumb = thumb.resize((330, 205), Image.Resampling.LANCZOS)
    selector.alpha_composite(thumb.convert("RGBA"), (684, y + 10))
    draw = ImageDraw.Draw(selector)
    draw.ellipse((76, y + 29, 120, y + 73), fill=navy)
    draw.line((88, y + 50, 98, y + 60), fill=white, width=5)
    draw.line((98, y + 60, 111, y + 39), fill=white, width=5)
    draw.text((139, y + 22), "LAND CRUISER", font=font(32), fill=navy)
    draw.text((76, y + 82), values["body"], font=fit_font(draw, values["body"], 570, 29, 21), fill=orange)
    draw.text((76, y + 126), values["years"], font=font(32), fill=navy)
    draw.rounded_rectangle((476, y + 145, 645, y + 207), radius=12, fill=navy)
    size_text = f"SIZE {code}"
    size_font = fit_font(draw, size_text, 145, 33, 25)
    box = draw.textbbox((0, 0), size_text, font=size_font)
    draw.text((476 + (169 - (box[2] - box[0])) // 2, y + 153), size_text, font=size_font, fill=white)

draw.rectangle((0, 1272, W, H), fill=navy)
draw.rectangle((0, 1272, W, 1278), fill=orange)
draw.text((64, 1310), "ПЕРЕД ЗАКАЗОМ СВЕРЬТЕ", font=font(35), fill=white)
draw.text((64, 1352), "СЕРИЮ, КУЗОВ И ГОД ВЫПУСКА", font=fit_font(draw, "СЕРИЮ, КУЗОВ И ГОД ВЫПУСКА", 930, 35, 27), fill=white)
selector_path = selector_dir / "LandCruiser_S_M_L_XL_SKU共用选择图_1086x1448.png"
selector.convert("RGB").save(selector_path, quality=96)

# Updated nine-image overview.
thumb_w, thumb_h = 326, 435
contact = Image.new("RGB", (thumb_w * 3 + 40, thumb_h * 3 + 80), (232, 237, 241))
assets = []
for code in ["S", "M", "L", "XL"]:
    assets.append(main_dir / f"LandCruiser_{code}_主图_1086x1448.png")
    assets.append(fit_dir / f"LandCruiser_{code}_车型适配图_1086x1448.png")
assets.append(selector_path)
for index, path in enumerate(assets):
    image = Image.open(path).convert("RGB").resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
    contact.paste(image, (10 + (index % 3) * thumb_w, 10 + (index // 3) * thumb_h))
contact.save(preview_dir / "LandCruiser_九图总览.png", quality=96)

zip_path = pack.build(v.slug)

print({"main": 4, "fitment": 4, "selector": 1, "backup": str(backup), "zip": str(zip_path)})
