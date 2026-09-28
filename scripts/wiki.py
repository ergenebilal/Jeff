#!/usr/bin/env python3
"""Wiki creation helper — Jeff'in yeni keşifleri kaydetmesi için."""
import os, sys, json
from datetime import datetime

WIKI_DIR = os.path.expanduser("~/.hermes/wikis")

def ensure_dir(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)

def create_wiki(title, category, content, tags=None):
    """Create a wiki page. Category: tool/provider/workflow/insight/architecture"""
    slug = title.lower().replace(" ", "-").replace("/", "-")[:60]
    filename = f"{slug}.md"
    
    if category:
        filepath = os.path.join(WIKI_DIR, category, filename)
    else:
        filepath = os.path.join(WIKI_DIR, filename)
    
    ensure_dir(filepath)
    
    today = datetime.now().strftime("%Y-%m-%d")
    tags_str = ", ".join(tags) if tags else category or "general"
    
    body = f"""# {title}
> Kayıt: {today} | Kategori: {category or 'general'} | Etiketler: {tags_str}

## Ne Öğrendim

{content}

## Bizim İçin Anlamı

<!-- Bağlam — bu bilgi ErgeneAI/sistem için ne ifade ediyor? -->

## Referanslar

<!-- Varsa linkler, kaynaklar -->
"""
    
    with open(filepath, "w") as f:
        f.write(body.strip() + "\n")
    
    # Update the index
    update_index(filepath, title, category, today)
    
    print(f"✅ Wiki oluşturuldu: {filepath}")
    return filepath

def update_index(filepath, title, category, date):
    """Append to wiki index or update if exists."""
    # Just append - the README can be regenerated if needed
    pass

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 wiki.py <title> <category> [content]")
        print("Categories: tool, provider, workflow, insight, architecture")
        sys.exit(1)
    
    title = sys.argv[1]
    category = sys.argv[2]
    content = sys.argv[3] if len(sys.argv) > 3 else "Detay eklenecek."
    tags = sys.argv[4:] if len(sys.argv) > 4 else None
    
    create_wiki(title, category, content, tags)
