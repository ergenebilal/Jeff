#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/hermes/hermes_data')
from tools import web_cek, dosya_ekle, log_hata, telegram_mesaj_gonder
import datetime

KAYNAKLAR = [
    ("https://github.com/trending", "github_trending"),
    ("https://news.ycombinator.com", "hacker_news"),
    ("https://www.reddit.com/r/programming.json", "reddit_programming"),
]

def topla_ve_kaydet():
    yeni_eklenen = []
    for url, kaynak_adi in KAYNAKLAR:
        try:
            icerik = web_cek(url)
            dosya_adi = f"/tmp/feed_{kaynak_adi}_{datetime.date.today()}.txt"
            with open(dosya_adi, 'w', encoding='utf-8') as f:
                f.write(f"Kaynak: {url}\nTarih: {datetime.date.today()}\n\n{icerik[:5000]}")
            sonuc = dosya_ekle(dosya_adi)
            yeni_eklenen.append(f"{kaynak_adi}: {sonuc}")
        except Exception as e:
            log_hata("auto_feed", f"{kaynak_adi} hatası: {e}", "tekrar dene")
    return yeni_eklenen

if __name__ == "__main__":
    print(f"[{datetime.datetime.now()}] Beslenme başladı...")
    sonuc = topla_ve_kaydet()
    print(f"Eklenenler: {sonuc}")
    # Telegram'a bildirim gönder
    if sonuc:
        mesaj = f"🌿 Günlük beslenme tamamlandı.\nEklenenler: {', '.join(sonuc)}"
    else:
        mesaj = "⚠️ Beslenme yapıldı ancak hiçbir kaynak eklenemedi. Logları kontrol et."
    telegram_mesaj_gonder(mesaj)
