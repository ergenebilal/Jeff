#!/usr/bin/env python3
"""Markdown → şık PDF (Playwright/Chromium). Türkçe karakterler ve tablolar destekli.

BIÇIM STANDARDI (v2 — tüm belgeler bu standarda uyar):
  · Kapak: H1 + tek satır meta
  · Bölüm: "## N. BAŞLIK" (yeşil alt çizgi)
  · Alt başlık: "### ..." (kayıt/firma blokları)
  · Meta satırı: *eğik* → gri, küçük (tarih · kapsam · telefon vb.)
  · Metin blokları: arka arkaya "> " satırları TEK kutu içinde birleşir (HTML etiketi belgeye yazılmaz)
  · Tablo: "|" ile; CSV'den gelen listeler csv_to_html() ile

KOPYALAMA GÜVENLİĞİ: bitişik harf (ligatür) ve kerning kapatıldı — PDF'ten kopyalanan metin
boşluksuz/bozuk çıkmaz ("say falık" gibi hatalar önlenir).

Kullanım:
  python3 md_pdf.py girdi.md cikti.pdf ["Başlık"]
  python3 md_pdf.py --csv-kapi girdi.csv cikti.pdf
"""
import csv
import html
import os
import re
import sys

from playwright.sync_api import sync_playwright

F_DISPLAY = "file:///home/hermes/pipeline/fonts/archivo-black.ttf"
F_TEXT = "file:///home/hermes/pipeline/fonts/manrope.ttf"
F_REG = "file:///home/hermes/pipeline/fonts/InterTight.ttf"

CSS = f"""
@font-face {{ font-family:'AB'; src:url('{F_DISPLAY}') format('truetype'); font-weight:400; }}
@font-face {{ font-family:'MR'; src:url('{F_TEXT}') format('truetype-variations'); font-weight:200 800; }}
@font-face {{ font-family:'IT'; src:url('{F_REG}') format('truetype-variations'); font-weight:100 900; }}
@page {{ size:A4; margin:16mm 14mm 18mm 14mm; }}
* {{ box-sizing:border-box; }}
body {{ font-family:'MR','IT',sans-serif; color:#101a15; font-size:10.5pt; line-height:1.55; margin:0;
        font-variant-ligatures:none; font-kerning:none; text-rendering:geometricPrecision;
        hyphens:none; -webkit-hyphens:none; word-break:normal; overflow-wrap:break-word; }}
h1 {{ font-family:'AB'; font-size:19pt; line-height:1.15; margin:0 0 6px; color:#08130d; letter-spacing:-.01em; }}
h2 {{ font-family:'AB'; font-size:13pt; margin:20px 0 8px; color:#0d3b22; border-bottom:2px solid #8CF06F;
      padding-bottom:5px; break-after:avoid; }}
h3 {{ font-family:'MR'; font-weight:800; font-size:11pt; margin:14px 0 3px; color:#123a25; break-after:avoid; }}
p {{ margin:0 0 6px; font-size:10.5pt; }}
ul, ol {{ margin:6px 0 10px; padding-left:20px; }}
li {{ margin-bottom:3px; }}
strong {{ font-weight:800; color:#08130d; }}
em {{ color:#5d6f66; font-style:normal; font-size:9.5pt; }}
hr {{ border:0; border-top:1px solid #dfe7e2; margin:16px 0; }}
table {{ width:100%; border-collapse:collapse; margin:10px 0 14px; font-size:9pt; }}
th {{ background:#0d3b22; color:#fff; text-align:left; padding:7px 8px; font-weight:700; }}
td {{ padding:6px 8px; border-bottom:1px solid #e6ece8; vertical-align:top; }}
tr:nth-child(even) td {{ background:#f7faf8; }}
blockquote {{ margin:6px 0 12px; padding:9px 13px; font-size:9.8pt; line-height:1.5; background:#f2f8f4;
              border-left:4px solid #8CF06F; border-radius:0 6px 6px 0; break-inside:avoid; }}
blockquote .bqp {{ margin:0 0 7px; }}
blockquote .bqp:last-child {{ margin-bottom:0; }}
code {{ font-family:'IT',monospace; background:#f0f4f1; padding:1px 4px; border-radius:3px; font-size:9pt; }}
.kapak {{ border-bottom:3px solid #8CF06F; padding-bottom:10px; margin-bottom:14px; }}
.alt {{ color:#5d6f66; font-size:9.5pt; }}
.sayfa-kir {{ page-break-before:always; }}
"""


def _temizle(t):
    """Fazla boşluk ve görünmez kirleri temizle."""
    t = t.replace("\u00a0", " ").replace("\u0307", "")
    t = re.sub(r"[ \t]{2,}", " ", t)
    return t.rstrip()


def satir_ic(t):
    """Satır içi markdown → HTML (HTML kaçışı yapılır; belgeye HTML yazılmaz)."""
    t = html.escape(_temizle(t))
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", t)
    t = re.sub(r"`(.+?)`", r"<code>\1</code>", t)
    return t


def md_to_html(md):
    """Markdown → HTML. Arka arkaya '> ' satırları TEK alıntı kutusunda birleştirilir."""
    out, i = [], 0
    satirlar = md.split("\n")
    while i < len(satirlar):
        s = satirlar[i].rstrip()
        # --- tablo ---
        if s.startswith("|") and i + 1 < len(satirlar) and set(satirlar[i + 1].replace("|", "").strip()) <= set("-: "):
            bas = [c.strip() for c in s.strip("|").split("|")]
            i += 2
            govde = []
            while i < len(satirlar) and satirlar[i].strip().startswith("|"):
                govde.append([c.strip() for c in satirlar[i].strip().strip("|").split("|")])
                i += 1
            out.append("<table><thead><tr>" + "".join(f"<th>{satir_ic(x)}</th>" for x in bas) + "</tr></thead><tbody>")
            for g in govde:
                out.append("<tr>" + "".join(f"<td>{satir_ic(x)}</td>" for x in g) + "</tr>")
            out.append("</tbody></table>")
            continue
        # --- alıntı bloğu (çok satırlı, paragraflı) ---
        if s.startswith(">"):
            ham = []
            while i < len(satirlar) and satirlar[i].rstrip().startswith(">"):
                x = satirlar[i].rstrip()
                ham.append(x[2:] if x.startswith("> ") else x[1:])
                i += 1
            paragraflar, gecici = [], []
            for x in ham:
                if x.strip():
                    gecici.append(satir_ic(x))
                elif gecici:
                    paragraflar.append(gecici)
                    gecici = []
            if gecici:
                paragraflar.append(gecici)
            govde = "".join(f'<div class="bqp">{"<br>".join(pr)}</div>' for pr in paragraflar)
            out.append(f"<blockquote>{govde}</blockquote>")
            continue
        # --- başlıklar ---
        if s.startswith("### "):
            out.append(f"<h3>{satir_ic(s[4:])}</h3>")
        elif s.startswith("## "):
            out.append(f"<h2>{satir_ic(s[3:])}</h2>")
        elif s.startswith("# "):
            out.append(f'<div class="kapak"><h1>{satir_ic(s[2:])}</h1></div>')
        # --- listeler ---
        elif re.match(r"^\s*[-*] ", s):
            out.append("<ul>")
            while i < len(satirlar) and re.match(r"^\s*[-*] ", satirlar[i]):
                out.append("<li>" + satir_ic(re.sub(r"^\s*[-*] ", "", satirlar[i])) + "</li>")
                i += 1
            out.append("</ul>")
            continue
        elif re.match(r"^\s*\d+\. ", s):
            out.append("<ol>")
            while i < len(satirlar) and re.match(r"^\s*\d+\. ", satirlar[i]):
                out.append("<li>" + satir_ic(re.sub(r"^\s*\d+\. ", "", satirlar[i])) + "</li>")
                i += 1
            out.append("</ol>")
            continue
        elif s.strip() == "---":
            out.append("<hr>")
        elif s.strip():
            out.append(f"<p>{satir_ic(s)}</p>")
        i += 1
    return "\n".join(out)


def pdf(html_govde, cikti, baslik, yatay=False):
    css = CSS.replace("size:A4;", "size:A4 landscape;") if yatay else CSS
    tam = (f"<!doctype html><html lang=tr><head><meta charset=utf-8><title>{html.escape(baslik)}</title>"
           f"<style>{css}</style></head><body>{html_govde}</body></html>")
    gecici = f"/tmp/pdf_{os.getpid()}.html"
    open(gecici, "w", encoding="utf-8").write(tam)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        pg.goto("file://" + gecici)
        pg.evaluate("async () => { await document.fonts.ready; }")
        pg.wait_for_timeout(400)
        pg.pdf(path=cikti, format="A4", landscape=yatay, print_background=True,
               margin={"top": "14mm", "bottom": "16mm", "left": "13mm", "right": "13mm"},
               display_header_footer=True,
               header_template="<div></div>",
               footer_template=('<div style="font:8pt \'Helvetica\';color:#8b9c92;width:100%;padding:0 12mm;'
                                'display:flex;justify-content:space-between">'
                                f'<span>{html.escape(baslik)}</span><span>sayfa <span class="pageNumber"></span>/'
                                '<span class="totalPages"></span></span></div>'))
        b.close()
    print(f"✓ {cikti} ({os.path.getsize(cikti)//1024} KB)")


def csv_to_html(yol, baslik, kolonlar=None, limit=None):
    satirlar = list(csv.DictReader(open(yol, encoding="utf-8-sig")))
    satirlar = satirlar[:limit] if limit else satirlar
    bas = kolonlar or list(satirlar[0].keys())
    g = ["<table><thead><tr>" + "".join(f"<th>{html.escape(b)}</th>" for b in bas) + "</tr></thead><tbody>"]
    for r in satirlar:
        g.append("<tr>" + "".join(f"<td>{html.escape(_temizle(str(r.get(b, '')))[:80])}</td>" for b in bas) + "</tr>")
    g.append("</tbody></table>")
    return "".join(g)


if __name__ == "__main__":
    if sys.argv[1] == "--csv-kapi":
        src, hedef = sys.argv[2], sys.argv[3]
        baslik = "Doktor Kılavuzu — Kapı Listesi (ilk 60 hedef)"
        h = (f'<div class="kapak"><h1>{baslik}</h1><div class="alt">14.09.2026 · öncelik sırası · '
             f'telefon, site, Instagram ve platform durumu doğrulanmıştır</div></div>')
        h += csv_to_html(src, baslik,
                         kolonlar=["#", "hekim / işletme", "branş", "ilçe", "telefon", "site durumu", "instagram",
                                   "puan", "yorum", "doktor kılavuzu", "öncelik"])
        pdf(h, hedef, baslik, yatay=True)
    else:
        md = open(sys.argv[1], encoding="utf-8").read()
        ad = sys.argv[3] if len(sys.argv) > 3 else os.path.basename(sys.argv[1])
        pdf(md_to_html(md), sys.argv[2], ad)
