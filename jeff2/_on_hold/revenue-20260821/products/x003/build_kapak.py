#!/usr/bin/env python3
"""X-003 prompt pack kapak — Avukat + Hekim"""
from PIL import Image, ImageDraw, ImageFont

def build(path, title1, title2, subtitle, icon, out):
    W, H = 2000, 1500
    NAVY=(31,56,100); GOLD=(255,217,102); WHITE=(255,255,255); LIGHT=(222,235,247)
    img = Image.new("RGB",(W,H),NAVY)
    d = ImageDraw.Draw(img)
    d.rectangle([0,0,W,40],fill=GOLD)
    d.rectangle([0,H-40,W,H],fill=GOLD)
    d.rectangle([0,0,30,H],fill=GOLD)
    def center(y,t,font,fill):
        b= d.textbbox((0,0),t,font=font); tw=b[2]-b[0]; d.text(((W-tw)//2,y),t,fill=fill,font=font)
    t1=ImageFont.truetype(path,140); t2=ImageFont.truetype(path,84); t3=ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",52)
    center(100,title1,t1,GOLD)
    center(280,title2,t1,WHITE)
    center(480,subtitle,t3,LIGHT)
    # ikon dairesi
    cx,cy,r=W//2,H-520,260
    d.ellipse([cx-r,cy-r,cx+r,cy+r],fill=GOLD)
    big=ImageFont.truetype(path,230)
    center(cy-140,icon,big,NAVY)
    chips=["✅ 12 Hazır Prompt","✅ Türkçe","✅ PDF İndir","✅ AI Uyumlu"]
    f=ImageFont.truetype(path,44)
    for i,c in enumerate(chips):
        bb=d.textbbox((0,0),c,font=f); tw=bb[2]-bb[0]; cw=tw+70
        x=(W-(4*cw+60))//2 + i*(cw+20)
        d.rounded_rectangle([x,800,x+cw,880],radius=40,outline=GOLD,width=4)
        d.text((x+35,815),c,fill=WHITE,font=f)
    center(H-140,"ErgeneAI · info@ergeneai.com",ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",40),LIGHT)
    img.save(out); print("OK",out)

FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
build(FONT,"AVUKAT","AI PROMPT PAKETİ","12 hazır, Türkçe, mevzuat uyumlu prompt","⚖️","/home/hermes/jeff2/revenue/products/x003/kapak_avukat.png")
build(FONT,"HEKİM","AI PROMPT PAKETİ","10 hazır, Türkçe, etik & KVKK uyumlu","🩺","/home/hermes/jeff2/revenue/products/x003/kapak_hekim.png")
