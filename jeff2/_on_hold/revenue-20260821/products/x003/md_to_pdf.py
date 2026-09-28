#!/usr/bin/env python3
"""Markdown prompt pack -> şık PDF (reportlab)"""
import re
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.enums import TA_LEFT

NAVY = colors.HexColor("#1F3864")
GOLD = colors.HexColor("#FFD966")
GREY = colors.HexColor("#444444")

def md_to_pdf(md_path, out_path, brand_title):
    styles = getSampleStyleSheet()
    title = ParagraphStyle("Title2", parent=styles["Title"], fontSize=24, textColor=colors.white, alignment=1, backColor=NAVY, spaceAfter=6, borderPadding=10)
    h1 = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=16, textColor=NAVY, spaceBefore=10, spaceAfter=4)
    prompt = ParagraphStyle("Prompt", parent=styles["BodyText"], fontSize=9.5, leading=13, backColor=colors.HexColor("#F4F4F4"), borderColor=colors.HexColor("#DDDDDD"), borderWidth=0.5, borderPadding=8, spaceAfter=8, leftIndent=6, textColor=colors.black)
    body = ParagraphStyle("Body", parent=styles["BodyText"], fontSize=10, leading=14)
    small = ParagraphStyle("Small", parent=styles["BodyText"], fontSize=8, textColor=GOLD)

    lines = open(md_path, encoding="utf-8").read().splitlines()
    doc = SimpleDocTemplate(out_path, pagesize=A4, leftMargin=18*mm, rightMargin=18*mm, topMargin=18*mm, bottomMargin=18*mm)
    story = []
    story.append(Paragraph(brand_title, title))
    story.append(Paragraph("ErgeneAI · AI Prompt Paketi", small))
    story.append(Spacer(1, 8))

    for ln in lines:
        s = ln.strip()
        if not s:
            continue
        if s.startswith("# ") or s.startswith("## "):
            story.append(Paragraph(s.lstrip("# ").strip(), h1))
            story.append(HRFlowable(width="100%", thickness=1, color=NAVY, spaceAfter=6))
        elif s.startswith("```") or s.startswith("---"):
            continue
        elif s == "```" or s == "```":
            continue
        elif s.startswith("> "):
            story.append(Paragraph(s[2:], body))
        else:
            # prompt bloğu içinde mi?
            story.append(Paragraph(_fmt(s), body))

    doc.build(story)
    print("PDF OK:", out_path)

def _fmt(s):
    # basit bold ** ** ve satır sonu desteği
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    return s.replace("&", "&amp;").replace("<b>", "\x00b").replace("</b>", "\x00B") if False else _safe(s)

def _safe(s):
    import html
    s = html.escape(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = s.replace("\n", "<br/>")
    return s

if __name__ == "__main__":
    import sys
    md_to_pdf(sys.argv[1], sys.argv[2], sys.argv[3])
