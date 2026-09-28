#!/usr/bin/env python3
"""X-001 — TR + Global E-Ticaret Net Kâr & Komisyon Hesaplayıcı (formüllü .xlsx)"""
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.utils import get_column_letter

wb = openpyxl.Workbook()

# ---------- Renk / stil tanımları ----------
NAVY = "1F3864"
BLUE = "2E75B6"
LIGHT = "DEEBF7"
GOLD = "FFF2CC"
GREEN = "C6EFCE"
RED = "FFC7CE"
GRAY = "F2F2F2"
WHITE = "FFFFFF"

def style_title(cell, text):
    cell.value = text
    cell.font = Font(bold=True, size=16, color=WHITE)
    cell.fill = PatternFill("solid", fgColor=NAVY)
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

def style_header(cell, text):
    cell.value = text
    cell.font = Font(bold=True, color=WHITE, size=11)
    cell.fill = PatternFill("solid", fgColor=BLUE)
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

def style_label(cell, text=None, fill=LIGHT):
    if text is not None:
        cell.value = text
    cell.font = Font(bold=True)
    cell.fill = PatternFill("solid", fgColor=fill)
    cell.alignment = Alignment(vertical="center")

def style_input(cell):
    cell.fill = PatternFill("solid", fgColor=WHITE)
    cell.border = Border(left=Side(style="thin", color="B0B0B0"),
                         right=Side(style="thin", color="B0B0B0"),
                         top=Side(style="thin", color="B0B0B0"),
                         bottom=Side(style="thin", color="B0B0B0"))
    cell.alignment = Alignment(horizontal="center")

# =================================================================
# SAYFA 1 — GİRİŞ (Dashboard)
# =================================================================
ws = wb.active
ws.title = "Giriş"
ws.sheet_view.showGridLines = False
ws.column_dimensions['A'].width = 34
ws.column_dimensions['B'].width = 22
ws.column_dimensions['C'].width = 22
ws.column_dimensions['D'].width = 8

ws.merge_cells('A1:C1')
style_title(ws['A1'], "🛒 E-TİCARET NET KÂR & KOMİSYON HESAPLAYICI")
ws.merge_cells('A2:C2')
ws['A2'] = "TR Pazaryerleri (Trendyol / Hepsiburada / Amazon TR) + Global Etsy"
ws['A2'].font = Font(italic=True, color="666666", size=10)
ws['A2'].alignment = Alignment(horizontal="center")

# Başlık satırları
ws['A4'] = "ÜRÜN BİLGİSİ"; ws['A4'].font = Font(bold=True, size=13, color=NAVY)
ws['A5'] = "Ürün Adı"; ws['B5'] = ""; ws['C5'] = ""
ws['A6'] = "Satış Fiyatı (₺)"; ws['B6'] = 100
ws['A7'] = "Ürün Maliyeti (₺ / adet)"; ws['B7'] = 35
ws['A8'] = "Satış Adedi"; ws['B8'] = 1
for r in range(5, 9):
    style_label(ws[f'A{r}'])
    style_input(ws[f'B{r}'])

ws['A10'] = "PAZARYERİ & KATEGORİ"; ws['A10'].font = Font(bold=True, size=13, color=NAVY)
ws['A11'] = "Pazaryeri"; ws['B11'] = "Trendyol"
ws['A12'] = "Kategori"; ws['B12'] = "Elektronik"
style_label(ws['A11']); style_input(ws['B11'])
style_label(ws['A12']); style_input(ws['B12'])

# Dropdown'lar
dv_pz = DataValidation(type="list", formula1='"Trendyol,Hepsiburada,Amazon TR,Etsy"', allow_blank=False)
dv_kat = DataValidation(type="list", formula1='=Matris!$A$3:$A$12', allow_blank=False)
ws.add_data_validation(dv_pz); ws.add_data_validation(dv_kat)
dv_pz.add(ws['B11']); dv_kat.add(ws['B12'])

ws['A14'] = "MALİYET EKLERİ"; ws['A14'].font = Font(bold=True, size=13, color=NAVY)
ws['A15'] = "Kargo Maliyeti (₺ / adet)"; ws['B15'] = 20
ws['A16'] = "Reklam Bütçesi (₺ / ay)"; ws['B16'] = 0
ws['A17'] = "Reklam ACoS (%)"; ws['B17'] = 30
for r in range(15, 18):
    style_label(ws[f'A{r}'])
    style_input(ws[f'B{r}'])
ws['B17'].number_format = "0"

# =================================================================
# SAYFA 2 — MATRİS (komisyon verisi)
# =================================================================
ms = wb.create_sheet("Matris")
ms.column_dimensions['A'].width = 22
for c in "BCDEF":
    ms.column_dimensions[c].width = 14

ms.merge_cells('A1:F1')
style_title(ms['A1'], "KOMİSYON ORAN MATRİSİ (kategori bazlı)")

headers = ["Kategori", "Trendyol", "Hepsiburada", "Amazon TR", "Etsy İşlem", "Etsy Ödeme"]
for i, h in enumerate(headers, start=1):
    style_header(ms.cell(row=2, column=i), h)

data = [
    ("Elektronik", 0.08, 0.05, 0.10, 0.065, 0.03),
    ("Giyim", 0.2136, 0.18, 0.15, 0.065, 0.03),
    ("Ayakkabı", 0.20, 0.18, 0.15, 0.065, 0.03),
    ("Kozmetik", 0.18, 0.17, 0.13, 0.065, 0.03),
    ("Takı & Mücevher", 0.225, 0.20, 0.15, 0.065, 0.03),
    ("Ev & Yaşam", 0.15, 0.12, 0.12, 0.065, 0.03),
    ("Gıda", 0.125, 0.10, 0.08, 0.065, 0.03),
    ("Cep Telefonu", 0.07, 0.06, 0.08, 0.065, 0.03),
    ("Kitap", 0.15, 0.10, 0.12, 0.065, 0.03),
    ("Oyuncak", 0.15, 0.12, 0.13, 0.065, 0.03),
]
r = 3
for row in data:
    for c, val in enumerate(row, start=1):
        cell = ms.cell(row=r, column=c, value=val)
        if c > 1:
            cell.number_format = "0.0%"
    r += 1

ms['A14'] = "Not: Oranlar 2026 ortalama değerleridir. Pazaryeri güncel komisyon sayfasından doğrulayın."
ms['A14'].font = Font(italic=True, size=9, color="888888")
for rr in range(3, 13):
    for cc in range(1, 7):
        ms.cell(row=rr, column=cc).border = Border(left=Side(style="thin", color="D0D0D0"), right=Side(style="thin", color="D0D0D0"), top=Side(style="thin", color="D0D0D0"), bottom=Side(style="thin", color="D0D0D0"))
        ms.cell(row=rr, column=cc).alignment = Alignment(horizontal="center")

# =================================================================
# SAYFA 3 — HESAPLAMA (otomatik, formüllü)
# =================================================================
hc = wb.create_sheet("Hesaplama")
hc.sheet_view.showGridLines = False
hc.column_dimensions['A'].width = 38
hc.column_dimensions['B'].width = 20
hc.column_dimensions['C'].width = 26

hc.merge_cells('A1:B1')
style_title(hc['A1'], "NET KÂR HESAPLAMA MOTORU")

rows = [
    ("Satış Fiyatı (₺)", "=Giriş!B6", "₺0.00", "bg"),
    ("Ürün Maliyeti (₺/adet)", "=Giriş!B7", "₺0.00", "in"),
    ("Satış Adedi", "=Giriş!B8", "0", "in"),
    ("Pazaryeri", "=Giriş!B11", "", "txt"),
    ("Kategori", "=Giriş!B12", "", "txt"),
    ("Komisyon Oranı", '=IF(B5="Trendyol",VLOOKUP(B6,Matris!$A$3:$B$12,2,0),IF(B5="Hepsiburada",VLOOKUP(B6,Matris!$A$3:$C$12,3,0),IF(B5="Amazon TR",VLOOKUP(B6,Matris!$A$3:$D$12,4,0),VLOOKUP(B6,Matris!$A$3:$E$12,5,0))))', "0.0%", "res"),
    ("Komisyon Tutarı (₺)", "=B2*B7", "₺0.00", "res"),
    ("Kargo Maliyeti (₺)", "=Giriş!B15", "₺0.00", "in"),
    ("Reklam Bütçesi (₺)", "=Giriş!B16", "₺0.00", "in"),
    ("Reklam ACoS (%)", "=Giriş!B17/100", "0%", "in"),
    ("Reklam Maliyeti (₺)", "=B2*B11", "₺0.00", "res"),
    ("KDV (%18 TR)", "=B2*0.18*0.5", "₺0.00", "res"),
    ("Stopaj (varsa %1)", "=B2*0.01", "₺0.00", "res"),
    ("TOPLAM UNSUR (₺)", "=B8+B9+B12+B13+B14", "₺0.00", "sum"),
    ("NET KÂR (₺ / ürün)", "=B2-B3-B15", "₺0.00", "big"),
    ("Toplam Kâr (₺)", "=B16*B4", "₺0.00", "big"),
    ("Brüt Kâr Marjı", "=IF(B2=0,0,B16/B2)", "0.0%", "res"),
]

# E sütununda oran kontrol değerleri: E1..E5 pazaryeri/kategori bilgisini taşır
# (E1=E2 satış fiyatı, E5=kategori) — formüller E2/E5'e referans veriyor.
r = 2
for label, formula, nf, kind in rows:
    style_label(hc.cell(row=r, column=1), label)
    cell = hc.cell(row=r, column=2, value=formula)
    cell.number_format = nf
    if kind == "bg":
        cell.fill = PatternFill("solid", fgColor=GOLD); cell.font = Font(bold=True, size=12)
    elif kind == "in":
        cell.fill = PatternFill("solid", fgColor=WHITE)
    elif kind == "res":
        cell.fill = PatternFill("solid", fgColor=LIGHT)
    elif kind == "sum":
        cell.fill = PatternFill("solid", fgColor=GOLD); cell.font = Font(bold=True)
    elif kind == "big":
        cell.fill = PatternFill("solid", fgColor=GREEN); cell.font = Font(bold=True, size=14, color="006100")
    cell.alignment = Alignment(horizontal="center")
    cell.border = Border(left=Side(style="thin", color="B0B0B0"), right=Side(style="thin", color="B0B0B0"), top=Side(style="thin", color="B0B0B0"), bottom=Side(style="thin", color="B0B0B0"))
    r += 1

# Özet panel — koşullu renkli kar/zarar
hc['A21'] = "DURUM"; hc['A21'].font = Font(bold=True, size=13, color=NAVY)
hc['A22'] = '=IF(B16>0,"✅ KÂRLI",IF(B16=0,"⚖️ BAŞABAŞ","❌ ZARARDA"))'
hc['A22'].font = Font(bold=True, size=14)

# =================================================================
# SAYFA 4 — REHBER
# =================================================================
gd = wb.create_sheet("Rehber")
gd.column_dimensions['A'].width = 6
gd.column_dimensions['B'].width = 100
gd.merge_cells('B1:B1')
gd['B1'] = "📘 KULLANIM REHBERİ"
gd['B1'].font = Font(bold=True, size=15, color=NAVY)

guide = [
    "1. 'Giriş' sekmesinde ürün bilgilerini doldurun: ad, satış fiyatı, maliyet, adet.",
    "2. Pazaryeri ve kategoriyi açılır menüden seçin (oranlar 'Matris' sekmesinden otomatik çekilir).",
    "3. Kargo maliyeti, reklam bütçesi ve ACoS'unuzu girin.",
    "4. 'Hesaplama' sekmesi tüm ücretleri (komisyon, kargo, reklam, KDV, stopaj) otomatik toplar ve NET KÂR'ı gösterir.",
    "5. Yeşil 'KÂRLI' / kırmızı 'ZARARDA' sinyali ile fiyat kararınızı anında görün.",
    "",
    "⚠️ Oranlar 2026 güncel ortalama değerlerdir. Pazaryeri komisyonu değişirse 'Matris' sekmesini güncelleyin.",
    "💡 'Fiyatlandırma Asistanı' olarak kullanın: maliyeti girin, kârlı kalacak minimum satış fiyatını bulun.",
    "📧 Satın alım sonrası destek & güncelleme: info@ergeneai.com",
]
for i, line in enumerate(guide, start=3):
    gd.cell(row=i, column=2, value=line)

# fullCalcOnLoad — Excel/LibreOffice açınca formüller hesaplansın
wb.calculation.fullCalcOnLoad = True

out = "/home/hermes/jeff2/revenue/products/x001/TR-Eticaret-NetKar-Komisyon-Hesaplayici.xlsx"
wb.save(out)
print("KAYDEDİLDİ:", out)
print("Sheets:", wb.sheetnames)
