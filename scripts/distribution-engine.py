#!/usr/bin/env python3
import os
import sys
import re

def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^a-z0-9]', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')

def create_output_dir(product_name):
    dirname = slugify(product_name)
    path = os.path.join("output", dirname)
    os.makedirs(path, exist_ok=True)
    return path

def generate_social_posts(product, description, audience):
    lines = [
        "# Sosyal Medya Postlari (5 Adet)\n",
        f"**Urun:** {product}  \n",
        f"**Hedef Kitle:** {audience}\n\n",
        "---\n",
        f"## Post 1 — X (Twitter)\n",
        f"{product} ile {audience} icin cozum burada.\n",
        f"{description[:200]}\n",
        f"Daha fazlasini kesfetmeye hazir misin? 👇\n\n",
        f"#Firsat #{slugify(product).replace('-','')} #{slugify(audience.split(',')[0]).replace('-','')}\n\n",
        "---\n",
        f"## Post 2 — LinkedIn\n",
        f"**{product} ile tanisin.**\n\n",
        f"{description[:300]}\n\n",
        f"Bu cozum ozellikle {audience} icin tasarlandi. Profesyonel hayatinizda fark yaratmak\n",
        f"istiyorsaniz, bu tam size gore.\n\n",
        f"Detayli bilgi icin takipte kalin! 🚀\n\n",
        f"#{slugify(product).replace('-','')} #{slugify(audience.split(',')[0]).replace('-','')} Inovasyon\n\n",
        "---\n",
        f"## Post 3 — Instagram\n",
        f"🔥 **{product}** cikti!\n\n",
        f"{description[:150]}\n\n",
        f"{audience} — bu sizin icin ozel olarak hazirlandi. Kacirmayin!\n\n",
        f"👉 Link profilde\n\n",
        f"#YeniUrun #{slugify(product).replace('-','')} #{slugify(audience.split(',')[0]).replace('-','')} Kesfet\n\n",
        "---\n",
        f"## Post 4 — X (Twitter) Kisa\n",
        f"Simdi {product} ile {audience} olmanin avantajlarini yasayin.\n",
        f"{description[:100]}\n\n",
        f"{slugify(product).replace('-','')} #{slugify(audience.split(',')[0]).replace('-','')} Yenilik\n\n",
        "---\n",
        f"## Post 5 — LinkedIn / Instagram\n",
        f"**Degerli {audience},**\n\n",
        f"Size ozel bir cozumumuz var: {product}\n\n",
        f"{description[:250]}\n\n",
        f"Hayatinizi kolaylastiracak bu firsati kacirmayin. Hemen inceleyin!\n\n",
        f"#{slugify(product).replace('-','')} #{slugify(audience.split(',')[0]).replace('-','')} DijitalDonusum\n",
    ]
    return "".join(lines)

def generate_community_comments(product, description, audience):
    lines = [
        "# Topluluk Yorumlari (3 Adet)\n",
        f"**Urun:** {product}\n",
        f"**Hedef Kitle:** {audience}\n\n",
        "---\n",
        f"## Yorum 1 — Reddit (r/girisimcilik)\n\n",
        f"Kendi isimi yuruturken {audience} icin hep su sorunu yasiyordum: "
        f"{description[:180]}\n\n",
        f"Daha sonra {product} ile karsilastim ve isler gercekten degisti. "
        f"Ozellikle zaman kazandiran yonuyle farki hemen hissettim. "
        f"Denemek isteyenlere siddetle tavsiye ederim.\n\n",
        "---\n",
        f"## Yorum 2 — Skool Toplulugu\n\n",
        f"Selam arkadaslar, uzun suredir {audience} olarak {product} 'i "
        f"kullaniyorum ve cok memnunum.\n\n",
        f"{description[:200]}\n\n",
        f"Sizin deneyimleriniz nasil? Kullanan varsa yorumlarini merak ediyorum.\n\n",
        "---\n",
        f"## Yorum 3 — Reddit (r/urunlertanitimi)\n\n",
        f"Bugun {product} ile tanistim ve gercekten etkilendim.\n\n",
        f"{description[:150]}\n\n",
        f"Ozellikle {audience} icin tasarlanmis olmasi buyuk bir arti. "
        f"Fiyat/performans acisindan da degerlendirmek lazim.\n\n",
    ]
    return "".join(lines)

def generate_seo_content(product, description, audience):
    lines = [
        "# SEO Icerik (2 Blog Yazisi)\n",
        f"**Urun:** {product}\n",
        f"**Hedef Kitle:** {audience}\n\n",
        "---\n",
        f"## Blog Yazisi 1\n\n",
        f"**Baslik:** {product} ile {audience} icin En Iyi Cozumler\n\n",
        f"**Giris Paragrafi:**\n",
        f"Gunumuzde {audience} olmanin zorluklari her gecen gun artiyor. "
        f"Iste tam bu noktada {product} devreye giriyor. "
        f"{description[:300]}\n",
        f"Bu yazimizda {product} 'in sundugu avantajlari, "
        f"kimler icin uygun oldugunu ve nasil maksimum verim "
        f"alabileceginizi detayli bir sekilde ele alacagiz.\n\n",
        f"**Hashtagler:** #{slugify(product).replace('-','')}, #{slugify(audience.strip()).replace('-','')}, cozum, rehber, inovasyon, dijital\n\n",
        "---\n",
        f"## Blog Yazisi 2\n\n",
        f"**Baslik:** {product} Nedir ve {audience} Icin Neden Onemlidir?\n\n",
        f"**Giris Paragrafi:**\n",
        f"Teknoloji dunyasinda hizla yukselen {product}, "
        f"ozellikle {audience} icin sundugu yenilikci yaklasimla dikkat cekiyor. "
        f"{description[:300]}\n",
        f"Bu kapsamli rehberde {product} 'in ne oldugunu, "
        f"nasil calistigini ve isinize nasil deger katacagini "
        f"adim adim anlatiyor olacagiz.\n\n",
        f"**Hashtagler:** #{slugify(product).replace('-','')}, #{slugify(audience.strip()).replace('-','')}, nedir, rehber, teknoloji, yenilik\n",
    ]
    return "".join(lines)

def generate_email_chain(product, description, audience):
    lines = [
        "# E-posta Zinciri (3 Mail)\n",
        f"**Urun:** {product}\n",
        f"**Hedef Kitle:** {audience}\n\n",
        "---\n",
        f"## Mail 1 — Tanitim\n\n",
        f"**Konu:** {product} ile tanisin! 🎉\n\n",
        f"Merhaba,\n\n",
        f"Size heyecan verici bir haberi paylasmak istiyoruz: **{product}** "
        f"artik sizlerle!\n\n",
        f"{description[:250]}\n\n",
        f"Bu yeniligi kacirmayin, hemen kesfedin.\n\n",
        f"Sevgiler,\n{product} Ekibi\n\n",
        "---\n",
        f"## Mail 2 — Deger\n\n",
        f"**Konu:** {product} size nasil deger katar? 💡\n\n",
        f"Merhaba,\n\n",
        f"Gecen mailimizde {product} 'i tanitmistik. Simdi biraz daha "
        f"derine inelim:\n\n",
        f"{description[:300]}\n\n",
        f"{audience} icin ozel olarak tasarlanan {product} ile "
        f"islerinizi cok daha verimli hale getirebilirsiniz.\n\n",
        f"Detayli bilgi icin sizi bekliyoruz.\n\n",
        f"Sevgiler,\n{product} Ekibi\n\n",
        "---\n",
        f"## Mail 3 — Satis\n\n",
        f"**Konu:** {product} 'i denemeye hazir misiniz? 🚀\n\n",
        f"Merhaba,\n\n",
        f"{audience} icin tasarlanan {product} ile tanisma firsatini "
        f"kacirmayin.\n\n",
        f"{description[:200]}\n\n",
        f"**Su an harekete gecin ve farki gorun!**\n\n",
        f"Hemen baslayin 👇\n\n",
        f"Sevgiler,\n{product} Ekibi\n",
    ]
    return "".join(lines)

def generate_followup_schedule(product, audience):
    lines = [
        "# Takipte Kalma Takvimi\n",
        f"**Urun:** {product}\n",
        f"**Hedef Kitle:** {audience}\n\n",
        "---\n",
        f"## 7 Gun Sonra — Hatirlatma\n\n",
        f"Merhaba,\n\n",
        f"Gecen hafta {product} ile tanisma firsati bulmustunuz. "
        f"Henuz denemediyseniz, simdi tam zamani!\n\n",
        f"{audience} icin ozel olarak tasarlanan bu cozumle "
        f"neler kacirdiginizi gormek ister misiniz?\n\n",
        "---\n",
        f"## 14 Gun Sonra — Takip\n\n",
        f"Merhaba,\n\n",
        f"{product} hakkinda dusuncelerinizi merak ediyoruz. "
        f"Deneme firsatiniz oldu mu? Herhangi bir sorunuz varsa "
        f"yardimci olmaktan mutluluk duyariz.\n\n",
        f"Unutmayin, {audience} icin en dogru cozum {product}!\n\n",
        "---\n",
        f"## 21 Gun Sonra — Son Hatirlatma\n\n",
        f"Merhaba,\n\n",
        f"Bu, {product} ile ilgili son hatirlatma mesajimiz.\n\n",
        f"{audience} olarak bu firsati kacirmak istemezsiniz. "
        f"Hala zaman varken degerlendirin!\n\n",
        f"Sizi aramizda gormekten mutluluk duyariz.\n",
    ]
    return "".join(lines)

def main():
    if len(sys.argv) < 3:
        print("Kullanim: python3 distribution-engine.py \"Urun Adi\" \"Aciklama\" \"Hedef Kitle\"")
        sys.exit(1)

    product = sys.argv[1]
    description = sys.argv[2]
    audience = sys.argv[3] if len(sys.argv) > 3 else "genel kitle"

    outdir = create_output_dir(product)
    slug = slugify(product)

    files = {
        "5_sosyal_post.md": generate_social_posts(product, description, audience),
        "3_topluluk_yorumu.md": generate_community_comments(product, description, audience),
        "2_seo_icerik.md": generate_seo_content(product, description, audience),
        "1_email_zinciri.md": generate_email_chain(product, description, audience),
        "1_takip_takvimi.md": generate_followup_schedule(product, audience),
    }

    for filename, content in files.items():
        path = os.path.join(outdir, filename)
        with open(path, "w") as f:
            f.write(content)

    summary = []
    for k in files:
        parts = k.split("_")
        label = parts[1].replace(".md", "")
        summary.append(f"{parts[0]} {label}")
    print(f"'{slug}/ icin {len(files)} icerik olusturuldu: {', '.join(summary)}")

if __name__ == "__main__":
    main()
