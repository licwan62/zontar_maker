from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pathlib import Path
import shutil, zipfile

import sys; from pathlib import Path as _P; sys.path.insert(0, str(_P(__file__).resolve().parents[2] / "src"))
from zontar import layout, pack
v = layout.vehicle("renault_logan").ensure_dirs()
src, main_dir, fit_dir, selector_dir, preview_dir = v.source, v.main, v.fitment, v.selector, v.preview
info_dir = v.data_dir  # text notes are versioned in git; pack copies them into 04_上架资料
W, H = 1086, 1448
navy, orange, white = (3, 37, 67), (232, 71, 5), (255, 255, 255)
impact = r"C:\Windows\Fonts\impact.ttf"
arial_bold = r"C:\Windows\Fonts\arialbd.ttf"
arial = r"C:\Windows\Fonts\arial.ttf"

def condensed(size): return ImageFont.truetype(impact, size)
def bold(size): return ImageFont.truetype(arial_bold, size)
def regular(size): return ImageFont.truetype(arial, size)
def fit(draw, text, width, start, minimum=18, condensed_font=True):
    size = start
    while size > minimum:
        f = condensed(size) if condensed_font else bold(size)
        if draw.textbbox((0, 0), text, font=f)[2] <= width: return f
        size -= 1
    return condensed(minimum) if condensed_font else bold(minimum)

def cover(image, width, height, focus=0.5):
    scale = max(width / image.width, height / image.height)
    resized = image.resize((round(image.width * scale), round(image.height * scale)), Image.Resampling.LANCZOS)
    left = max(0, (resized.width - width) // 2)
    top = max(0, min(resized.height - height, round((resized.height - height) * focus)))
    return resized.crop((left, top, left + width, top + height))

logo = Image.open(layout.brand_logo()).convert("RGBA")
alpha = logo.getchannel("A").point(lambda v: 255 if v > 45 else 0)
logo = logo.crop(alpha.getbbox())
def add_logo(image, x, y, width):
    lg = logo.resize((width, round(width * logo.height / logo.width)), Image.Resampling.LANCZOS)
    px = lg.load()
    for yy in range(lg.height):
        for xx in range(lg.width):
            r,g,b,a = px[xx,yy]
            if not a: continue
            if max(r,g,b) < 110: px[xx,yy] = (10,20,28,a)
            elif b > r*1.3: px[xx,yy] = (32,120,222,a)
    image.alpha_composite(lg, (x,y))

sprite = Image.open(layout.brand_icons()).convert("RGBA")
icons=[]
for i in range(4):
    icon=sprite.crop((round(sprite.width*i/4),0,round(sprite.width*(i+1)/4),sprite.height))
    a=icon.getchannel("A").point(lambda v:255 if v>70 else 0)
    icons.append(icon.crop(a.getbbox()))

data = {
    "3M": {"base":"base_3M_sedan.png", "body":"SEDAN / STEPWAY", "years":"2004–2022", "cards":[("RENAULT LOGAN SEDAN","2004–2022"),("LOGAN STEPWAY SEDAN","2004–2022")]},
    "2M": {"base":"base_2M_wagon.png", "body":"MCV WAGON", "years":"2009–2018", "cards":[("RENAULT LOGAN WAGON","2009–2018"),("RENAULT LOGAN MCV","2009–2018")]},
}

for code, d in data.items():
    base = cover(Image.open(src/d["base"]).convert("RGB"), W, H, 0.42).convert("RGBA")
    layer=Image.new("RGBA",(W,H),(0,0,0,0)); mask=Image.new("L",(W,H),0); p=mask.load()
    for y in range(465):
        a=247 if y<=320 else round(247*(1-(y-320)/145)**1.35)
        for x in range(W): p[x,y]=max(0,a)
    layer.paste((248,250,252,255),(0,0,W,H)); layer.putalpha(mask.filter(ImageFilter.GaussianBlur(7))); base.alpha_composite(layer)
    dr=ImageDraw.Draw(base); add_logo(base,849,28,187)
    dr.text((34,40),"RENAULT LOGAN",font=fit(dr,"RENAULT LOGAN",785,76,58),fill=navy)
    dr.text((34,140),d["body"],font=fit(dr,d["body"],655,54,38),fill=orange)
    dr.rounded_rectangle((720,136,1051,215),radius=14,fill=orange)
    yf=fit(dr,d["years"],291,49,37); bb=dr.textbbox((0,0),d["years"],font=yf)
    dr.text((720+(331-(bb[2]-bb[0]))//2,145),d["years"],font=yf,fill=white)
    sw=365; dr.rounded_rectangle((34,243,34+sw,333),radius=14,fill=navy)
    dr.text((59,252),f"SIZE: {code}",font=fit(dr,f"SIZE: {code}",sw-50,58,43),fill=white)
    dx=34+sw+27; dr.line((dx,249,dx,328),fill=navy,width=4)
    dr.text((dx+28,247),"ВСЕСЕЗОННЫЙ ЧЕХОЛ",font=fit(dr,"ВСЕСЕЗОННЫЙ ЧЕХОЛ",610,34,27),fill=navy)
    dr.text((dx+28,287),"ДЛЯ АВТОМОБИЛЯ",font=fit(dr,"ДЛЯ АВТОМОБИЛЯ",610,34,27),fill=navy)
    dr.rectangle((0,1220,W,H),fill=navy)
    labels=[("ЗАЩИТА","ОТ ДОЖДЯ"),("ЗАЩИТА","ОТ СНЕГА"),("ЗАЩИТА","ОТ СОЛНЦА"),("ВСЕСЕЗОННЫЙ","ЧЕХОЛ")]
    for i,(l1,l2) in enumerate(labels):
        x=i*271; ic=icons[i]; s=min(58/ic.width,58/ic.height); ic=ic.resize((round(ic.width*s),round(ic.height*s)),Image.Resampling.LANCZOS)
        base.alpha_composite(ic,(x+22,1248+(58-ic.height)//2)); dr.text((x+91,1242),l1,font=bold(18),fill=white); dr.text((x+91,1270),l2,font=bold(18),fill=white)
        if i<3: dr.line((x+270,1238,x+270,1323),fill=(118,151,177),width=2)
    for y,t,s in [(1350,"Материалы принадлежат бренду Tozaroa.",18),(1379,"За товары сторонних продавцов бренд ответственности не несёт.",17)]:
        f=regular(s); bb=dr.textbbox((0,0),t,font=f); dr.text(((W-(bb[2]-bb[0]))//2,y),t,font=f,fill=(220,230,238))
    base.convert("RGB").save(main_dir/f"Renault_Logan_{code}_主图_1086x1448.png",quality=96)

    fit_image=cover(Image.open(src/d["base"]).convert("RGB"),W,H,0.43).convert("RGBA")
    overlay=Image.new("RGBA",(W,H),(0,0,0,0)); od=ImageDraw.Draw(overlay); od.rectangle((0,0,W,730),fill=(247,250,252,238)); od.rectangle((0,1297,W,H),fill=navy); fit_image.alpha_composite(overlay)
    dr=ImageDraw.Draw(fit_image); add_logo(fit_image,856,24,176)
    dr.text((55,37),"КАК ВЫБРАТЬ",font=condensed(61),fill=navy); dr.text((55,103),"СВОЙ ВАРИАНТ",font=condensed(61),fill=orange)
    dr.rounded_rectangle((57,205,796,355),radius=24,fill=navy); dr.text((84,225),"РАЗМЕР",font=condensed(62),fill=white); dr.text((570,211),code,font=condensed(76),fill=orange)
    dr.text((60,400),"ПОДХОДИТ ДЛЯ:",font=condensed(34),fill=navy); dr.rounded_rectangle((60,452,838,458),radius=3,fill=orange)
    for i,(model,years) in enumerate(d["cards"]):
        y=490+i*93; dr.rounded_rectangle((58,y,900,y+78),radius=13,fill=(255,255,255,240),outline=(215,222,228),width=2); cy=y+39
        dr.ellipse((76,cy-21,118,cy+21),fill=navy); dr.line((88,cy,98,cy+10),fill=white,width=5); dr.line((98,cy+10,110,cy-10),fill=white,width=5)
        mf=fit_font=fit(dr,model,520,31,21,False); dr.text((137,y+20),model,font=mf,fill=navy); yf=bold(28); bb=dr.textbbox((0,0),years,font=yf); dr.text((875-(bb[2]-bb[0]),y+21),years,font=yf,fill=orange)
    dr.rectangle((0,1297,W,H),fill=navy); dr.rectangle((0,1297,W,1303),fill=orange); dr.ellipse((48,1324,118,1394),outline=orange,width=4); dr.text((76,1325),"!",font=bold(54),fill=white)
    dr.text((143,1318),"ПЕРЕД ПОКУПКОЙ ПРОВЕРЬТЕ",font=bold(31),fill=white); dr.text((143,1354),"МОДЕЛЬ, КУЗОВ И ГОД ВЫПУСКА",font=fit(dr,"МОДЕЛЬ, КУЗОВ И ГОД ВЫПУСКА",860,31,24,False),fill=white)
    fit_image.convert("RGB").save(fit_dir/f"Renault_Logan_{code}_车型适配图_1086x1448.png",quality=96)

sel=Image.new("RGBA",(W,H),(244,248,251,255)); dr=ImageDraw.Draw(sel); add_logo(sel,858,26,174)
dr.text((54,36),"ВЫБЕРИТЕ СВОЙ",font=condensed(54),fill=navy); dr.text((54,99),"RENAULT LOGAN",font=condensed(58),fill=orange); dr.text((57,178),"КУЗОВ · ГОД ВЫПУСКА · РАЗМЕР",font=bold(27),fill=navy); dr.rounded_rectangle((57,222,1017,228),radius=3,fill=orange)
for i,code in enumerate(["3M","2M"]):
    d=data[code]; y=290+i*430; dr.rounded_rectangle((52,y,1034,y+380),radius=20,fill=white,outline=(216,224,230),width=2)
    thumb=cover(Image.open(src/d["base"]).convert("RGB"),430,350,0.43); sel.alpha_composite(thumb.convert("RGBA"),(584,y+15)); dr=ImageDraw.Draw(sel)
    dr.ellipse((76,y+35,120,y+79),fill=navy); dr.line((88,y+56,98,y+66),fill=white,width=5); dr.line((98,y+66,111,y+45),fill=white,width=5)
    dr.text((139,y+28),"RENAULT LOGAN",font=bold(34),fill=navy); dr.text((76,y+104),d["body"],font=fit(dr,d["body"],480,38,27),fill=orange); dr.text((76,y+160),d["years"],font=bold(38),fill=navy)
    dr.rounded_rectangle((76,y+230,300,y+315),radius=14,fill=navy); sf=condensed(54); st=f"SIZE {code}"; bb=dr.textbbox((0,0),st,font=sf); dr.text((76+(224-(bb[2]-bb[0]))//2,y+241),st,font=sf,fill=white)
dr.rectangle((0,1272,W,H),fill=navy); dr.rectangle((0,1272,W,1278),fill=orange); dr.text((64,1310),"ПЕРЕД ЗАКАЗОМ СВЕРЬТЕ",font=bold(35),fill=white); dr.text((64,1352),"КУЗОВ И ГОД ВЫПУСКА",font=bold(35),fill=white)
sel.convert("RGB").save(selector_dir/"Renault_Logan_3M_2M_SKU共用选择图_1086x1448.png",quality=96)

# Preview montage
assets=[]
for c in ["3M","2M"]: assets += [main_dir/f"Renault_Logan_{c}_主图_1086x1448.png",fit_dir/f"Renault_Logan_{c}_车型适配图_1086x1448.png"]
assets += [selector_dir/"Renault_Logan_3M_2M_SKU共用选择图_1086x1448.png"]
tw,th=326,435; sheet=Image.new("RGB",(tw*3+40,th*2+30),(232,237,241))
for i,p in enumerate(assets): sheet.paste(Image.open(p).convert("RGB").resize((tw,th),Image.Resampling.LANCZOS),(10+(i%3)*tw,10+(i//3)*th))
sheet.save(preview_dir/"Renault_Logan_五图总览.png",quality=96)

(info_dir/"尺码分组说明.txt").write_text("Renault Logan 两个Ozon SKU：\n3M：Sedan，包含Stepway，2004–2022；实际发货尺码L。\n2M：Wagon，包含MCV，2009–2018；实际发货尺码L。\n主图与车型图按SKU分别制作；SKU选择图、共用副图及A+可在同一卡片内共用。\n",encoding="utf-8")

zip_path = pack.build(v.slug)
print({"main":2,"fitment":2,"selector":1,"zip":str(zip_path)})
