#!/usr/bin/env python3
"""WhatsApp demo görseli — AI resepsiyonist diyaloğu (dental)"""
from PIL import Image, ImageDraw, ImageFont

W, H = 900, 1350
BG = (222, 217, 211)  # WhatsApp sohbet arka planı
GREEN = (222, 250, 215)  # giden balon
WHITE = (255, 255, 255)  # gelen balon
TEAL = (0, 168, 132)  # WhatsApp yeşili (başlık)

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)

f_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 34)
f_bold = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 26)
f_body = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 25)
f_time = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 18)

# Başlık çubuğu
d.rectangle([0, 0, W, 110], fill=TEAL)
d.ellipse([30, 25, 90, 85], fill=(255,255,255))
d.text((50, 38), "D", fill=TEAL, font=f_bold)
d.text((115, 40), "Diş Kliniği WhatsApp", fill=(255,255,255), font=f_title)
d.text((115, 80), "çevrimiçi • AI asistan aktif", fill=(210,240,235), font=f_time)

# Balon çizim yardımcısı
def bubble(x, y, w, h, color, radius=18):
    d.rounded_rectangle([x, y, x+w, y+h], radius=radius, fill=color)

# Metni satırlara böl
def draw_text(x, y, text, font, fill, max_w):
    words = text.split()
    lines, cur = [], ""
    for w_ in words:
        t = cur + " " + w_
        if d.textlength(t, font=font) <= max_w:
            cur = t
        else:
            lines.append(cur); cur = w_
    lines.append(cur)
    return lines

y = 140
# Gelen (hasta)
lines = draw_text(50, 0, "Merhaba, diş beyazlatma ücreti ne kadar?", f_body, (0,0,0), 520)
h = len(lines)*32 + 30
bubble(30, y, 560, h, WHITE)
for i, l in enumerate(lines):
    d.text((52, y+15+i*32), l, fill=(0,0,0), font=f_body)
d.text((540, y+h-30), "21:02", fill=(130,130,130), font=f_time)
y += h + 14

# Giden (AI resepsiyonist)
lines = draw_text(50, 0, "Merhaba! 😊 Beyazlatma seansımız ₺1.500, tek seansta 3 ton açılma sağlıyor. Randevu almak ister misiniz?", f_body, (0,0,0), 600)
h = len(lines)*32 + 30
bubble(210, y, 660, h, GREEN)
for i, l in enumerate(lines):
    d.text((232, y+15+i*32), l, fill=(0,0,0), font=f_body)
d.text((820, y+h-30), "21:02", fill=(130,130,130), font=f_time)
y += h + 14

# Gelen (hasta)
lines = draw_text(50, 0, "Evet, bu cumartesi olur mu?", f_body, (0,0,0), 500)
h = len(lines)*32 + 30
bubble(30, y, 500, h, WHITE)
for i, l in enumerate(lines):
    d.text((52, y+15+i*32), l, fill=(0,0,0), font=f_body)
d.text((480, y+h-30), "21:03", fill=(130,130,130), font=f_time)
y += h + 14

# Giden (AI)
lines = draw_text(50, 0, "Cumartesi 10:30 için doktorumuz müsait ✓ Takvime işledim, seans öncesi hatırlatma göndereceğim. Sağlıklı günler! 🙏", f_body, (0,0,0), 620)
h = len(lines)*32 + 30
bubble(190, y, 680, h, GREEN)
for i, l in enumerate(lines):
    d.text((212, y+15+i*32), l, fill=(0,0,0), font=f_body)
d.text((830, y+h-30), "21:03", fill=(130,130,130), font=f_time)
y += h + 14

# Alt banner (pazarlama) — "gece 2'de gelen mesaj da cevapsız kalmaz"
banner_y = y + 20
d.rectangle([40, banner_y, W-40, banner_y+80], fill=TEAL)
d.text((70, banner_y+18), "🕑 Gece bile hasta mesajı cevapsız kalmaz (7/24)", fill=(255,255,255), font=f_bold)

img.save("/home/hermes/jeff2/revenue/whatsapp-demo-dental.png")
print("Demo görsel kaydedildi")
