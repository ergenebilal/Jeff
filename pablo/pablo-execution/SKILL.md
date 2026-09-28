---
name: pablo-execution
category: system
description: Pablo (Windows Agent) — Windows GUI ve masaüstü icra düğümü.
---

# Pablo Execution Protocol (Windows Edge Agent)

Pablo, Bilal Ergene'nin Windows makinesindeki (Lenovo) **fiziksel masaüstü ve icra koludur (Edge Execution Operator)**.
Jeff (Sunucu Core) stratejiyi kurar ve hafızayı (`MEMORY.md`) tutar; Pablo ise Windows masaüstü oturumunda emri alıp 0ms Win32 Focus Shield ile Bilal'in gözü önünde icra eder.

## Mimari Hiyerarşi & Tek Gerçeklik Kaynağı
```
Bilal Ergene (Nihai Karar / %99 Otonomi)
        │
        ▼
    Jeff (Hermes v4.1, Linux) — Strateji, Orkestrasyon, Tek Gerçeklik Kaynağı (MEMORY.md)
        │ REST / Bridge (100.89.26.86:7788 / X-Alfred-Token: cybergene-bridge-2026)
        ▼
    Pablo (Windows Native Hermes) — Fiziksel İcra Kolu, Hafızasız Operatör
```
- **Hafıza Modeli (Seçenek B):** Pablo kendi kalıcı `MEMORY.md` kopyasını tutmaz. Tek gerçeklik kaynağı Jeff'in `/home/hermes/.hermes/MEMORY.md` dosyasıdır. Pablo yalnızca geçici oturum state'i tutar.

## İcra & Odak Prensipleri (0ms Win32 Focus Shield)
1. **Gözünün Önünde İcra (Foreground Rule):** Masaüstü/GUI görevleri asla arka planda (headless) veya simge durumunda kalmaz. Her pencere Bilal'in gözü önünde, tam ekranda ve en ön safta (`HWND_TOPMOST` / `SW_SHOWMAXIMIZED`) açılır.
2. **Windows Odak Kalkanı (Focus Shield):** Windows `SetForegroundWindow` kısıtlamalarını aşmak için Win32 API (`SetWindowPos`, `AppActivate`, Alt-Key injection) ve `creationflags=0x08000000` (CREATE_NO_WINDOW background subprocesses) kullanılır.
   - **⚠️ SINIR:** Pablo `CREATE_NO_WINDOW` ile çalıştığı için `wscript.shell AppActivate` + `SendKeys` odak penceresi bulamaz ve `False` döner — tuş gönderilmez. Bu yol browser odak değiştirme için çalışmaz.
3. **Çift Katmanlı Approval Gate (Kırmızı Çizgiler):**
   Jeff onay vermiş olsa bile, Pablo aşağıdaki eylemlerde otonom çalışmayı durdurur ve Bilal'in Telegram onayını bekler:
   - Kamuoyuna açık paylaşım (post, tweet, yorum)
   - Yeni/soğuk kişiye mesaj gönderimi (WhatsApp, DM)
   - Yıkıcı sistem/dosya silme işlemleri
   - Finansal harcama / ödeme

## API & Kullanım Uçları

### Canlılık ve Health Kontrolü
```bash
curl http://100.89.26.86:7788/health
```

### Görev İcrası (Jeff → Pablo via `alfred` CLI / Python)
Sunucudaki `alfred` CLI aracı doğrudan Pablo'ya (`100.89.26.86:7788`) istek atar:
```bash
# Tarayıcıda URL/Video Açma (Ön planda):
alfred browser "https://www.youtube.com/watch?v=BqsmECm4t3E"

# Tarayıcı Eylemleri (Tıklama / Doldurma / DOM Seçicisi):
alfred browser_act fill --target "[data-testid='tweetTextarea_0']" --value "CyberGene Canli Test Yayini"
alfred browser_act click --target "[data-testid='tweetButtonInline']"

# Dosya Gezgini / Sürücü Açma (PowerShell Start-Process):
alfred shell "powershell -command \"Start-Process 'C:\\'\""

# Ekran Görüntüsü Alma (HER ZAMAN alfred screenshot kullan, asla pyautogui.screenshot çağırma!):
alfred screenshot -o /tmp/pablo_screen.png

# Shell Komutu Çalıştırma (Siyah cmd penceresi açmadan):
alfred shell "Get-Process | Select-Object -First 5"
```

## 🛑 KRİTİK GÜVENLİK KURALLARI & JEFF PİTFALL DEFTERİ

1. **KÖR TIKLAMA YASAĞI (No Blind Coordinates):**
   - Web sayfalarında (X.com, LinkedIn vb.) rastgele koordinat uydurarak `pyautogui.click(w * 0.5, h * 0.38)` gibi tıklamalar YAPMAK KESİNLİKLE YASAKTIR.
   - Sayfa yapısı değişkendir; kör tıklama boşluğa gider, ardından basılan Ctrl+V hiçbir yere yapışmaz.
   - **Doğru Yol:**
     a) DOM Seçicisi ile: `alfred browser_act fill --target "..." --value "..."` veya
     b) Chrome DevTools / Klavye Tab navigasyonu veya
     c) Önce `alfred screenshot -o /tmp/screen.png` alıp elementi görsel olarak teyit ettikten sonra tıklamak.

2. **YALANCI BAŞARI VE HALÜSİNASYON YASAĞI (Evidence Mandatory):**
   - Kendi yazdığın Python scriptinin exit_code 0 vermesi veya print('SUCCESS') basması eylemin UI'da gerçekleştiğini KANITLAMAZ.
   - Ekranı görmeden asla kullanıcıya "Yaptım şef, ekranda gördün mü? 😎" deme.
   - Ekranda teyit edemediysen dürüst ol: "Komutu gönderdim ancak ekran görüntüsüyle doğrulayamadım, kontrol eder misin?" de.

3. **EKRAN GÖRÜNTÜSÜ ALMA KURALI:**
   - Windows üzerinde `python -c "import pyautogui; pyautogui.screenshot()"` çalıştırmak arka plan oturumunda `OSError: screen grab failed` verir.
   - Ekran görüntüsü almak için HER ZAMAN sunucudan `alfred screenshot -o /tmp/screen.png` komutunu kullan. Bu komut Pablo Node'un Win32 masaüstü bağlayıcısı üzerinden hatasız 1920x1200 ekran görüntüsü çeker.

4. **Explorer Açma Pitfall:** Doğrudan `explorer.exe C:\` subprocess ile çağrıldığında exit code 1 döndürebilir; dosya gezgini pencerelerini açmak için `powershell -command "Start-Process 'C:\\'"` tercih et.

5. **Türkçe/Unicode Karakter Yapıştırma:** `SendKeys` veya `typewrite` Türkçe ve Unicode karakterleri (`ı, ğ, ş, ç, İ, Ğ`) bozar veya yazamaz. Doğru yöntem: `win32clipboard` ile panoya Unicode metin yazıp `pyautogui.hotkey('ctrl', 'v')` ile yapıştırmaktır.

6. **Pablo'ya Çok Satırlı Python Betiği Gönderme:** PowerShell üzerinden karmaşık çok satırlı python kodu gönderirken tırnak/kaçış hatalarını önlemek için betiği base64 encode edip Pablo'da decode ederek çalıştır:
  `python -c "import base64; open('C:/path/script.py', 'wb').write(base64.b64decode('...'))"`

7. **`browser_act` PLAYWRIGHT CONTEXT SPLIT (KRİTİK):**
   - `alfred browser <url>` görünen Chrome penceresini açar. `alfred browser_act` ise Playwright'ın **kendi ayrı headless context**'ine bağlanır. İki instance birbirinden haberdar değildir.
   - **Belirti:** `alfred browser_read state` → `"url": "about:blank"` döner, oysa ekranda hedef site açık görünür. Bu durumda `browser_act` hiçbir zaman görünen sekmeye ulaşamaz — kaç kez denersen dene.
   - **Tanı adımı:** Her `browser_act` denemesinden önce `alfred browser_read state` çalıştır. URL `about:blank` ise split-context tuzağı aktif.
   - **2 denemeden sonra dur:** Context split tespit edilince aynı `browser_act` komutunu tekrar deneme — mekanizma aynı, sonuç aynı. Hemen aşağıdaki karar ağacına geç.
   - **Karar ağacı (öncelik sırasıyla):**
     1. **API yolu varsa kullan** — hedef platformun resmi API'si (X API, Gmail API vb.) her zaman en güvenilir.
     2. **Bilal'e devret** — görünen Chrome'da tek tıkla biten işlemleri Bilal manuel tamamlasın; bu en hızlı yoldur.
     3. **Remote debugging (son çare):** Chrome'u `--remote-debugging-port=9222` ile yeniden başlat. **UYARI:** `--user-data-dir` parametresi ASLA verme — farklı profil açılırsa oturum cookie'leri kaybolur, giriş sayfasına düşer. Mevcut Chrome'u kapatmadan önce Bilal'e sor:
   ```bash
   # DOĞRU (--user-data-dir YOK):
   alfred shell "powershell -command \"Get-Process chrome | Stop-Process -Force; Start-Sleep 2; Start-Process 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe' -ArgumentList '--remote-debugging-port=9222','https://hedef.com' -WindowStyle Maximized\""
   # YANLIŞ (oturumu siler):
   # ... -ArgumentList '--remote-debugging-port=9222','--user-data-dir=C:\\custom-dir' ...
   ```

8. **Win32 `mouse_event` CREATE_NO_WINDOW SINIRI:**
   - Pablo `CREATE_NO_WINDOW` (0x08000000) flag'iyle çalıştığı için Win32 `mouse_event` ve `SetCursorPos` çağrıları görünen masaüstü oturumuna ulaşamaz — tıklama boşluğa gider, `exit_code: 0` dönse bile.
   - `wscript.shell AppActivate` da aynı nedenle `False` döner ve odak değişmez.
   - Bu yolları denemek zaman kaybıdır; yukarıdaki karar ağacına geç.

8. **PowerShell / CMD Sarma Kuralı (`powershell -Command`):**
   - `alfred shell` komutuvarsayılan olarak `cmd.exe` ortamında çalışır.
   - PowerShell cmdlets (`Get-ChildItem`, `Get-Content`, `Select-Object` vb.) çalıştırılırken komut DAİMA `powershell -Command "..."` veya UTF-8 Türkçe karakter sorunu olmaması için `powershell -Command "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; Get-Content ..."` biçiminde sarmalanmalıdır.
   - Doğrudan `Get-ChildItem` yazılırsa `'Get-ChildItem' is not recognized as an internal or external command` hatası verir.

9. **Bridge API Task Pending Tuzağı:**
   - `POST http://127.0.0.1:7700/alfred/task` göreve `task_id` + `status: queued` döndürür ama Windows tarafındaki Alfred receiver çalışmıyorsa (bilgisayar kapalı, servis durmuş, Tailscale offline) task sonsuza kadar `pending` kalır.
   - **Tanı:** `GET /alfred/task/{task_id}` 15s sonra hâlâ `pending` dönüyorsa Windows tarafı komutu almıyor demektir — aynı komutu tekrar deneme.
   - **Doğru Body Formatı:** `{"type": "shell", "payload": {"cmd": "..."}, "timeout": 30}` — `task` alanı değil `type` alanı kullanılır; eksik `type` alanı `422 Field required` hatası döndürür.
   - **Pablo Direct API Token:** `http://100.89.26.86:7788/execute` doğrudan token ister (`X-Alfred-Token`); Bridge (`7700`) üzerinden gitmek daha güvenlidir.
   - **Durum tespiti:** `curl -s http://100.89.26.86:7788/health` → `{"ok": true, "status": "online"}` Pablo'nun ayakta olduğunu gösterir ama Alfred receiver'ın komutu işlediğini garantilemez — task pending kalıyorsa Bilal'e bilgisayarı kontrol ettir.
   - **Token Uyuşmazlığı Root Cause (KRİTİK):** Pablo `/health` endpoint'i token istemez (200 döner), ama `/execute` ve `/tasks` token zorunludur. Sunucu `cybergene-bridge-2026` token'ıyla çağırırken Pablo Windows tarafında farklı bir token bekliyorsa her zaman `401 Unauthorized` döner — Pablo online görünse bile hiçbir komut çalışmaz. Bridge `alfred_heartbeat` tablosunda son kayıt ~19 saat önceyse token uyuşmazlığı kesindir. **Teşhis:** `sqlite3 /home/hermes/jeff2/bridge/bridge.db "SELECT * FROM alfred_heartbeat ORDER BY ts DESC LIMIT 3"` ile son heartbeat zamanını kontrol et. **Çözüm:** Token'ı Bilal'den al (Pablo Windows config'indeki gerçek değer) ve sunucu tarafındaki `alfred_tool.py` içindeki `BRIDGE_KEY` değişkenini eşitle — ya da tam tersi, Pablo'nun config'ini sunucu token'ına güncelle. Token sunucu tarafındaki hiçbir dosyada saklanmaz (maskelenmiş), doğrudan Bilal'den alınmalıdır.

13. **Antigravity Bot Token Maskeleme Tuzağı (`@Antigravity_cybrgn_bot`):**
   - `/opt/hermes/antigravity_telegram_bot_hybrid.py` içindeki `BOT_TOKEN` değeri `"8837468670:***"` şeklinde maskelenmiştir — dosyada gerçek token yoktur.
   - `systemctl cat antigravity-telegram-bot` da token içermez (`Environment=PYTHONUNBUFFERED=1` dışında).
   - Process environment'ından (`/proc/<pid>/environ`) da token alınamaz.
   - **Çözüm:** Token'ı Bilal'den al veya `@Antigravity_cybrgn_bot`'a doğrudan Telegram'dan mesaj at — bot Windows'ta çalışıyorsa yanıt verir. Jeff bu bota HTTP ile ping atamaz.
   - **Bot'un Amacı:** Windows bilgisayarını Telegram'dan uzaktan yönetmek — Pablo'ya görev gönder, shell komutu çalıştır, screenshot al, ReAct agentic loop başlat. Deploy için: bota `shell cd C:\Users\lenovo\cybergene-web && .\deploy.ps1` gönder.

10. **Onay Korumalı (Approval-Gated) Görev Sorgulama:**
   - Pablo API `shell` eylemleri onay kapısına (`APPROVAL_REQUIRED`) takıldığında istemciye `APPROVAL_REQUIRED` ve `approval_id` döner.
   - Kullanıcı Telegram veya arayüzden onay verdikten sonra aynı komutu tekrar çalıştırıp yeni bir `approval_id` tetiklemek yerine, mevcut görevin sonucunu doğrudan `curl -s -H "X-Alfred-Token: cybergene-bridge-2026" http://100.89.26.86:7788/tasks/<task_id>` uç noktası üzerinden sorgulamak (reconcile) gerekir.

10. **Windows CLI Focus Lock ve Masaüstü Odaklama Döngüsü Yasağı (25.09.2026 — KRİTİK KURAL):**
   - Arka plan CLI süreçlerinden (`alfred shell`) WScript `AppActivate`, Win32 `SetForegroundWindow`, `SendKeys` veya pencere küçültme/odaklama betikleriyle masaüstündeki pencerelere (Chrome, Telegram, Perplexity vb.) tekrar tekrar odaklanmaya çalışmak Windows Focus Lock engeli nedeniyle hantal deneme-yanılma döngüsüne girer.
   - **Kural:** Masaüstündeki pencereleri arka plandan karmaşık PowerShell/Win32 focus betikleriyle öne çekmeye çalışarak zaman kaybetmek KESİNLİKLE YASAKTIR. Bilgi veya veri edinme işlemlerinde DAİMA doğrudan dosya okuma (`read_file`, `Get-Content`), API çağrısı veya `web_extract` kullan; masaüstü GUI odaklama döngüsüne girme.

11. **v1.1 Browser_Act İcra ve Güvenlik Protokolü (25.09.2026):**
   - **Jenerik Hedef Yasağı (`BLOCKED_AMBIGUOUS_TARGET`):** `--target "button"`, `--target "div"`, `--target "a"` gibi belirsiz ve jenerik seçiciler icra öncesi reddedilir. Spesifik role (`[role="button"][name="Not defteri oluştur"]`), `data-testid` veya benzersiz `has-text` seçicisi zorunludur. Birden fazla eşleşmede ilk öğe rastgele seçilmez.
   - **Sessiz Fallback Yasağı:** DOM tıklaması başarısız olduğunda native foreground `keybd_event` veya fare koordinatına sessiz geçiş yapılmaz. Doğrudan `BLOCKED` statüsü döner.
   - **Sonuç Ayrımı:** `ACTION_EXECUTED` (komut gönderildi) ile `OUTCOME_VERIFIED` (nesne/URL oluştu ve doğrulandı) birbirinden ayrılır. Yalnızca `OUTCOME_VERIFIED` durumunda kullanıcıya "tamamlandı" denir.
   - **Mükerrer İşlem Koruması:** Belirsiz (`UNKNOWN`) sonuçlarda aynı eylem tekrar tıklanmaz. Tekrar öncesi nesne varlığı doğrulanır.
   - **Çifte Başarısızlık Devre Kesicisi (Circuit Breaker):** Pencere odağı veya hedef doğrulama 2 kez üst üste başarısız olursa işlem anında dondurulup kanıtla birlikte `FAILED_CIRCUIT_BREAKER` bildirilir.

12. **Chrome CDP Otomasyon Profili ve Gerçek Bağlantı (25.09.2026):**
   - Kişisel Chrome profili kilitlenmelerini önlemek için `C:\CyberGene\ChromeAutomationProfile` yolunda özel otomasyon profili kullanılır.
   - Yerel CDP portu: `127.0.0.1:9223` üzerinden bağlanılır. `about:blank` sorunu aşılarak gerçek Gemini Notebook sekmeleri görünür hale gelir.
   - **Kanıtlanmış Doğrulama Taahhüdü:** Nesne oluşumu öncesi ve sonrası fark kaydedilir. Nesne ID ve URL teyit edilmeden (`OUTCOME_VERIFIED`) "tamamlandı" denmez.


### Desteklenen Eylemler
- `ping` / `health` — Canlılık ve durum kontrolü
- `shell` — Windows cmd/PowerShell (siyah pencere açmadan, 0x08000000)
- `screenshot` — 1920x1200 ekran görüntüsü yakalama
- `browser_open` / `browser_read` / `browser_act` — Ön plan Chrome/Edge otomasyonu
- `whatsapp_send` — WhatsApp Web taslak ve mesaj yönetimi
- `youtube_play` — Video açma ve oynatma
- `window_list` / `window_focus` — Pencere tarama ve en öne getirme
