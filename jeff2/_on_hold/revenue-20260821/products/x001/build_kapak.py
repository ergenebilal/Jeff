#!/usr/bin/env python3
"""X-001 ürün kapak görseli — Pillow ile, marka renkli, Türkçe okunaklı"""
from PIL import Image, ImageDraw, ImageFont

W, H = 2000, 1500  # Etsy 4:3 kapak
NAVY = (31, 56, 100)
GOLD = (255, 217, 102)
WHITE = (255, 255, 255)
LIGHT = (222, 235, 247)

img = Image.new("RGB", (W, H), NAVY)
d = ImageDraw.Draw(img)

# üst alt şeritler
d.rectangle([0, 0, W, 40], fill=GOLD)
d.rectangle([0, H-40, W, H], fill=GOLD)

# sol akçent
d.rectangle([0, 0, 30, H], fill=GOLD)

# emoji/simge alanı için basit çizim: dairesel büyük "₺"
cx, cy, r = W//2, H-560, 300
d.ellipse([cx-r, cy-r, cx+r, cy+r], fill=GOLD)
big_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 300)
d.text((cx-120, cy-220), "₺", fill=NAVY, font=big_font)

# Başlıklar
def center_text(y, text, font, fill):
    bbox = d.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    d.text(((W-tw)//2, y), text, fill=fill, font=font)

t1 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 130)
t2 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 72)
t3 = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 52)

center_text(90, "E-TİCARET", t1, WHITE)
center_text(240, "NET KÂR HESAPLAYICI", t1, GOLD)
center_text(430, "Komisyon • Kargo • Reklam • KDV • Stopaj", t3, LIGHT)
center_text(535, "Trendyol  |  Hepsiburada  |  Amazon TR  |  Etsy", t3, LIGHT)

# kullanım özellik çipleri (üstte, çemberin üstünde)
chips = ["✅ 10 Kategori Oranı", "✅ Otomatik Net Kâr", "✅ Fiyat Karar Aracı", "✅ İndir & Kullan"]
cy0 = 760
for i, c in enumerate(chips):
    f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 46)
    bbox = d.textbbox((0,0), c, font=f); tw = bbox[2]-bbox[0]
    chip_w = tw+70
    x = (W - (4*chip_w + 60))//2 + i*(chip_w+20)
    d.rounded_rectangle([x, cy0, x+chip_w, cy0+80], radius=40, fill=(255,255,255,0), outline=GOLD, width=4)
    d.text((x+35, cy0+15), c, fill=WHITE, font=f)

# alt bilgi
center_text(H-150, "Ar Electra · info@ergeneai.com", ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 40), LIGHT)

img.save("/home/hermes/jeff2/revenue/products/x001/kapak.png")
print("KAPAK KAYDEDİLDİ /home/hermes/jeff2/revenue/products/x001/kapak.png", img.size)
