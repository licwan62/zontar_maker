from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pathlib import Path
import csv, html, shutil, zipfile

ROOT = Path('Toyota_RAV4_灰色无耳_Tozaroa_上架包')
IMG = ROOT / '01_SKU专属图'
DOC = ROOT / '04_上架资料'
LOGO = Path(r'C:\Users\Lenovo\Desktop\exec-d3683c74-61df-4003-b326-40f68d3b800e.png')
FONT = r'C:\Windows\Fonts\arial.ttf'
BOLD = r'C:\Windows\Fonts\arialbd.ttf'
W, H = 1086, 1448

def font(size, bold=False): return ImageFont.truetype(BOLD if bold else FONT, size)

logo = Image.open(LOGO).convert('RGBA')
bbox = logo.getbbox()
logo = logo.crop(bbox)

data = {
 'M': {
  'base':'base_M.png', 'label':'TOYOTA RAV4', 'sub':'SUV 5 ДВЕРЕЙ · LONG',
  'years':'2005–2026',
  'rows':['2025–2026 · SUV 5 дверей','2018–2026 · SUV 5 дверей','2015–2019 · SUV 5 дверей','2010–2016 · Long, 5 дверей','2005–2010 · Long, 5 дверей'],
 },
 'S': {
  'base':'base_S.png', 'label':'TOYOTA RAV4', 'sub':'SUV 5 ДВЕРЕЙ',
  'years':'1994–2016',
  'rows':['2012–2015 · SUV 5 дверей','2010–2016 · SUV 5 дверей','2005–2010 · SUV 5 дверей','2003–2006 · SUV 5 дверей','2000–2003 · SUV 5 дверей','1994–2000 · SUV 5 дверей'],
 },
 'YS': {
  'base':'base_YS.png', 'label':'TOYOTA RAV4', 'sub':'КОРОТКАЯ БАЗА · 3 ДВЕРИ',
  'years':'1994–2006',
  'rows':['2003–2006 · SUV 3 двери','2000–2003 · SUV 3 двери','1994–2000 · SUV 3 двери','1994–2000 · SUV, короткая база'],
 },
}

def paste_logo(im, y=20, target_w=210, x=30):
    ratio = target_w/logo.width
    lg = logo.resize((target_w, int(logo.height*ratio)), Image.Resampling.LANCZOS)
    im.alpha_composite(lg, (x, y))

def text_center(draw, xy_y, text, f, fill, stroke=0):
    box = draw.textbbox((0,0), text, font=f, stroke_width=stroke)
    draw.text(((W-(box[2]-box[0]))//2, xy_y), text, font=f, fill=fill, stroke_width=stroke, stroke_fill=(255,255,255,210))

for code, d in data.items():
    base = Image.open(IMG/d['base']).convert('RGBA').resize((W,H), Image.Resampling.LANCZOS)
    shade = Image.new('RGBA',(W,H),(0,0,0,0)); sd=ImageDraw.Draw(shade)
    sd.rectangle((0,0,W,300), fill=(240,245,248,218))
    sd.rectangle((0,H-170,W,H), fill=(12,25,39,220))
    base.alpha_composite(shade)
    paste_logo(base, 10, 210, 35)
    dr=ImageDraw.Draw(base)
    text_center(dr,105,d['label'],font(62,True),(20,31,44,255))
    text_center(dr,180,d['sub'],font(29,True),(41,63,81,255))
    dr.rounded_rectangle((390,230,696,310),radius=20,fill=(231,108,36,245))
    text_center(dr,238,f'РАЗМЕР {code}',font(45,True),'white')
    text_center(dr,325,d['years'],font(31,True),(255,255,255,255),2)
    disclaimer='Материалы принадлежат бренду Tozaroa.  За товары сторонних продавцов бренд ответственности не несёт.'
    text_center(dr,H-125,disclaimer,font(20), 'white')
    out=IMG/f'RAV4_{code}_主图_1086x1448.png'; base.convert('RGB').save(out,quality=96)

    bg=Image.open(IMG/d['base']).convert('RGB').resize((W,H),Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(5)).convert('RGBA')
    bg.alpha_composite(Image.new('RGBA',(W,H),(10,24,38,150)))
    paste_logo(bg,10,200,35); dr=ImageDraw.Draw(bg)
    text_center(dr,155,'ПРОВЕРЬТЕ СОВМЕСТИМОСТЬ',font(43,True),'white')
    text_center(dr,220,f'TOYOTA RAV4 · РАЗМЕР {code}',font(38,True),(255,169,87,255))
    y=330
    for row in d['rows']:
        dr.rounded_rectangle((90,y,W-90,y+105),radius=18,fill=(245,247,248,232),outline=(231,108,36,255),width=3)
        dr.text((130,y+31),row,font=font(29,True),fill=(18,35,51,255)); y+=125
    dr.text((95,H-180),'Перед покупкой сопоставьте год, кузов и версию автомобиля.',font=font(25,True),fill='white')
    dr.text((95,H-135),'Зеркала складываются и закрываются цельным полотном без карманов.',font=font(22),fill='white')
    text_center(dr,H-80,'Материалы принадлежат бренду Tozaroa.',font(20),'white')
    bg.convert('RGB').save(IMG/f'RAV4_{code}_车型适配图_1086x1448.png',quality=96)

# Shared SKU selector
canvas=Image.new('RGBA',(W,H),(232,238,241,255)); dr=ImageDraw.Draw(canvas)
paste_logo(canvas,10,200,35)
text_center(dr,150,'ВЫБЕРИТЕ СВОЙ RAV4',font(52,True),(18,35,51,255))
text_center(dr,215,'СВЕРЬТЕ КУЗОВ И ГОД ВЫПУСКА',font(27,True),(75,91,104,255))
y=330
for code in ['M','S','YS']:
    d=data[code]
    dr.rounded_rectangle((70,y,W-70,y+270),radius=28,fill='white',outline=(27,61,83,255),width=3)
    dr.rounded_rectangle((95,y+42,260,y+207),radius=24,fill=(231,108,36,255))
    dr.text((131,y+82),code,font=font(62,True),fill='white')
    dr.text((295,y+42),d['sub'],font=font(27,True),fill=(18,35,51,255))
    dr.text((295,y+94),d['years'],font=font(38,True),fill=(231,108,36,255))
    desc={'M':'Современные 5-дверные и Long','S':'Ранние 5-дверные версии','YS':'3-дверные и короткая база'}[code]
    dr.text((295,y+151),desc,font=font(24),fill=(70,82,92,255))
    dr.text((295,y+195),'Точный список — на отдельной карточке размера',font=font(20),fill=(70,82,92,255))
    y+=300
dr.text((80,H-180),'Размер YS назначен строкам исходной таблицы с пометкой «нет доступного размера».',font=font(21,True),fill=(18,35,51,255))
dr.text((80,H-130),'Материалы принадлежат бренду Tozaroa. За товары сторонних продавцов бренд ответственности не несёт.',font=font(18),fill=(40,55,66,255))
canvas.convert('RGB').save(IMG/'RAV4_M_S_YS_SKU共用选择图_1086x1448.png',quality=96)

titles={
'M':'Чехол на автомобиль Tozaroa для Toyota RAV4 SUV 5 дверей и Long 2005–2026, серый всесезонный тент на машину для парковки от дождя, снега, солнца, пыли и листьев, без карманов для зеркал',
'S':'Чехол на автомобиль Tozaroa для Toyota RAV4 SUV 5 дверей 1994–2016, серый всесезонный тент на машину для уличной парковки от дождя, снега, солнца, пыли и листьев, без карманов для зеркал',
'YS':'Чехол на автомобиль Tozaroa для Toyota RAV4 SUV 3 двери и короткой базы 1994–2006, серый всесезонный тент на машину от дождя, снега, солнца, пыли и листьев, без карманов для зеркал'
}
tags=['#защитаавто','#тентнамашину','#тентдляавтомобиля','#чехолнаавтомобиль','#авточехол','#чехолдлямашины','#чехол_для_авто','#автотент','#тент_для_автомобиля','#чехолнаавто','#тентдлямашины','#пылезащитаавто','#чехолнамашину','#всепогодныйчехол','#автопокрывало','#тентнаавто','#чехол_на_машину_кроссовер','#защитный_чехол_тент']
five={}
for code,d in data.items():
    five[code]=(f"1. СОВМЕСТИМОСТЬ. Чехол подготовлен для Toyota RAV4 размера {code}; перед заказом обязательно сопоставьте год выпуска, тип кузова и версию автомобиля со списком на отдельном изображении совместимости. "
    "2. МАТЕРИАЛ. Лёгкое однослойное полотно PEVA серого цвета имеет гладкую поверхность, мягкий матово-сатиновый блеск, естественно драпируется и не имитирует утеплённый или стёганый чехол. "
    "3. КОНСТРУКЦИЯ БЕЗ КАРМАНОВ. Перед установкой сложите штатные зеркала; затем цельное полотно закрывает зеркала, кузов, стёкла, фары, дверные ручки и верхнюю часть колёс. Отдельных ушек и светоотражающих полос нет. "
    "4. ДЛЯ ЕЖЕДНЕВНОЙ ПАРКОВКИ. Чехол помогает закрыть автомобиль от обычного дождя и снега, дорожной пыли, солнечного света и опавших листьев. Не заявляются утепление, защита от града или экстремального ветра. "
    "5. УСТАНОВКА И УХОД. Используйте на чистом остывшем автомобиле: сложите зеркала, расправьте полотно по крыше и опустите края. После использования протрите загрязнения, полностью просушите и аккуратно сложите чехол.")

csv_path=DOC/'Toyota_RAV4_Tozaroa_上架内容.csv'
with csv_path.open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f); w.writerow(['SKU','品牌','车型','适配','标题','标题字符数','标签','标签数量','五点介绍','颜色','材质','主图','车型图','共用SKU图'])
    for c,d in data.items(): w.writerow([c,'Tozaroa','Toyota RAV4','; '.join(d['rows']),titles[c],len(titles[c]),' '.join(tags),len(tags),five[c],'Серый','Однослойный PEVA',f'../01_SKU专属图/RAV4_{c}_主图_1086x1448.png',f'../01_SKU专属图/RAV4_{c}_车型适配图_1086x1448.png','../01_SKU专属图/RAV4_M_S_YS_SKU共用选择图_1086x1448.png'])

cards=[]
for p in sorted(ROOT.rglob('*.png')):
    if p.name.startswith('base_'): continue
    rel=p.relative_to(ROOT).as_posix(); cards.append(f'<figure><img src="../{html.escape(rel)}"><figcaption>{html.escape(rel)}</figcaption></figure>')
(DOC/'图片预览.html').write_text('<!doctype html><meta charset="utf-8"><style>body{font-family:Arial;background:#eef2f4;margin:24px}h1{color:#17364a}.g{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}figure{margin:0;background:white;padding:10px;border-radius:12px}img{width:100%;height:520px;object-fit:contain;background:#ddd}figcaption{font-size:12px;word-break:break-all}</style><h1>Toyota RAV4 Tozaroa 上架包预览</h1><div class="g">'+''.join(cards)+'</div>',encoding='utf-8')

(DOC/'尺码分组说明.txt').write_text('Toyota RAV4：M、S、YS 三个SKU。原表“无可用尺码”4行全部按用户指示归入YS。年份与车身版本不跨行推断，具体列表见CSV和车型适配图。\n\n注意：当前项目中的越野车通用副图和A+仍带ZONTAR品牌，已作为参考复制，但不纳入本次Tozaroa上传ZIP。完成Tozaroa统一换牌后方可上传并在三个SKU间共用。\n',encoding='utf-8')

zip_path=ROOT.with_suffix('.zip')
with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as z:
    for p in ROOT.rglob('*'):
        rel=p.relative_to(ROOT)
        if p.is_file() and not p.name.startswith(('base_','QA_')) and rel.parts[0] not in {'02_共用越野车副图','03_共用越野车A+'}:
            z.write(p,p.relative_to(ROOT.parent))
print('built',zip_path)
for c,t in titles.items(): print(c,len(t),t)
