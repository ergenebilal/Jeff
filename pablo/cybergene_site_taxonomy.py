#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CYBERGENE.CO KONU HARİTASI (SITE PILLAR TAXONOMY)
---------------------------------------------------
Instagram içerik önerilerinin HANGİ konuyu kaç kez işlediğini ölçmek için
kullanılan sabit referans. Kaynak: cybergene-web reposunun kendisi, kod
üzerinden üretilmez — cybergene.co'da fiilen yayında olan dört hizmet
sütunu ve dört süreç adımıdır.

Kaynak dosyalar (tek gerçeklik kaynağı buradadır, burası bir KOPYADIR):
- cybergene-web/src/i18n/tr.json  → service1..4, service1..4Description/Example, step1..4
- cybergene-web/src/components/Services.astro
- cybergene-web/src/components/Process.astro

cybergene.co'nun manşeti veya hizmet metinleri değişirse bu dosya elle
güncellenmelidir; otomatik senkron yoktur. Bu, Instagram içeriğinin
sitenin güncel kapsamını yanlış yansıtmasını önlemek için bilinçli bir
manuel kontrol noktasıdır.
"""

# cybergene.co'nun dört hizmet sütunu ("Services" bölümü) — Instagram içeriği
# NE hakkında olduğuyla ilgili birincil eksen. "visual_family" (instagram_editorial_gate.py)
# bunun NASIL anlatıldığıyla ilgili ayrı bir eksendir; ikisi karıştırılmaz.
SITE_PILLARS = {
    "AI Agents": "İşletme adına çalışan dijital çalışma arkadaşları (örn. karşılama, teklif, müşteri takibi).",
    "AI Automation": "Tekrar eden süreçleri daha akıllı sistemlere dönüştürme (örn. dekont eşleştirme, sabah özeti).",
    "AI Integration": "Yapay zekâyı mevcut araç/iş akışlarına bağlama (örn. takvim, CRM, WhatsApp, muhasebe).",
    "Custom AI Systems": "İşletmeye özel, hazır kalıba girmeyen sistemler.",
    "Süreç ve yaklaşım": (
        "Sitenin 'Dinleriz → Analiz Ederiz → Tasarlarız → Geliştiririz' akışı ve genel AI "
        "benimseme mantığı (P01–P03 tarzı temel/kavramsal içerik burada durur)."
    ),
}

PROCESS_STEPS = ["Dinleriz", "Analiz Ederiz", "Tasarlarız", "Geliştiririz"]

# master-v0.1.md §6: "Hiçbir ana mesaj markayı tek sektöre daraltmaz." Bu yüzden
# burada onaylı/sabit bir sektör listesi YOKTUR — sektörler yalnız örnektir,
# içerik pillar'ı her zaman yukarıdaki 5 madde ile sınırlıdır.

# master-v0.1.md §5 / playbook-v1.0.md §3: "Son 6 gönderide tek sektörün veya
# tek görsel ailenin baskınlaşması editoryal gözden geçirme sebebidir." Bu eşik
# o kuralın kod karşılığıdır — kaç son kayıt taranır ve kaç tanesi aynıysa uyarı basılır.
RECENCY_WINDOW = 6
RECENCY_DOMINANCE_THRESHOLD = 4  # son RECENCY_WINDOW kayıttan en az bu kadarı aynıysa uyar
