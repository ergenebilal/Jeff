#!/usr/bin/env python3
"""
Lead DM Template - GitHub repo sahiplerine outreach mesajı
Kullanım: Günde 5 DM, lead generator'dan gelen kişilere
"""
import os
import sys
from typing import Optional

TEMPLATES: dict[str, str] = {
    "ai_agent": (
        "Hey {name}, {repo} projeni gördüm — AI agent tarafında gerçekten sağlam iş çıkarmışsın. "
        "Ben de aynı alanda çalışıyorum, kendi Hermes agent'ımı kurdum ve süreçleri otomatikleştirdim. "
        "Denk gelmişken şu rehber işine yarayabilir: https://ergene.gumroad.com/l/zero-to-ai-agent "
        "(şu an $7.99, içinde 3 adet production n8n workflow'u var). "
        "Kolay gelsin!"
    ),
    "n8n": (
        "Selam {name}, {repo} reposuna baktım — n8n kullanıyorsun, güzel iş. "
        "Ben de agent + n8n kombinasyonuyla uğraşıyorum. "
        "Production'da kullandığım 3 workflow'u şuraya bırakayım, belki iş görür: "
        "https://ergene.gumroad.com/l/zero-to-ai-agent "
        "Kolay gelsin!"
    ),
    "automation": (
        "Hey {name}, {repo} ilginç bir proje. Otomasyon tarafında ben de benzer şeyler yapıyorum. "
        "Kendi AI agent'ımı sıfırdan kurup 17 platformda monitoring çalıştırıyorum — hepsi $7 server'da. "
        "Detaylar: https://ergene.gumroad.com/l/zero-to-ai-agent "
        "İyi çalışmalar!"
    ),
}

DEFAULT_TEMPLATE: str = (
    "Hey {name}, {repo} projen ilgimi çekti. AI agent otomasyonuyla uğraşıyorsan "
    "şu rehbere göz atabilirsin: https://ergene.gumroad.com/l/zero-to-ai-agent "
    "Kolay gelsin!"
)


def get_template(repo_category: str = "ai_agent") -> str:
    """Get template by category, fallback to default."""
    return TEMPLATES.get(repo_category, DEFAULT_TEMPLATE)


def fill_template(template: str, name: str = "there", repo: str = "your repo") -> str:
    """Fill template variables."""
    return template.format(name=name, repo=repo)


def main() -> None:
    """Print available templates."""
    print("=== Lead DM Templates ===\n")
    for category, template in TEMPLATES.items():
        print(f"[{category}]")
        example: str = fill_template(template, name="Ali", repo="awesome-agent")
        print(f"  {example}")
        print()

    print("Usage: get_template('n8n') -> fill_template(template, name='...', repo='...')")


if __name__ == "__main__":
    main()
