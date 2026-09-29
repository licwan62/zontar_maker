from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import csv, shutil, zipfile

import sys; from pathlib import Path as _P; sys.path.insert(0, str(_P(__file__).resolve().parents[2] / "src"))
from zontar import layout, pack
v = layout.vehicle("toyota_land_cruiser").ensure_dirs()
src, main_dir, fit_dir, selector_dir, preview_dir = v.source, v.main, v.fitment, v.selector, v.preview
gallery_dir, pc_dir, mobile_dir = v.gallery, v.aplus_pc, v.aplus_mobile
info_dir = v.data_dir  # listing CSV + notes are versioned in git; pack copies them into 04_上架资料

W, H = 1086, 1448
navy = (4, 24, 44)
orange = (244, 91, 22)
white = (255, 255, 255)
regular = r"C:\Windows\Fonts\tahoma.ttf"
bold = r"C:\Windows\Fonts\ariblk.ttf"
condensed = r"C:\Windows\Fonts\tahomabd.ttf"

def F(size, heavy=False, condensed_font=False):
    return ImageFont.truetype(condensed if condensed_font else (bold if heavy else regular), size)

def draw_text(draw, xy, value, size, color=white, heavy=False, condensed_font=False, stroke=0):
    draw.text(xy, value, font=F(size, heavy, condensed_font), fill=color, stroke_width=stroke, stroke_fill=navy)

def text_bbox(draw, value, size, heavy=False, condensed_font=False):
    return draw.textbbox((0, 0), value, font=F(size, heavy, condensed_font))

def center_text(draw, y, value, size, color=white, heavy=False, condensed_font=False):
    box = text_bbox(draw, value, size, heavy, condensed_font)
    draw_text(draw, ((W - (box[2] - box[0])) // 2, y), value, size, color, heavy, condensed_font)

def cover(image, width, height, focus=0.5):
    scale = max(width / image.width, height / image.height)
    resized = image.resize((round(image.width * scale), round(image.height * scale)), Image.Resampling.LANCZOS)
    left = max(0, (resized.width - width) // 2)
    top = max(0, min(resized.height - height, round((resized.height - height) * focus)))
    return resized.crop((left, top, left + width, top + height))

def gradient(image, y0, y1, color, max_alpha, reverse=False):
    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    pixels = layer.load()
    for y in range(max(0, y0), min(image.height, y1)):
        q = (y - y0) / max(1, y1 - y0)
        alpha = round(max_alpha * (((1 - q) if reverse else q) ** 1.15))
        for x in range(image.width):
            pixels[x, y] = (*color, alpha)
    image.alpha_composite(layer)

logo = Image.open(layout.brand_logo()).convert("RGBA")
alpha = logo.getchannel("A").point(lambda value: 255 if value > 45 else 0)
logo = logo.crop(alpha.getbbox())

def add_brand(image, x, y, width):
    scaled = logo.resize((width, round(width * logo.height / logo.width)), Image.Resampling.LANCZOS)
    pixels = scaled.load()
    for yy in range(scaled.height):
        for xx in range(scaled.width):
            r, g, b, a = pixels[xx, yy]
            if a > 0 and max(r, g, b) < 110:
                pixels[xx, yy] = (255, 255, 255, a)
            elif a > 0 and b > r * 1.4:
                pixels[xx, yy] = (90, 177, 255, a)
    image.alpha_composite(scaled, (x, y))

sprite = Image.open(layout.brand_icons()).convert("RGBA")
icons = []
for i in range(4):
    x0 = round(sprite.width * i / 4)
    x1 = round(sprite.width * (i + 1) / 4)
    icon = sprite.crop((x0, 0, x1, sprite.height))
    icon_alpha = icon.getchannel("A").point(lambda value: 255 if value > 70 else 0)
    icon = icon.crop(icon_alpha.getbbox())
    icons.append(icon)

data = {
    "S": {
        "shipping": "YM",
        "body": "70 SERIES · 3 ДВЕРИ",
        "years": "1984–2026",
        "fit": [
            "71 · Рестайлинг 1 · 2007–2023",
            "71 · Рестайлинг 2 · 2023–2026",
            "70 Series · короткая база · 1984–2007",
        ],
        "fit_full": "Land Cruiser 71 70 Series Restyling 1 2007–2023; Land Cruiser 71 70 Series Restyling 2 2023–2026; Land Cruiser 70 Series короткая база 1984–2007",
    },
    "M": {
        "shipping": "YL",
        "body": "60/80 SERIES · 5 ДВЕРЕЙ",
        "years": "1980–1994",
        "fit": [
            "60 Series · 1980–1990",
            "80 Series · 1989–1994",
        ],
        "fit_full": "Land Cruiser 60 Series 1980–1990; Land Cruiser 80 Series 1989–1994",
    },
    "L": {
        "shipping": "YXL",
        "body": "76 · 80/100/200/300",
        "years": "1995–2026",
        "fit": [
            "76 · 70 Series · 2007–2026",
            "80 Series рестайлинг · 1995–1997",
            "100 Series / Cygnus · 1998–2007",
            "200 Series / Arctic Trucks · 2007–2021",
            "300 Series / Arctic Trucks · 2021–2026",
        ],
        "fit_full": "Land Cruiser 76 70 Series 2007–2026; Land Cruiser 80 Series Restyling 1995–1997; Land Cruiser 100 Series и Cygnus 1998–2007; Land Cruiser 200 Series и Arctic Trucks 2007–2021; Land Cruiser 300 Series и Arctic Trucks 2021–2026",
    },
    "XL": {
        "shipping": "YXL",
        "body": "78 · ДЛИННАЯ БАЗА",
        "years": "1984–2026",
        "fit": [
            "78 · Рестайлинг 1 · 2007–2023",
            "78 · Рестайлинг 2 · 2023–2026",
            "70 Series · длинная база · 1984–2007",
        ],
        "fit_full": "Land Cruiser 78 70 Series Restyling 1 2007–2023; Land Cruiser 78 70 Series Restyling 2 2023–2026; Land Cruiser 70 Series длинная база 1984–2007",
    },
}

for code, values in data.items():
    photo = Image.open(src / f"base_{code}.png").convert("RGB")
    image = cover(photo, W, H, 0.48).convert("RGBA")
    gradient(image, 0, 510, navy, 225, True)
    gradient(image, 1050, H, navy, 245)
    draw = ImageDraw.Draw(image)
    add_brand(image, 840, 37, 198)
    draw_text(draw, (48, 42), "TOYOTA", 66, white, True)
    draw_text(draw, (48, 112), "LAND CRUISER", 54, white, True)
    draw_text(draw, (49, 180), values["body"], 31, orange, True, True)
    draw.rounded_rectangle((50, 230, 374, 302), radius=12, fill=(*orange, 242))
    draw_text(draw, (73, 241), values["years"], 40, white, True, True)
    draw.rounded_rectangle((50, 324, 315, 404), radius=12, fill=(*navy, 240))
    draw_text(draw, (73, 335), "SIZE: " + code, 44, white, True, True)
    draw.rectangle((0, 1222, W, H), fill=(*navy, 248))
    labels = [("ЗАЩИТА", "ОТ ДОЖДЯ"), ("ЗАЩИТА", "ОТ СНЕГА"), ("ЗАЩИТА", "ОТ СОЛНЦА"), ("ДЛЯ ПАРКОВКИ", "В ЛЮБОЙ СЕЗОН")]
    for i, (line1, line2) in enumerate(labels):
        x = i * 271
        icon = icons[i]
        scale = min(62 / icon.width, 62 / icon.height)
        icon = icon.resize((round(icon.width * scale), round(icon.height * scale)), Image.Resampling.LANCZOS)
        image.alpha_composite(icon, (x + 24, 1250 + (62 - icon.height) // 2))
        draw_text(draw, (x + 97, 1244), line1, 18, white, True, True)
        draw_text(draw, (x + 97, 1272), line2, 18, white, True, True)
        if i < 3:
            draw.line((x + 270, 1240, x + 270, 1326), fill=(113, 144, 168), width=2)
    center_text(draw, 1350, "Материалы принадлежат бренду Tozaroa.", 18, (215, 228, 237))
    center_text(draw, 1378, "За товары сторонних продавцов бренд ответственности не несёт.", 17, (215, 228, 237))
    image.convert("RGB").save(main_dir / f"LandCruiser_{code}_主图_1086x1448.png", quality=95)

    vehicle = Image.open(src / f"vehicle_{code}.png").convert("RGB")
    image = cover(vehicle, W, H, 0.5).convert("RGBA")
    gradient(image, 0, 450, navy, 225, True)
    gradient(image, 620, H, navy, 245)
    draw = ImageDraw.Draw(image)
    add_brand(image, 842, 27, 195)
    draw_text(draw, (45, 34), "TOYOTA", 60, white, True, True)
    draw_text(draw, (45, 98), "LAND CRUISER", 48, white, True, True)
    draw_text(draw, (49, 157), values["body"], 27, (255, 132, 72), True, True)
    draw_text(draw, (49, 201), values["years"], 36, white, True, True)
    draw.line((48, 745, 1038, 745), fill=(255, 255, 255, 180), width=2)
    draw_text(draw, (49, 760), "ПОДХОДИТ ДЛЯ", 47, white, True, True)
    draw.rounded_rectangle((804, 758, 1038, 827), radius=11, fill=(*orange, 245))
    draw_text(draw, (830, 770), "SIZE " + code, 40, white, True, True)
    y = 850
    available = 470
    gap = 4
    row_h = (available - gap * (len(values["fit"]) - 1)) // len(values["fit"])
    font_size = 33 if len(values["fit"]) <= 3 else 27
    for index, row in enumerate(values["fit"]):
        yy = y + index * (row_h + gap)
        draw.rounded_rectangle((46, yy, 1040, yy + row_h), radius=8, fill=(8, 39, 70, 205))
        draw.rectangle((46, yy, 54, yy + row_h), fill=orange)
        box = text_bbox(draw, row, font_size, True, True)
        draw_text(draw, (76, yy + max(8, (row_h - (box[3] - box[1])) // 2 - 2)), row, font_size, white, True, True)
    center_text(draw, 1362, "СВЕРЬТЕ СЕРИЮ, КУЗОВ И ГОД", 30, white, True, True)
    image.convert("RGB").save(fit_dir / f"LandCruiser_{code}_车型适配图_1086x1448.png", quality=95)

# Shared four-SKU selector.
canvas = Image.new("RGBA", (W, H), (*navy, 255))
draw = ImageDraw.Draw(canvas)
draw_text(draw, (45, 25), "ВЫБЕРИТЕ LAND CRUISER", 48, white, True, True)
draw_text(draw, (48, 90), "СЕРИЯ · ГОД ВЫПУСКА · КОД", 27, (196, 218, 234), False, True)
add_brand(canvas, 842, 21, 192)
panel_h = 299
for i, code in enumerate(["S", "M", "L", "XL"]):
    values = data[code]
    y = 154 + i * 305
    vehicle = Image.open(src / f"vehicle_{code}.png").convert("RGB")
    panel = cover(vehicle, W, panel_h, 0.50).convert("RGBA")
    shade = Image.new("RGBA", (W, panel_h), (0, 0, 0, 0))
    pixels = shade.load()
    for x in range(W):
        alpha_value = min(255, round(248 * (1 - x / W) ** 1.2 + 32))
        for yy in range(panel_h):
            pixels[x, yy] = (*navy, alpha_value)
    panel.alpha_composite(shade)
    canvas.alpha_composite(panel, (0, y))
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, y, 13, y + panel_h), fill=orange)
    draw_text(draw, (45, y + 16), "LAND CRUISER", 33, white, True, True)
    draw_text(draw, (45, y + 56), values["body"], 24, (255, 140, 83), True, True)
    draw_text(draw, (45, y + 91), values["years"], 32, white, True, True)
    yy = y + 137
    for row in values["fit"][:5]:
        short = row.replace("Рестайлинг", "Рест.")
        draw_text(draw, (47, yy), short, 19, white, False, True)
        yy += 25
    draw.rounded_rectangle((862, y + 208, 1030, y + 280), radius=12, fill=(*orange, 242))
    draw_text(draw, (891, y + 218), code, 50, white, True, True)
    if i < 3:
        draw.line((0, y + panel_h + 3, W, y + panel_h + 3), fill=(255, 255, 255, 140), width=2)
center_text(draw, 1398, "СВЕРЬТЕ МОДЕЛЬ, КУЗОВ И ГОД", 25, white, True, True)
selector_path = selector_dir / "LandCruiser_S_M_L_XL_SKU共用选择图_1086x1448.png"
canvas.convert("RGB").save(selector_path, quality=95)

# Shared gallery and A+ for the SUV body group.
for source_path in sorted(layout.category_library(v.gallery_source).glob("*.png")):
    shutil.copy2(source_path, gallery_dir / source_path.name)
for source_path in sorted((layout.category_library(v.aplus_source) / "01_PC端_5张").glob("*.png")):
    shutil.copy2(source_path, pc_dir / source_path.name)
for source_path in sorted((layout.category_library(v.aplus_source) / "02_手机端_5张").glob("*.png")):
    shutil.copy2(source_path, mobile_dir / source_path.name)

common_tags = [
    "#защитаавто", "#тентнамашину", "#тентдляавтомобиля", "#чехолнаавтомобиль",
    "#авточехол", "#чехолдлямашины", "#чехол_для_авто", "#автотент",
    "#тент_для_автомобиля", "#чехолнаавто", "#тентдлямашины", "#пылезащитаавто",
]
tag_variants = {
    "S": ["#на_внедорожник", "#чехол_на_кроссовер", "#тент_для_кроссовера", "#чехол_для_машины_от_дождя", "#чехол_зимний_на_машину", "#всепогодныйчехол"],
    "M": ["#чехолнамашину", "#всесезонныйчехол", "#автопокрывало", "#чехол_на_машину_кроссовер", "#защита_авто_от_пыли", "#тент_на_автомобиль"],
    "L": ["#тойота_ленд_крузер_200", "#на_внедорожник", "#тент_на_автомобиль_кроссовер", "#чехол_на_автомобиль", "#всесезонныйтент", "#защитный_чехол_тент"],
    "XL": ["#чехолнаавтомобильXL", "#чехолдлямашиныXL", "#автоXL", "#внедорожников_чехол_для_авто", "#чехол_на_машину_всесезонный", "#тент_для_машины_универсальный"],
}

titles = {
    "S": "Чехол на автомобиль Tozaroa для Toyota Land Cruiser 70 Series, 71, короткая база 1984–2026, серый всесезонный тент на внедорожник от дождя, снега, солнца и пыли, без карманов для зеркал",
    "M": "Чехол на автомобиль Tozaroa для Toyota Land Cruiser 60 и 80 Series 1980–1994, серый всесезонный тент на внедорожник от дождя, снега, солнца, пыли и листьев, без карманов для зеркал",
    "L": "Чехол на автомобиль Tozaroa для Toyota Land Cruiser 76, 80, 100, 200 и 300 Series 1995–2026, серый всесезонный тент на внедорожник от дождя, снега, солнца и пыли, без карманов для зеркал",
    "XL": "Чехол на автомобиль Tozaroa для Toyota Land Cruiser 78 и длинной базы 70 Series 1984–2026, серый всесезонный тент на внедорожник от дождя, снега, солнца и пыли, без карманов для зеркал",
}

def bullets(code):
    return (
        f"1. СОВМЕСТИМОСТЬ. Чехол подготовлен для Toyota Land Cruiser размера {code}; перед заказом обязательно сопоставьте серию, индекс кузова, длину базы и год выпуска со списком на отдельном изображении совместимости. "
        "2. МАТЕРИАЛ. Лёгкое однослойное полотно PEVA серого цвета имеет гладкую поверхность, мягкий матово-сатиновый блеск и естественно драпируется; это не утеплённый, не стёганый и не алюминизированный чехол. "
        "3. КОНСТРУКЦИЯ БЕЗ КАРМАНОВ. Перед установкой сложите штатные зеркала. Цельное полотно закрывает зеркала, кузов, стёкла, фары, дверные ручки и верхнюю часть колёс; отдельных ушек, молний и светоотражающих полос нет. "
        "4. ДЛЯ ЕЖЕДНЕВНОЙ ПАРКОВКИ. Чехол помогает закрыть автомобиль от обычного дождя и снега, дорожной пыли, солнечного света и опавших листьев. Не заявляются утепление, защита от града или устойчивость к экстремальному ветру. "
        "5. УСТАНОВКА И УХОД. Используйте на чистом остывшем автомобиле: сложите зеркала, расправьте полотно по крыше и равномерно опустите края. После использования удалите загрязнения, полностью просушите материал и аккуратно сложите чехол."
    )

csv_path = info_dir / "Toyota_Land_Cruiser_Tozaroa_上架内容.csv"
headers = ["SKU", "实际发货尺码", "品牌", "车型", "适配", "标题", "标题字符数", "标签", "标签数量", "五点介绍", "颜色", "材质", "主图", "车型图", "共用SKU图"]
rows = []
for code, values in data.items():
    title = titles[code]
    tags = common_tags + tag_variants[code]
    rows.append([
        code, values["shipping"], "Tozaroa", "Toyota Land Cruiser", values["fit_full"], title, len(title), " ".join(tags), len(tags), bullets(code),
        "Серый", "Однослойный PEVA", f"../01_主图/LandCruiser_{code}_主图_1086x1448.png",
        f"../02_车型适配图/LandCruiser_{code}_车型适配图_1086x1448.png", "../03_SKU共用图/LandCruiser_S_M_L_XL_SKU共用选择图_1086x1448.png",
    ])
with csv_path.open("w", encoding="utf-8-sig", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(headers)
    writer.writerows(rows)

(info_dir / "尺码分组说明.txt").write_text(
    "Toyota Land Cruiser 按Ozon展示尺码分为4个SKU：\n"
    "S → 实际发货YM：71、70 Series短轴，1984–2026。\n"
    "M → 实际发货YL：60 Series、80 Series早期，1980–1994。\n"
    "L → 实际发货YXL：76、80改款、100/200/300、Cygnus、Arctic Trucks，1995–2026。\n"
    "XL → 实际发货YXL：78、70 Series长轴，1984–2026。\n"
    "越野车共用副图8张、PC端A+ 5张、移动端A+ 5张已放入06、07、08文件夹。",
    encoding="utf-8",
)

# Contact sheet: 4 main images, 4 fitment images and one shared selector.
thumb_w, thumb_h = 326, 435
contact = Image.new("RGB", (thumb_w * 3 + 40, thumb_h * 3 + 80), (235, 239, 243))
assets = []
for code in ["S", "M", "L", "XL"]:
    assets.append(main_dir / f"LandCruiser_{code}_主图_1086x1448.png")
    assets.append(fit_dir / f"LandCruiser_{code}_车型适配图_1086x1448.png")
assets.append(selector_path)
for index, path in enumerate(assets):
    image = Image.open(path).convert("RGB").resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
    x = 10 + (index % 3) * thumb_w
    y = 10 + (index // 3) * thumb_h
    contact.paste(image, (x, y))
contact.save(preview_dir / "LandCruiser_九图总览.png", quality=95)

zip_path = pack.build(v.slug)

print({"package": str(v.package), "zip": str(zip_path), "title_lengths": {code: len(title) for code, title in titles.items()}})
