from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import zipfile

root=Path('Toyota_RAV4_灰色无耳_Tozaroa_上架包')
src=root/'01_SKU专属图'; out=root/'06_新版设计V3'; out.mkdir(exist_ok=True)
W,H=1086,1448; navy='#062746'; orange='#e95209'; pale='#f4f7fa'; white='#ffffff'
font_regular=r'C:\Windows\Fonts\arial.ttf'; font_bold=r'C:\Windows\Fonts\arialbd.ttf'
def font(n,b=False): return ImageFont.truetype(font_bold if b else font_regular,n)
logo=Image.open(r'C:\Users\Lenovo\Desktop\exec-d3683c74-61df-4003-b326-40f68d3b800e.png').convert('RGBA')
alpha=logo.getchannel('A').point(lambda v: 255 if v>40 else 0)
logo=logo.crop(alpha.getbbox())
def brand(im,x,y,w):
    h=round(logo.height*w/logo.width); im.alpha_composite(logo.resize((w,h),Image.Resampling.LANCZOS),(x,y))
def txt(d,x,y,s,n=30,color=navy,b=True): d.text((x,y),s,font=font(n,b),fill=color)
def centered(d,y,s,n=30,color=navy,b=True):
    bb=d.textbbox((0,0),s,font=font(n,b)); txt(d,(W-(bb[2]-bb[0]))//2,y,s,n,color,b)
def fit(im,w,h):
    scale=max(w/im.width,h/im.height); z=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.LANCZOS)
    return z.crop(((z.width-w)//2,(z.height-h)//2,(z.width+w)//2,(z.height+h)//2))
def icon(d,x,y,k):
    if k=='rain':
        d.arc((x-19,y-16,x+19,y+12),180,360,fill=white,width=4)
        for a in [-12,0,12]: d.line((x+a,y+10,x+a-5,y+26),fill=white,width=3)
    elif k=='snow':
        for a in [(x,y-23,x,y+23),(x-20,y-12,x+20,y+12),(x-20,y+12,x+20,y-12)]: d.line(a,fill=white,width=4)
    elif k=='sun':
        d.ellipse((x-10,y-10,x+10,y+10),outline=white,width=3)
        for dx,dy in [(0,-22),(0,22),(-22,0),(22,0)]: d.line((x+dx*.65,y+dy*.65,x+dx,y+dy),fill=white,width=3)
    else:
        d.ellipse((x-18,y-9,x+12,y+10),outline=white,width=3);d.ellipse((x-4,y-17,x+20,y+6),outline=white,width=3)

data={
'M':{'body':'5-ДВЕРНЫЙ SUV · LONG','years':'2005–2026','fit':['2025–2026   5 дверей','2018–2026   5 дверей','2015–2019   5 дверей','2010–2016   Long · 5 дверей','2005–2010   Long · 5 дверей']},
'S':{'body':'5-ДВЕРНЫЙ SUV','years':'1994–2016','fit':['2012–2015   5 дверей','2010–2016   5 дверей','2005–2010   5 дверей','2003–2006   5 дверей','2000–2003   5 дверей','1994–2000   5 дверей']},
'YS':{'body':'3 ДВЕРИ · КОРОТКАЯ БАЗА','years':'1994–2006','fit':['2003–2006   3 двери','2000–2003   3 двери','1994–2000   3 двери','1994–2000   короткая база']}}

for code,v in data.items():
    # Main: photograph occupies the dominant 80% of the page.
    photo=Image.open(src/f'base_{code}.png').convert('RGB'); im=Image.new('RGBA',(W,H),pale)
    im.paste(fit(photo.crop((0,240,photo.width,1330)),W,1128),(0,205)); d=ImageDraw.Draw(im)
    d.rectangle((0,0,W,232),fill=(246,249,251,245))
    txt(d,48,42,'TOYOTA RAV4',69)
    txt(d,52,125,v['body'],32,orange)
    brand(im,836,22,205)
    d.rounded_rectangle((49,184,395,259),radius=14,fill=navy);txt(d,72,196,v['years'],40,white)
    d.rounded_rectangle((800,179,1038,260),radius=14,fill=orange);txt(d,825,195,'SIZE '+code,39,white)
    d.rectangle((0,1270,W,H),fill=navy)
    labels=[('rain','ДОЖДЬ'),('snow','СНЕГ'),('sun','СОЛНЦЕ'),('dust','ПЫЛЬ')]
    for i,(k,s) in enumerate(labels):
        cx=93+270*i; icon(d,cx,1328,k);txt(d,cx+42,1309,s,25,white)
        if i<3:d.line((270*(i+1),1294,270*(i+1),1372),fill='#53718a',width=2)
    disclaimer='Материалы принадлежат бренду Tozaroa.'
    disclaimer2='За товары сторонних продавцов бренд ответственности не несёт.'
    centered(d,1380,disclaimer,20,'#d9e5ef',False);centered(d,1407,disclaimer2,20,'#d9e5ef',False)
    im.convert('RGB').save(out/f'RAV4_{code}_主图_V3_1086x1448.png')

    # Fitment: vehicle photo plus dense full-height selection rows.
    car=Image.open(src/f'vehicle_{code}.png').convert('RGB'); im=Image.new('RGBA',(W,H),white);im.paste(fit(car,W,772),(0,0));d=ImageDraw.Draw(im)
    d.rectangle((0,0,W,212),fill=(246,249,251,238));txt(d,44,44,'TOYOTA RAV4',65);txt(d,49,128,v['body']+'  '+v['years'],28,orange);brand(im,838,24,202)
    d.rectangle((0,732,W,1448),fill=white);d.rectangle((0,732,W,828),fill=navy)
    txt(d,49,752,'ТОЧНАЯ СОВМЕСТИМОСТЬ',41,white)
    d.rounded_rectangle((821,741,1032,818),15,fill=orange);txt(d,853,753,'SIZE '+code,35,white)
    start=841; available=500; gap=7; rh=(available-(len(v['fit'])-1)*gap)//len(v['fit'])
    for i,s in enumerate(v['fit']):
        y=start+i*(rh+gap)
        d.rounded_rectangle((43,y,1043,y+rh),13,fill='#eef3f7')
        d.rectangle((43,y,57,y+rh),fill=orange)
        txt(d,83,y+(rh-38)//2,s,37)
    d.rectangle((0,1362,W,H),fill=orange)
    centered(d,1378,'ПРОВЕРЬТЕ КУЗОВ И ГОД ПЕРЕД ЗАКАЗОМ',32,white)
    im.convert('RGB').save(out/f'RAV4_{code}_车型适配图_V3_1086x1448.png')

# Shared selector: three broad visual rows, no microtext or dead white area.
im=Image.new('RGBA',(W,H),white);d=ImageDraw.Draw(im)
d.rectangle((0,0,W,182),fill=navy)
txt(d,44,31,'ВЫБЕРИТЕ СВОЙ RAV4',56,white)
txt(d,48,112,'КУЗОВ · ГОД ВЫПУСКА · КОД',28,'#d7e5ef')
d.rounded_rectangle((840,14,1053,105),13,fill=white);brand(im,845,20,197)
for i,code in enumerate(['M','S','YS']):
    v=data[code]; y=192+i*392
    d.rounded_rectangle((25,y,1061,y+380),18,fill='#f4f7fa',outline=navy,width=3)
    d.rounded_rectangle((25,y,191,y+380),18,fill=navy)
    txt(d,57,y+128,code,76,white)
    car=Image.open(src/f'vehicle_{code}.png').convert('RGB')
    im.paste(fit(car,354,340),(202,y+20))
    txt(d,578,y+23,'TOYOTA RAV4',39)
    txt(d,578,y+81,v['body'],25,orange)
    txt(d,578,y+126,v['years'],36)
    yy=y+183
    for row in v['fit']:
        txt(d,579,yy,row,22,navy);yy+=32
d.rectangle((0,1370,W,H),fill=orange)
centered(d,1389,'СВЕРЬТЕ МОДЕЛЬ, КУЗОВ И ГОД',34,white)
im.convert('RGB').save(out/'RAV4_M_S_YS_SKU共用选择图_V3_1086x1448.png')

zpath=root.parent/'Toyota_RAV4_灰色无耳_Tozaroa_新版设计V3.zip'
with zipfile.ZipFile(zpath,'w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(out.glob('*.png')):z.write(p,Path('Toyota_RAV4_新版设计V3')/p.name)
    for p in sorted((root/'04_上架资料').glob('*')):
        if p.suffix.lower() in {'.csv','.txt'}:z.write(p,Path('Toyota_RAV4_新版设计V3')/'上架资料'/p.name)
print(zpath)
