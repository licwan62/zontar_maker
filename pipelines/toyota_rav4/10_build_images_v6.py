from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pathlib import Path
import zipfile

import sys; from pathlib import Path as _P; sys.path.insert(0, str(_P(__file__).resolve().parents[2] / "src"))
from zontar import layout, pack
# Renders V6 into a staging folder. Source files keep the historical YS name; the SKU is labelled XS (as delivered).
# Verified 2026-09-29: M/S are pixel-identical to the package; XS is visually identical (the delivered XS files were re-encoded once).
v=layout.vehicle('toyota_rav4'); src=v.source; out=layout.asset('outputs/vehicles/toyota_rav4/staging/V6'); out.mkdir(parents=True,exist_ok=True)
W,H=1086,1448; navy=(4,24,44); orange=(244,91,22); white=(255,255,255)
regular=r'C:\Windows\Fonts\tahoma.ttf'; bold=r'C:\Windows\Fonts\ariblk.ttf'; condensed=r'C:\Windows\Fonts\tahomabd.ttf'
def F(n,b=False,c=False):return ImageFont.truetype(condensed if c else (bold if b else regular),n)
def text(d,xy,s,n,color=white,b=False,c=False,stroke=0):d.text(xy,s,font=F(n,b,c),fill=color,stroke_width=stroke,stroke_fill=navy)
def bbox(d,s,n,b=False,c=False):return d.textbbox((0,0),s,font=F(n,b,c))
def center(d,y,s,n,color=white,b=False,c=False):
    bb=bbox(d,s,n,b,c);text(d,((W-(bb[2]-bb[0]))//2,y),s,n,color,b,c)
def cover(im,w,h,focus=.5):
    scale=max(w/im.width,h/im.height); z=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.LANCZOS)
    left=(z.width-w)//2;top=max(0,min(z.height-h,round((z.height-h)*focus)));return z.crop((left,top,left+w,top+h))
def gradient(im,y0,y1,color,max_alpha,reverse=False):
    lay=Image.new('RGBA',im.size,(0,0,0,0));p=lay.load()
    for y in range(max(0,y0),min(im.height,y1)):
        q=(y-y0)/max(1,(y1-y0));a=round(max_alpha*((1-q) if reverse else q)**1.15)
        for x in range(im.width):p[x,y]=(*color,a)
    im.alpha_composite(lay)
logo=Image.open(layout.brand_logo()).convert('RGBA')
al=logo.getchannel('A').point(lambda v:255 if v>45 else 0);logo=logo.crop(al.getbbox())
def brand(im,x,y,w):
    z=logo.resize((w,round(w*logo.height/logo.width)),Image.Resampling.LANCZOS);px=z.load()
    for yy in range(z.height):
        for xx in range(z.width):
            r,g,b,a=px[xx,yy]
            if a>0 and max(r,g,b)<110:px[xx,yy]=(255,255,255,a)
            elif a>0 and b>r*1.4:px[xx,yy]=(90,177,255,a)
    im.alpha_composite(z,(x,y))
sprite=Image.open(layout.brand_icons()).convert('RGBA')
icon_cells=[]
for i in range(4):
    x0=round(sprite.width*i/4);x1=round(sprite.width*(i+1)/4)
    cell=sprite.crop((x0,0,x1,sprite.height))
    alpha=cell.getchannel('A').point(lambda v:255 if v>70 else 0)
    cell=cell.crop(alpha.getbbox())
    icon_cells.append(cell)
data={
'M':{'body':'5-ДВЕРНЫЙ SUV · LONG','years':'2005–2026','fit':['2025–2026  ·  5 дверей','2018–2026  ·  5 дверей','2015–2019  ·  5 дверей','2010–2016  ·  Long, 5 дверей','2005–2010  ·  Long, 5 дверей']},
'S':{'body':'5-ДВЕРНЫЙ SUV','years':'1994–2016','fit':['2012–2015  ·  5 дверей','2010–2016  ·  5 дверей','2005–2010  ·  5 дверей','2003–2006  ·  5 дверей','2000–2003  ·  5 дверей','1994–2000  ·  5 дверей']},
'YS':{'body':'3 ДВЕРИ · КОРОТКАЯ БАЗА','years':'1994–2006','fit':['2003–2006  ·  3 двери','2000–2003  ·  3 двери','1994–2000  ·  3 двери','1994–2000  ·  короткая база']}}

LABEL={'YS':'XS'}  # source-file code -> SKU shown on images and in file names
for code,v in data.items():
    lab=LABEL.get(code,code)
    photo=Image.open(src/f'base_{code}.png').convert('RGB')
    im=photo.resize((W,H),Image.Resampling.LANCZOS).convert('RGBA');gradient(im,0,510,navy,220,True);gradient(im,1050,H,navy,245)
    d=ImageDraw.Draw(im)
    brand(im,840,37,198)
    text(d,(48,43),'TOYOTA RAV4',72,white,True)
    text(d,(49,132),v['body'],38,orange,True,c=True)
    d.rounded_rectangle((50,192,374,266),radius=12,fill=(*orange,242))
    text(d,(73,204),v['years'],42,white,True,c=True)
    d.rounded_rectangle((50,290,315,370),radius=12,fill=(*navy,240))
    text(d,(73,301),'SIZE: '+lab,44,white,True,c=True)
    d.rectangle((0,1222,W,H),fill=(*navy,248))
    labels=[('ЗАЩИТА','ОТ ДОЖДЯ'),('ЗАЩИТА','ОТ СНЕГА'),('ЗАЩИТА','ОТ СОЛНЦА'),('ДЛЯ ПАРКОВКИ','В ЛЮБОЙ СЕЗОН')]
    for i,(a,b) in enumerate(labels):
        x=i*271
        cell=icon_cells[i]; scale=min(62/cell.width,62/cell.height); z=cell.resize((round(cell.width*scale),round(cell.height*scale)),Image.Resampling.LANCZOS)
        im.alpha_composite(z,(x+24,1250+(62-z.height)//2))
        text(d,(x+97,1244),a,18,white,True,c=True);text(d,(x+97,1272),b,18,white,True,c=True)
        if i<3:d.line((x+270,1240,x+270,1326),fill=(113,144,168),width=2)
    center(d,1350,'Материалы принадлежат бренду Tozaroa.',18,(215,228,237))
    center(d,1378,'За товары сторонних продавцов бренд ответственности не несёт.',17,(215,228,237))
    im.convert('RGB').save(out/f'RAV4_{lab}_主图_V6_1086x1448.png')

    car=Image.open(src/f'vehicle_{code}.png').convert('RGB')
    im=cover(car.crop((0,250,1086,1350)),W,H,.54).convert('RGBA')
    gradient(im,0,450,navy,225,True);gradient(im,620,H,navy,245)
    d=ImageDraw.Draw(im);brand(im,842,27,195)
    text(d,(45,37),'TOYOTA RAV4',72,white,True,c=True)
    text(d,(49,126),v['body'],29,(255,132,72),True,c=True)
    text(d,(49,175),v['years'],38,white,True,c=True)
    d.line((48,790,1038,790),fill=(255,255,255,180),width=2)
    text(d,(49,805),'ПОДХОДИТ ДЛЯ',49,white,True,c=True)
    d.rounded_rectangle((804,803,1038,872),radius=11,fill=(*orange,245))
    text(d,(830,815),'SIZE '+lab,42,white,True,c=True)
    y=895; available=430; gap=4; row_h=(available-gap*(len(v['fit'])-1))//len(v['fit'])
    for j,s in enumerate(v['fit']):
        yy=y+j*(row_h+gap)
        d.rounded_rectangle((46,yy,1040,yy+row_h),radius=8,fill=(8,39,70,198))
        d.rectangle((46,yy,54,yy+row_h),fill=orange)
        text(d,(81,yy+(row_h-41)//2),s,38,white,True,c=True)
    center(d,1362,'СВЕРЬТЕ КУЗОВ И ГОД ПЕРЕД ЗАКАЗОМ',30,white,True,c=True)
    im.convert('RGB').save(out/f'RAV4_{lab}_车型适配图_V6_1086x1448.png')

# One visual language for the shared selector: every row is a full-bleed vehicle panel.
canvas=Image.new('RGBA',(W,H),(*navy,255));d=ImageDraw.Draw(canvas)
text(d,(45,25),'ВЫБЕРИТЕ СВОЙ RAV4',55,white,True,c=True)
text(d,(48,93),'КУЗОВ · ГОД ВЫПУСКА · КОД',28,(196,218,234),False,c=True)
brand(canvas,842,21,192)
for i,code in enumerate(['M','S','YS']):
    v=data[code]; y=165+i*407
    car=Image.open(src/f'vehicle_{code}.png').convert('RGB').crop((0,330,1086,1240))
    panel=cover(car,W,393,.48).convert('RGBA')
    # Left-to-right navy shade integrates text with the vehicle photograph.
    shade=Image.new('RGBA',(W,393),(0,0,0,0));p=shade.load()
    for xx in range(W):
        aa=round(246*(1-xx/W)**1.25+35)
        for yy in range(393):p[xx,yy]=(*navy,min(255,aa))
    panel.alpha_composite(shade);canvas.alpha_composite(panel,(0,y));d=ImageDraw.Draw(canvas)
    d.rectangle((0,y,13,y+393),fill=orange)
    text(d,(45,y+19),'RAV4',42,white,True,c=True)
    text(d,(45,y+67),v['body'],28,(255,140,83),True,c=True)
    text(d,(45,y+109),v['years'],39,white,True,c=True)
    yy=y+165
    for row in v['fit']:
        text(d,(47,yy),row,23,white,False,c=True);yy+=32
    d.rounded_rectangle((853,y+288,1030,y+370),radius=13,fill=(*orange,240))
    text(d,(881,y+301),LABEL.get(code,code),56,white,True,c=True)
    if i<2:d.line((0,y+401,W,y+401),fill=(255,255,255,140),width=2)
d=ImageDraw.Draw(canvas);center(d,1400,'СВЕРЬТЕ МОДЕЛЬ, КУЗОВ И ГОД',26,white,True,c=True)
canvas.convert('RGB').save(out/'RAV4_M_S_XS_SKU共用选择图_V6_1086x1448.png')

print(out)
