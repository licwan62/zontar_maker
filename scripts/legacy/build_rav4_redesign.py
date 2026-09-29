from PIL import Image,ImageDraw,ImageFont,ImageFilter
from pathlib import Path
import zipfile

R=Path('Toyota_RAV4_灰色无耳_Tozaroa_上架包'); SRC=R/'01_SKU专属图'; OUT=R/'05_新版设计V2'
W,H=1086,1448; NAV=(5,35,64,255); ORG=(226,76,0,255); WHITE=(255,255,255,255); GRAY=(234,239,243,255)
AR=r'C:\Windows\Fonts\arial.ttf'; BD=r'C:\Windows\Fonts\arialbd.ttf'
def F(n,b=False): return ImageFont.truetype(BD if b else AR,n)
logo=Image.open(r'C:\Users\Lenovo\Desktop\exec-d3683c74-61df-4003-b326-40f68d3b800e.png').convert('RGBA'); logo=logo.crop(logo.getbbox())
def add_logo(im,x=45,y=32,w=230):
 s=w/logo.width; im.alpha_composite(logo.resize((w,int(logo.height*s)),Image.Resampling.LANCZOS),(x,y))
def center(d,y,t,f,fill):
 b=d.textbbox((0,0),t,font=f); d.text(((W-b[2]+b[0])//2,y),t,font=f,fill=fill)
def fit(im,box):
 x0,y0,x1,y1=box; tw,th=x1-x0,y1-y0; s=max(tw/im.width,th/im.height); z=im.resize((int(im.width*s),int(im.height*s)),Image.Resampling.LANCZOS); return z.crop(((z.width-tw)//2,(z.height-th)//2,(z.width+tw)//2,(z.height+th)//2))
def icon(d,cx,cy,kind):
 if kind=='rain':
  d.arc((cx-25,cy-30,cx+25,cy+10),180,360,fill='white',width=5); d.line((cx-25,cy-10,cx+25,cy-10),fill='white',width=5)
  for q in (-18,0,18): d.line((cx+q,cy+4,cx+q-7,cy+20),fill='white',width=4)
 elif kind=='snow':
  for a,b in [((cx,cy-28),(cx,cy+25)),((cx-25,cy-15),(cx+25,cy+15)),((cx-25,cy+15),(cx+25,cy-15))]: d.line(a+b,fill='white',width=4)
 elif kind=='sun':
  d.ellipse((cx-14,cy-14,cx+14,cy+14),outline='white',width=4)
  for dx,dy in [(0,-30),(0,30),(-30,0),(30,0),(-22,-22),(22,22),(-22,22),(22,-22)]: d.line((cx+dx*.65,cy+dy*.65,cx+dx,cy+dy),fill='white',width=4)
 else:
  d.ellipse((cx-25,cy-17,cx+20,cy+12),outline='white',width=4); d.ellipse((cx-5,cy-27,cx+30,cy+8),outline='white',width=4)

D={
'M':('SUV 5 ДВЕРЕЙ · LONG','2005–2026',['2025–2026  SUV 5 дв.','2018–2026  SUV 5 дв.','2015–2019  SUV 5 дв.','2010–2016  Long 5 дв.','2005–2010  Long 5 дв.']),
'S':('SUV 5 ДВЕРЕЙ','1994–2016',['2012–2015  SUV 5 дв.','2010–2016  SUV 5 дв.','2005–2010  SUV 5 дв.','2003–2006  SUV 5 дв.','2000–2003  SUV 5 дв.','1994–2000  SUV 5 дв.']),
'YS':('КОРОТКАЯ БАЗА · 3 ДВЕРИ','1994–2006',['2003–2006  SUV 3 дв.','2000–2003  SUV 3 дв.','1994–2000  SUV 3 дв.','1994–2000  короткая база'])}

for code,(body,years,rows) in D.items():
 # Main image
 bg=Image.open(SRC/f'base_{code}.png').convert('RGBA').resize((W,H),Image.Resampling.LANCZOS)
 top=Image.new('RGBA',(W,390),(247,249,251,238)); bg.alpha_composite(top,(0,0)); d=ImageDraw.Draw(bg)
 add_logo(bg,825,18,205)
 d.text((55,120),'TOYOTA RAV4',font=F(68,True),fill=NAV)
 d.text((55,205),body,font=F(37,True),fill=ORG)
 d.rounded_rectangle((55,260,440,342),18,fill=NAV); d.text((82,274),years,font=F(44,True),fill=WHITE)
 d.rounded_rectangle((785,245,1020,355),20,fill=ORG); center_badge=f'SIZE {code}'; b=d.textbbox((0,0),center_badge,font=F(44,True)); d.text((785+(235-b[2])/2,274),center_badge,font=F(44,True),fill=WHITE)
 d.rectangle((0,H-185,W,H),fill=NAV)
 items=[('rain','ОТ ДОЖДЯ'),('snow','ОТ СНЕГА'),('sun','ОТ СОЛНЦА'),('dust','ОТ ПЫЛИ')]
 for i,(ic,tx) in enumerate(items):
  cx=135+i*270; icon(d,cx,H-115,ic); d.text((cx+42,H-135),tx,font=F(25,True),fill=WHITE)
 d.text((cx+42,H-102),'ДЛЯ ПАРКОВКИ',font=F(17),fill=(191,210,222,255))
 disc='Материалы принадлежат бренду Tozaroa · За товары сторонних продавцов бренд ответственности не несёт.'
 d.text((48,H-35),disc,font=F(17),fill=(210,223,232,255))
 bg.convert('RGB').save(OUT/f'RAV4_{code}_主图_V2_1086x1448.png',quality=96)

 # Fitment image
 car=Image.open(SRC/f'vehicle_{code}.png').convert('RGBA')
 page=Image.new('RGBA',(W,H),GRAY); page.alpha_composite(fit(car,(0,0,W,820)),(0,0)); d=ImageDraw.Draw(page)
 d.rectangle((0,0,W,245),fill=(245,248,250,225)); add_logo(page,840,15,190)
 d.text((55,105),'TOYOTA RAV4',font=F(65,True),fill=NAV); d.text((55,180),f'{body}   {years}',font=F(30,True),fill=ORG)
 card=(45,745,W-45,H-65); d.rounded_rectangle(card,28,fill=WHITE,outline=NAV,width=5)
 d.rounded_rectangle((45,745,W-45,850),28,fill=NAV); center(d,768,'ПРОВЕРЬТЕ СОВМЕСТИМОСТЬ',F(38,True),WHITE)
 d.rounded_rectangle((80,890,345,1160),30,fill=NAV); center_x=212; b=d.textbbox((0,0),code,font=F(115,True)); d.text((center_x-(b[2]-b[0])/2,930),code,font=F(115,True),fill=WHITE)
 d.text((108,1080),'РАЗМЕР',font=F(32,True),fill=(195,214,226,255))
 y=885
 for row in rows:
  d.text((395,y),row,font=F(25,True),fill=NAV); d.line((390,y+40,965,y+40),fill=(211,220,226,255),width=2); y+=48
 d.rectangle((45,H-145,W-45,H-65),fill=ORG); center(d,H-128,'СВЕРЬТЕ КУЗОВ И ГОД ПЕРЕД ЗАКАЗОМ',F(29,True),WHITE)
 page.convert('RGB').save(OUT/f'RAV4_{code}_车型适配图_V2_1086x1448.png',quality=96)

# Shared selector with real vehicle thumbnails and dense hierarchy
page=Image.new('RGBA',(W,H),WHITE); d=ImageDraw.Draw(page); d.rectangle((0,0,W,230),fill=NAV); d.rounded_rectangle((825,12,1048,105),18,fill=WHITE); add_logo(page,842,18,190)
center(d,75,'ВЫБЕРИТЕ СВОЙ RAV4',F(58,True),WHITE); center(d,155,'МОДЕЛЬ · КУЗОВ · ГОД ВЫПУСКА',F(29,True),(215,228,237,255))
y=255
for code,(body,years,rows) in D.items():
 d.rounded_rectangle((35,y,W-35,y+335),25,fill=(247,249,250,255),outline=NAV,width=4)
 d.rectangle((35,y,205,y+335),fill=NAV); b=d.textbbox((0,0),code,font=F(82,True)); d.text((120-(b[2]-b[0])/2,y+100),code,font=F(82,True),fill=WHITE)
 car=Image.open(SRC/f'vehicle_{code}.png').convert('RGBA'); thumb=fit(car,(0,0,285,285)); page.alpha_composite(thumb,(220,y+25))
 d.text((530,y+30),'TOYOTA RAV4',font=F(35,True),fill=NAV); d.text((530,y+78),body,font=F(24,True),fill=ORG); d.text((530,y+116),years,font=F(33,True),fill=NAV)
 yy=y+165
 for row in rows:
  d.text((530,yy),row,font=F(19,True),fill=(57,70,80,255)); yy+=27
 y+=360
d.rectangle((0,H-100,W,H),fill=ORG); center(d,H-78,'СВЕРЬТЕ МОДЕЛЬ, КУЗОВ И ГОД ПЕРЕД ЗАКАЗОМ',F(29,True),WHITE)
page.convert('RGB').save(OUT/'RAV4_M_S_YS_SKU共用选择图_V2_1086x1448.png',quality=96)

zip_path=R.parent/'Toyota_RAV4_灰色无耳_Tozaroa_新版设计V2.zip'
with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted(OUT.glob('*.png')): z.write(p,Path('Toyota_RAV4_新版设计V2')/p.name)
 for p in sorted((R/'04_上架资料').glob('*')):
  if p.suffix.lower() in {'.csv','.html','.txt'}: z.write(p,Path('Toyota_RAV4_新版设计V2')/'上架资料'/p.name)
print(zip_path)
