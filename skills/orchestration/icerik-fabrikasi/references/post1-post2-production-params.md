# Post 1+2 — Production Parameters (Approved 06.07.2026)

## Post 1: "Sisteminiz Sizi Yavaşlatıyor" (Track 1 — Sorun→Çözüm)

### Slide Yapısı
| Slide | Badge | Title / Hook | List |
|-------|-------|-------------|------|
| 1 — Cover | **OPERASYON** | "Sisteminiz Sizi / Yavaşlatıyor" | — |
| 2 — Loss | **KAYIP** | "Sisteminiz Size Ne Kaybettiriyor?" | 3 items |
| 3 — Solution | **ÇÖZÜM** | "Üç Adımda Dönüşüm" | 3 items |
| 4 — Result | **SONUÇ** | "Değişen Ne Olacak?" | 3 items |
| 5 — CTA | **SIRADAKİ** | "İşletmeniz İçin / Bir Adım" | 2-line body |

### Caption
```
Sisteminiz sizi yavaşlatıyor.

Her gün tekrarlayan işler, takip edilmeyen müşteriler ve sezgiye dayalı kararlar... İşletmenizin büyümesini engelleyen görünmez bir duvar.

Bunu değiştirmek mümkün.

3 adımda dönüşüm:
1. Mevcut sisteminizi haritalandırın
2. Size özel yol haritasını çıkarın
3. Adım adım dönüşümü başlatın

Sonuç? Operasyonel yük azalır, müşteri takibi otomatikleşir, kararlar veriye dayanır.

Sisteminizin size ne kaybettirdiğini görmek için bir adım atın.
```

### Etiketler
`#işletme #operasyon #dijitaldönüşüm #verimlilik #işgeliştirme #kurumsal #sistem #otomasyon #büyüme #işletmeçözümleri #ergeneai`

---

## Post 2: "Dijital Dönüşümün 3 Temel Kuralı" (Track 2 — Eğitim/Rehber)

### Slide Yapısı
| Slide | Badge | Title / Hook | List |
|-------|-------|-------------|------|
| 1 — Cover | **EĞİTİM** | "Dijital Dönüşümün / 3 Temel Kuralı" | — |
| 2 — Kural 1 | **KURAL 1** | "Önce Süreç, Sonra Teknoloji" | 3 items |
| 3 — Kural 2 | **KURAL 2** | "Küçük Başla, Hızlı Büyü" | 3 items |
| 4 — Kural 3 | **KURAL 3** | "Veriyle Yönet" | 3 items |
| 5 — CTA | **SIRADAKİ** | "Dönüşüm İçin / İlk Adımı Atın" | 2-line body |

### Caption
```
Dijital dönüşümün 3 temel kuralı:

1. Önce süreç, sonra teknoloji
İş akışını haritalandır, tıkanıklıkları bul, sonra doğru aracı seç.

2. Küçük başla, hızlı büyü
En büyük kaybın olduğu alandan başla, kazanımı gör, genişlet.

3. Veriyle yönet
Tüm operasyonu tek panoda gör, kararları veriye dayandır.

Dönüşüm bir adım uzakta. ErgeneAI ile başlayın.
```

### Etiketler
`#dijitaldönüşüm #eğitim #işletme #operasyon #verimlilik #kurumsal #sistem #büyüme #strateji #ergeneai`

---

## Ortak Visual System

| Parametre | Değer |
|-----------|-------|
| Canvas | 1024×1024 px |
| Background | `bg_operations.png` (FAL FLUX 2 dark office) |
| Overlay | radial α(10→50), dark (8,16,13) |
| Card width | %90 (922px) |
| Card position | centered, CARD_Y=120, CARD_H=560 |
| Card fill | (8,16,13) α 165 |
| Inner glow | white α 30→0 (top→bottom) |
| Edge fade | symmetric, 60px each side, α 0→175 |
| Shadow | (0,0,0) α 70, blur 28px, offset +10/+14 |
| Accent borders | top 1px α 80, bottom 2px α 180, #81E36F |
| Logo | top-center, 110px, y=18 |
| Hook | Inter Bold 105px, line spacing 115px |
| Badge | Inter Bold 20px, centered, #81E36F bg |
| List text | Inter Bold 28px |
| List numbers | Inter Bold 34px, #81E36F |
| Title | Inter Bold 50px, centered |
| Body (CTA) | Inter Bold 26px, centered |
| URL pill | 22px, centered, radius 20, pill_h 42 |
| URL pill fill | (13,45,12) dark green |
| URL pill outline | #81E36F, 1px |
| URL pill text | #FFFFFF, exact centered (see centering formula) |
| Slide count | 5 slides per post |
| Delivery | Daily cron 08:00, @ergeneaiicerik_Bot |

## Render Scripts
- Post 1: `/opt/hermes/instagram-pipeline-multi/render_carousel_v3.py`
- Post 2: `/opt/hermes/instagram-pipeline-multi/render_post2_v3.py`
- Delivery: `~/.hermes/scripts/post1_daily_delivery.sh`
- Cron: `0 8 * * *`, deliver=all, job_id=2a15805332d5
