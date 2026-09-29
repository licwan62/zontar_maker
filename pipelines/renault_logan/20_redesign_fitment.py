from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pathlib import Path
import zipfile

import sys; from pathlib import Path as _P; sys.path.insert(0, str(_P(__file__).resolve().parents[2] / "src"))
from zontar import layout, pack
v=layout.vehicle('renault_logan').ensure_dirs(); src=v.source; fitdir=v.fitment; seldir=v.selector; preview=v.preview
W,H=1086,1448; navy=(3,37,67); orange=(232,71,5); white=(255,255,255); pale=(241,246,249)
impact=r'C:\Windows\Fonts\impact.ttf'; arialb=r'C:\Windows\Fonts\arialbd.ttf'; arial=r'C:\Windows\Fonts\arial.ttf'
def cf(s): return ImageFont.truetype(impact,s)
def bf(s): return ImageFont.truetype(arialb,s)
def rf(s): return ImageFont.truetype(arial,s)
def fitfont(d,t,w,s,minimum=18,font='bold'):
    while s>minimum:
        f=cf(s) if font=='condensed' else bf(s)
        if d.textbbox((0,0),t,font=f)[2]<=w:return f
        s-=1
    return cf(minimum) if font=='condensed' else bf(minimum)
def cover(im,w,h,focus=.5):
    sc=max(w/im.width,h/im.height); im=im.resize((round(im.width*sc),round(im.height*sc)),Image.Resampling.LANCZOS)
    l=(im.width-w)//2; top=max(0,min(im.height-h,round((im.height-h)*focus))); return im.crop((l,top,l+w,top+h))
def place_rgba(dst,im,box):
    x,y,w,h=box; sc=min(w/im.width,h/im.height); im=im.resize((round(im.width*sc),round(im.height*sc)),Image.Resampling.LANCZOS)
    dst.alpha_composite(im,(x+(w-im.width)//2,y+(h-im.height)//2))
logo=Image.open(layout.brand_logo()).convert('RGBA'); a=logo.getchannel('A').point(lambda v:255 if v>45 else 0); logo=logo.crop(a.getbbox())
def addlogo(im,x,y,w):
    lg=logo.resize((w,round(w*logo.height/logo.width)),Image.Resampling.LANCZOS); px=lg.load()
    for yy in range(lg.height):
      for xx in range(lg.width):
       r,g,b,a=px[xx,yy]
       if a: px[xx,yy]=(10,20,28,a) if max(r,g,b)<110 else ((32,120,222,a) if b>r*1.3 else (r,g,b,a))
    im.alpha_composite(lg,(x,y))
def checkmark(d,cx,cy,r=23):
    d.ellipse((cx-r,cy-r,cx+r,cy+r),fill=navy); d.line((cx-10,cy,cx-2,cy+9),fill=white,width=5); d.line((cx-2,cy+9,cx+12,cy-12),fill=white,width=5)
data={
 '3M':dict(body='SEDAN / STEPWAY',years='2004–2022',vehicle='vehicle_sedan_cutout.png',scene='base_3M_sedan.png',line1='RENAULT LOGAN SEDAN',line2='ВКЛЮЧАЯ STEPWAY'),
 '2M':dict(body='MCV WAGON',years='2009–2018',vehicle='vehicle_wagon_cutout.png',scene='base_2M_wagon.png',line1='RENAULT LOGAN MCV',line2='КУЗОВ УНИВЕРСАЛ')}

# SKU-specific fitment master: large recognizable uncovered vehicle, compact information rail.
for code,d in data.items():
    scene=cover(Image.open(src/d['scene']).convert('RGB'),W,H,.48).filter(ImageFilter.GaussianBlur(8)).convert('RGBA')
    veil=Image.new('RGBA',(W,H),(247,250,252,205)); scene.alpha_composite(veil)
    dr=ImageDraw.Draw(scene); dr.rectangle((0,0,W,18),fill=orange); addlogo(scene,842,35,190)
    dr.text((54,48),'RENAULT LOGAN',font=cf(76),fill=navy)
    dr.text((56,139),d['body'],font=cf(59),fill=orange)
    dr.rounded_rectangle((56,220,454,326),radius=18,fill=navy); dr.text((82,233),'РАЗМЕР',font=cf(51),fill=white); dr.text((326,225),code,font=cf(67),fill=orange)
    dr.rounded_rectangle((478,220,879,326),radius=18,fill=orange); yf=cf(49); bb=dr.textbbox((0,0),d['years'],font=yf); dr.text((478+(401-(bb[2]-bb[0]))//2,242),d['years'],font=yf,fill=white)
    dr.text((57,370),'ТОЧНАЯ ПРОВЕРКА СОВМЕСТИМОСТИ',font=bf(29),fill=navy); dr.rectangle((57,415,1028,421),fill=orange)
    dr.rounded_rectangle((55,449,1030,610),radius=22,fill=(255,255,255,242),outline=(207,219,228),width=2)
    checkmark(dr,91,500,22); dr.text((132,474),d['line1'],font=fitfont(dr,d['line1'],830,39,29),fill=navy)
    checkmark(dr,91,559,22); dr.text((132,533),d['line2'],font=fitfont(dr,d['line2'],830,38,28),fill=orange)
    # pedestal and huge vehicle
    dr.ellipse((90,1095,1015,1280),fill=(17,49,74,32)); veh=Image.open(src/d['vehicle']).convert('RGBA'); place_rgba(scene,veh,(18,595,1050,690))
    dr.rounded_rectangle((58,1180,1028,1285),radius=19,fill=(255,255,255,235),outline=(207,219,228),width=2)
    dr.text((82,1201),'МОДЕЛЬ',font=cf(30),fill=orange); dr.text((82,1237),d['line1'],font=fitfont(dr,d['line1'],620,32,25),fill=navy)
    dr.rounded_rectangle((801,1196,997,1270),radius=13,fill=navy); sf=cf(45); st=f'SIZE {code}'; bb=dr.textbbox((0,0),st,font=sf); dr.text((801+(196-(bb[2]-bb[0]))//2,1206),st,font=sf,fill=white)
    dr.rectangle((0,1320,W,H),fill=navy); dr.rectangle((0,1320,W,1327),fill=orange); dr.ellipse((48,1350,112,1414),outline=orange,width=4); dr.text((73,1348),'!',font=bf(48),fill=white)
    dr.text((138,1343),'ПЕРЕД ЗАКАЗОМ СВЕРЬТЕ',font=bf(30),fill=white); dr.text((138,1380),'КУЗОВ И ГОД ВЫПУСКА',font=bf(30),fill=white)
    scene.convert('RGB').save(fitdir/f'Renault_Logan_{code}_车型适配图_1086x1448.png',quality=96)

# Shared selector: one strong comparison board, large distinct silhouettes and oversized size codes.
im=Image.new('RGBA',(W,H),pale+(255,)); dr=ImageDraw.Draw(im); dr.rectangle((0,0,W,18),fill=orange); addlogo(im,850,32,184)
dr.text((50,45),'ВЫБЕРИТЕ',font=cf(63),fill=navy); dr.text((50,116),'СВОЙ ВАРИАНТ',font=cf(63),fill=orange)
dr.text((54,198),'КУЗОВ',font=bf(25),fill=navy); dr.text((175,198),'•',font=bf(25),fill=orange); dr.text((207,198),'ГОД ВЫПУСКА',font=bf(25),fill=navy); dr.text((437,198),'•',font=bf(25),fill=orange); dr.text((468,198),'РАЗМЕР',font=bf(25),fill=navy); dr.rectangle((53,240,1032,247),fill=orange)
for i,code in enumerate(['3M','2M']):
    d=data[code]; y=282+i*475; card=(44,y,1042,y+438)
    dr.rounded_rectangle(card,radius=26,fill=white,outline=(201,215,225),width=3)
    dr.rounded_rectangle((62,y+22,272,y+126),radius=18,fill=navy); dr.text((82,y+37),'SIZE',font=cf(35),fill=white); dr.text((174,y+23),code,font=cf(67),fill=orange)
    dr.text((62,y+151),'RENAULT LOGAN',font=cf(44),fill=navy); dr.text((62,y+208),d['body'],font=cf(39),fill=orange)
    dr.rounded_rectangle((62,y+270,352,y+335),radius=12,fill=(239,244,247)); yf=bf(31); bb=dr.textbbox((0,0),d['years'],font=yf); dr.text((62+(290-(bb[2]-bb[0]))//2,y+284),d['years'],font=yf,fill=navy)
    checkmark(dr,89,y+382,20); dr.text((124,y+363),'ПОДХОДИТ',font=bf(26),fill=navy); dr.text((124,y+393),'К ЭТОМУ КУЗОВУ',font=bf(22),fill=(69,91,110))
    veh=Image.open(src/d['vehicle']).convert('RGBA'); place_rgba(im,veh,(336,y+18,690,402)); dr=ImageDraw.Draw(im)
    # orange body marker integrated with car side
    dr.rounded_rectangle((696,y+354,1014,y+415),radius=12,fill=orange); body=d['body']; f=fitfont(dr,body,286,31,22); bb=dr.textbbox((0,0),body,font=f); dr.text((696+(318-(bb[2]-bb[0]))//2,y+366),body,font=f,fill=white)
dr.rectangle((0,1260,W,H),fill=navy); dr.rectangle((0,1260,W,1267),fill=orange)
dr.text((54,1294),'1',font=cf(58),fill=orange); dr.text((102,1296),'СВЕРЬТЕ КУЗОВ',font=bf(27),fill=white)
dr.text((407,1294),'2',font=cf(58),fill=orange); dr.text((455,1296),'СВЕРЬТЕ ГОД',font=bf(27),fill=white)
dr.text((738,1294),'3',font=cf(58),fill=orange); dr.text((786,1296),'ВЫБЕРИТЕ SIZE',font=bf(27),fill=white)
dr.text((55,1380),'SEDAN / STEPWAY = 3M     •     MCV WAGON = 2M',font=fitfont(dr,'SEDAN / STEPWAY = 3M     •     MCV WAGON = 2M',975,29,22),fill=white)
im.convert('RGB').save(seldir/'Renault_Logan_3M_2M_SKU共用选择图_1086x1448.png',quality=96)

# refresh montage and delivery zip
assets=[]
for c in ['3M','2M']: assets += [v.main/f'Renault_Logan_{c}_主图_1086x1448.png',fitdir/f'Renault_Logan_{c}_车型适配图_1086x1448.png']
assets += [seldir/'Renault_Logan_3M_2M_SKU共用选择图_1086x1448.png']
tw,th=326,435; sheet=Image.new('RGB',(tw*3+40,th*2+30),(232,237,241))
for i,p in enumerate(assets): sheet.paste(Image.open(p).convert('RGB').resize((tw,th),Image.Resampling.LANCZOS),(10+(i%3)*tw,10+(i//3)*th))
sheet.save(preview/'Renault_Logan_五图总览.png',quality=96)
pack.build(v.slug)
print('redesigned',*[str(p) for p in [fitdir,seldir,preview/'Renault_Logan_五图总览.png']])
