"""Step 20: listing copy and upload rows, all as CSV (no xlsx tooling needed).

in : data/vehicles/volkswagen_tiguan/inputs/skus.csv
     data/reference/tag_bank/Data.csv                    (tag coverage check)
     data/templates/official_listing_template/模板.csv    (header rows of the Ozon upload template)
out: data/vehicles/volkswagen_tiguan/Volkswagen_Tiguan_Tozaroa_上架内容.csv   -> zip 04_上架资料
     data/vehicles/volkswagen_tiguan/尺码分组说明.txt                          -> zip 04_上架资料
     data/vehicles/volkswagen_tiguan/official_listing/模板.csv                 (rows to paste into the template)
     data/vehicles/volkswagen_tiguan/inputs/source_prompts.csv                 (prompts for the missing source photos)
"""
import sys; from pathlib import Path as _P; sys.path.insert(0, str(_P(__file__).resolve().parents[2] / "src"))
import re

from zontar import layout, tables

sys.stdout.reconfigure(encoding="utf-8")
v = layout.vehicle("volkswagen_tiguan")
reg = layout.vehicle_registry()[v.slug]
BRAND = reg["listing_brand"]
skus = {r["sku"]: r for r in tables.read_csv(v.data_dir / "inputs" / "skus.csv")}

common = [
    "#защитаавто", "#тентнамашину", "#тентдляавтомобиля", "#чехолнаавтомобиль",
    "#авточехол", "#чехолдлямашины", "#чехол_для_авто", "#автотент",
    "#тент_для_автомобиля", "#чехолнаавто", "#тентдлямашины", "#пылезащитаавто",
    "#чехолнаТигуан", "#чехолнаVolkswagenTiguan", "#тентнаФольксвагенТигуан",
]
variant_tags = {
    "S": ["#чехол_на_кроссовер", "#тент_для_кроссовера", "#чехол_для_машины_от_дождя",
          "#чехол_зимний_на_машину", "#всепогодныйчехол", "#чехолнаTiguanR"],
    "M": ["#чехол_на_машину_кроссовер", "#всесезонныйчехол", "#автопокрывало",
          "#защита_авто_от_пыли", "#тент_на_автомобиль", "#чехолнаTiguanAllspace"],
}
titles = {
    "S": f"Чехол на автомобиль {BRAND} для Volkswagen Tiguan I, II, III и Tiguan R 2007–2026, серый всесезонный тент на кроссовер от дождя, снега, солнца, пыли и листьев, без карманов для зеркал",
    "M": f"Чехол на автомобиль {BRAND} для Volkswagen Tiguan Allspace, L, L Pro и X 2016–2026, серый всесезонный тент на удлинённый кроссовер от дождя, снега, солнца и пыли, без карманов для зеркал",
}
fit_text = {
    "S": "Volkswagen Tiguan I 2007–2018; Tiguan II 2016–2025; Tiguan III (Европа) 2023–2026; Tiguan R 2020–2024",
    "M": "Volkswagen Tiguan Allspace / L 2016–2026; Tiguan L Pro / X 2020–2026; Tiguan III (версия США) 2025–2026",
}
first_point = {
    "S": "1. ТОЧНАЯ ПРИВЯЗКА К МОДЕЛИ. Вариант S подготовлен для Volkswagen Tiguan 2007–2026 годов: первое и второе "
         "поколение, европейская версия третьего поколения, а также Tiguan R 2020–2024. Перед заказом сверьте "
         "поколение и длину кузова: удлинённые Tiguan Allspace, L, L Pro и X относятся к варианту M.",
    "M": "1. ДЛЯ УДЛИНЁННОГО КУЗОВА. Вариант M рассчитан на Volkswagen Tiguan Allspace и Tiguan L 2016–2026, "
         "Tiguan L Pro и Tiguan X 2020–2026, а также на удлинённую версию Tiguan третьего поколения для рынка США "
         "2025–2026. Обычный Tiguan I–III европейской версии и Tiguan R относятся к варианту S.",
}
shared_points = (
    "2. СПЛОШНАЯ КОНСТРУКЦИЯ БЕЗ КАРМАНОВ ДЛЯ ЗЕРКАЛ. Перед установкой сложите боковые зеркала: единое полотно "
    "закрывает их вместе с кузовом. Такая схема сохраняет аккуратный силуэт и не создаёт лишних выступов.\n"
    "3. СЕРЫЙ ОДНОСЛОЙНЫЙ PEVA. Лёгкий гладкий материал с матово-сатиновым блеском помогает закрыть кузов от обычных "
    "осадков, снега, солнечного света, дорожной пыли и опавших листьев. Чехол не является утеплителем и не заменяет гараж.\n"
    "4. ДЛЯ УЛИЦЫ И ГАРАЖА. Полное покрытие кузова кроссовера помогает поддерживать автомобиль чище между поездками "
    "при уличной, дворовой или гаражной парковке. Надевайте только на остывший автомобиль и чистую поверхность.\n"
    "5. УСТАНОВКА И УХОД. Сложите зеркала, расправьте полотно по крыше, затем опустите края спереди, сзади и по бокам. "
    "После дождя просушите чехол перед хранением; очищайте мягкой влажной тканью без абразивов."
)

bank = {t.strip() for row in tables.read_csv(layout.data_root() / "reference/tag_bank/Data.csv")
        for t in re.split(r"\s+", row.get("标签词", "")) if t.startswith("#")}

errors, records = [], []
for code, sku in skus.items():
    tags = common + variant_tags[code]
    title = titles[code]
    bullets = first_point[code] + "\n" + shared_points
    if len(title) > 200:
        errors.append(f"{code}: title {len(title)} chars > 200")
    if len(tags) != len(set(tags)) or len(tags) > 30:
        errors.append(f"{code}: tags must be unique and at most 30")
    errors += [f"{code}: tag over 30 chars: {t}" for t in tags if len(t) > 30]
    in_bank = sum(t in bank for t in tags)
    print(f"{code}: title {len(title)} chars, {len(tags)} tags ({in_bank} from tag bank, {len(tags) - in_bank} model-specific/new)")
    records.append(dict(code=code, ship=sku["ship_size"], title=title, tags=" ".join(tags), n_tags=len(tags), bullets=bullets))
if errors:
    raise SystemExit("\n".join(errors))

prefix = "Volkswagen_Tiguan"
headers = ["SKU", "实际发货尺码", "品牌", "车型", "适配", "标题", "标题字符数", "标签", "标签数量", "五点介绍", "颜色", "材质", "主图", "车型图", "共用SKU图"]
rows = [[r["code"], r["ship"], BRAND, "Volkswagen Tiguan", fit_text[r["code"]], r["title"], len(r["title"]), r["tags"], r["n_tags"],
         r["bullets"], "Серый", "Однослойный PEVA",
         f"../01_主图/VW_Tiguan_{r['code']}_主图_1086x1448.png",
         f"../02_车型适配图/VW_Tiguan_{r['code']}_车型适配图_1086x1448.png",
         "../03_SKU共用图/VW_Tiguan_S_M_SKU共用选择图_1086x1448.png"] for r in records]
tables.write_csv(v.data_dir / f"{prefix}_{BRAND}_上架内容.csv", [headers, *rows])

(v.data_dir / "尺码分组说明.txt").write_text(
    "Volkswagen Tiguan 两个 Ozon SKU：\n"
    "S → 实际发货 YM：Tiguan I 2007–2018、Tiguan II 2016–2025、Tiguan III 欧洲版 2023–2026、Tiguan R 2020–2024。\n"
    "M → 实际发货 YL：Tiguan Allspace / L 2016–2026、Tiguan L Pro / X 2020–2026、Tiguan III 北美加长版 2025–2026。\n"
    "依据：inputs/size_map.csv（运营提供）与 inputs/fitment_detail.csv（俄罗斯销量表逐代车长）。\n"
    "越野车共用副图 8 张、PC 端 A+ 5 张、移动端 A+ 5 张在 06、07、08 文件夹。\n",
    encoding="utf-8")

# Upload rows in template column order (same column mapping as the delivered vehicles).
template = list(__import__("csv").reader((layout.data_root() / "templates/official_listing_template/模板.csv").open(encoding="utf-8-sig")))
header_rows = template[:next(i for i, row in enumerate(template) if row and row[0].strip().isdigit())]  # stop before example rows
width = len(header_rows[1])
upload = []
for i, r in enumerate(records):
    vals = [""] * width
    def put(col, value): vals[col - 1] = value
    put(1, i + 1); put(2, f"VolkswagenTiguan-{r['code']}"); put(3, r["title"]); put(4, 301); put(5, 888); put(6, "是")
    put(10, 800); put(11, 260); put(12, 60); put(13, 300); put(17, BRAND); put(18, "VolkswagenTiguan")
    put(19, r["code"]); put(20, "灰色"); put(21, "汽车罩"); put(22, 800); put(23, 1); put(24, r["tags"])
    put(25, r["bullets"]); put(27, "Volkswagen"); put(29, "Volkswagen"); put(33, r["title"]); put(34, 1); put(35, "PEVA")
    put(36, "Volkswagen Tiguan"); put(37, "Без карманов для зеркал"); put(38, "汽车"); put(40, "中国"); put(41, 1)
    upload.append(vals)
tables.write_csv(v.data_dir / "official_listing" / "模板.csv", [*header_rows, *upload])

rules = ("3:4 竖图，至少 1086×1448，无任何文字、额外 Logo、水印或标注。灰色单层轻薄光滑 PEVA 车罩，哑光至柔和缎面光泽，自然余量与少量不规则褶皱；"
         "无耳袋、无镜套、无反光条、无银色铝膜或金属高光。后视镜已折叠并被整片罩布连续覆盖。使用 C01「左垂右提」掀罩状态："
         "画面左侧车头处罩布下摆自然垂到保险杠和底盘之下、接近地面；罩布前缘从左向右连续升高，刚掀过中央大众车标，"
         "露出靠镜头一侧的单个车灯，并在右侧升到近侧前轮轮毂上方，完整露出近侧前轮及少量前翼子板。另一侧车灯仍被罩住。"
         "后轮露在罩布下摆之外。45–55 mm 全画幅标准焦距，自然前 3/4 视角，透视适中，车头与车尾大小差不过分；"
         "主图默认完整展示车辆，从前保险杠到后保险杠及两个可见车轮都在画面内，左右留少量边距。"
         "秋冬户外停车场景（落叶、初霜或薄雪），明亮清晰、接地真实；车身填满下方约 55–60%，上方约 35% 可叠加标题与大 Logo，避免过量天空和前景留白。")
prompts = [["sku", "file", "vehicle", "cover_state_id", "prompt"],
           ["S", "base_S.png", "Volkswagen Tiguan II 标准轴距（5 座，车长约 4.5 m）",
            "C01", "Volkswagen Tiguan 第二代标准轴距 SUV，车头朝左，灰色车罩覆盖车身，使用指定的非对称掀罩状态。" + rules],
           ["M", "base_M.png", "Volkswagen Tiguan Allspace（7 座加长版，车长约 4.7 m）",
            "C01", "Volkswagen Tiguan Allspace 加长版，车头朝左，灰色车罩覆盖车身，使用指定的非对称掀罩状态；通过车顶与车侧轮廓体现加长车身。" + rules]]
tables.write_csv(v.data_dir / "inputs" / "source_prompts.csv", prompts)
print("ok:", [str(v.data_dir / f"{prefix}_{BRAND}_上架内容.csv"), str(v.data_dir / "official_listing" / "模板.csv")])
