# Kod Denetim Metodolojisi — Sistem Sağlık Taraması

## Ne Zaman Kullanılır
- "Sistem eksiklerini tespit et", "gap analysis yap", "kod kalitesi kontrol et" gibi isteklerde
- Yeni bir modül/agent eklendikçe periyodik denetim
- Production öncesi kalite kapısı

## Tarama Parametreleri

Her .py dosyası için şu metrikleri topla:

| Metrik | Ne Anlama Gelir | Eşik |
|--------|----------------|------|
| **Satır sayısı** | Dosya karmaşıklığı | <100 = ince/şüpheli, >500 = bölünme adayı |
| **Fonksiyon sayısı** | İş mantığı yoğunluğu | <5 = muhtemelen stub |
| **Stub fonksiyon** | `def f():\n    pass` pattern | >0 = eksik implementasyon |
| **TODO/FIXME** | Bilinen eksikler | >0 = takip gerekli |
| **pass sayısı** | Boş bloklar | Fazlaysa implementasyon eksik |
| **class var mı** | OOP yapısı | Yoksa basit script |
| **try/except** | Error handling | Yoksa kritik eksik |
| **Redis kullanımı** | Entegrasyon | Agent'larda olmalı |
| **logging kullanımı** | Observability | print() varsa migration gerekli |
| **async def** | Concurrency | 0 = throughput sınırlı |

## Tarama Script'i (Tek Komut)

```bash
cd /opt/hermes/jeff_v2 && python3 << 'PYEOF'
import os, re
base = "/opt/hermes/jeff_v2"
skip = {'_archive', '_archive_faz0_20260806', '__pycache__', 'build', 'venv'}
for root, dirs, files in os.walk(base):
    dirs[:] = [d for d in dirs if d not in skip]
    for f in files:
        if not f.endswith('.py'): continue
        path = os.path.join(root, f)
        rel = os.path.relpath(path, base)
        try:
            with open(path) as fh: content = fh.read()
        except: continue
        lines = content.split('\n')
        lc = len(lines)
        fn = len(re.findall(r'def \w+', content))
        stub = len(re.findall(r'def \w+[^:]*:\s*\n\s*pass', content))
        td = sum(1 for l in lines if 'TODO' in l or 'FIXME' in l)
        has_cls = 'class ' in content
        has_try = 'try:' in content
        has_rd = 'redis' in content.lower()
        has_log = 'logging' in content or 'logger' in content
        has_async = 'async def' in content
        flags = []
        if stub > 0: flags.append(f'STUB:{stub}')
        if td > 0: flags.append(f'TODO:{td}')
        if not has_try and fn > 5: flags.append('NO_TRY')
        if not has_log and lc > 100: flags.append('NO_LOG')
        if lc < 100 and fn < 5: flags.append('THIN')
        flag_str = ' ⚠️ ' + ', '.join(flags) if flags else ''
        print(f"{rel:<50} {lc:>5} satır, {fn:>3} func{flag_str}")
PYEOF
```

## Kırmızı Bayraklar (Hemen Aksiyon Gerektiren)

| Durum | Severity | Aksiyon |
|-------|----------|---------|
| Test import ettiği modül yok | 🔴 KRİTİK | Modülü yaz veya testi düzelt |
| Self-healing restart yapamıyor | 🔴 KRİTİK | psutil/subprocess entegre et |
| Agent <150 satır, LLM çağrısı yok | 🔴 KRİTİK | Gerçek iş mantığı ekle |
| Test coverage %0 | 🔴 KRİTİK | pytest setup + test yaz |
| requirements.txt yok | 🟡 YÜKSEK | pip freeze + temizlik |
| Logging yok (dosya >100 satır) | 🟡 YÜKSEK | print→logging migration |
| try/except yok (5+ fonksiyon) | 🟡 YÜKSEK | Error handling ekle |
| Redis şifresiz | 🟡 YÜKSEK | Auth + TLS |
| 0 async fonksiyon | 🟢 ORTA | asyncio geçiş planla |

## Rapor Formatı

1. **Özet tablo:** Toplam dosya, satır, stub, TODO, coverage
2. **Durum tablosu:** Çalışan / Kısmi / Eksik sınıflandırması
3. **Gap analysis:** Gap, severity, effort, öncelik
4. **Yol haritası:** Fazlara ayrılmış, zaman tahminli
5. **Risk değerlendirmesi:** Olasılık × etki matrisi

## Örnek Kullanım (Jeff 4.0 — Ağustos 2026)

Bu metodoloji ile Jeff 4.0 sistemi tarandı. Sonuçlar:
- 34 aktif .py dosyası, 5,776 satır
- 1 stub fonksiyon, 0 TODO/FIXME
- Test coverage: ~%0 (2 test dosyası, 244 satır)
- Logging coverage: %18 (6/34 dosya)
- Error handling: %50 (17/34 dosya)
- Async: 0 fonksiyon
- Kritik bulgu: 2 test dosyası olmayan modülleri import ediyor (crash)
- Kritik bulgu: Self-healing sadece izliyor, restart yapamıyor
