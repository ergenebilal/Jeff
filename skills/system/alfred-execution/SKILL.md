---
name: alfred-execution
category: system
description: Execute digital, UI, browser, and physical actions on Bilal's local Windows machine (Alfred/Pablo) directly with sub-second latency and zero hallucination.
---

# Alfred Direct Execution Tool (Windows - Pablo Node)

Alfred (Pablo), senin yerel Windows makinesindeki (LENOVO - Tailscale `100.89.26.86:7788`) **doğrudan icra aracındır (execution tool)**.
Senin ellerin ve gözlerindir. Sen karar verirsin, `alfred` komutuyla icra edersin, sonucu anında görürsün.

---

## 🛑 SIFIR HALÜSİNASYON VE KESİN GÖRSEL/DOM KANITI PROTOKOLÜ (MUTLAK KURAL)

1. **ASLA KÖRLEME KOORDİNATLA TIKLAMA (BLIND PYAUTOGUI YASAKTIR):**
   - X/Twitter, LinkedIn, YouTube vb. web sayfalarında ve pencerelerde ekran koordinatlarını tahmin ederek (`pyautogui.click(w*0.5, h*0.35)`) tıklama yapan Python scriptleri yazmak KESİNLİKLE YASAKTIR!
   - Web arayüzlerinde tıklamak, form doldurmak veya metin yazmak için DAİMA `alfred browser_act` veya doğrulanmış DOM grounding hedefleri kullanacaksın.

2. **EXIT CODE 0 VE KENDİ YAZDIĞIN PRINT'LER KANIT DEĞİLDİR:**
   - Bir Python scripti hata vermeden bitti diye (`exit_code: 0`) veya scriptin içine `print('TWEET_PASTED_SUCCESSFULLY')` yazdın diye işlem BAŞARILI SAYILMAZ!
   - Kendi uydurduğun print çıktılarını kanıt sayarak Bilal'e *"Gördün mü şef, sıfır hatayla yaptık 😎"* gibi asılsız ve sahte başarı mesajları vermek EN BÜYÜK PROTOKOL İHLALİDİR.

3. **GÖRSEL / DOM DOĞRULAMA ZORUNLUDUR:**
   - Bir UI veya web eylemi yaptığında (özellikle tweet yazma, form doldurma, video açma vb.), işin gerçekten ekranda olup bittiğini görmek için:
     * `alfred screenshot -o /tmp/screen.png` ile ekran görüntüsü alacaksın.
     * `alfred browser_read state` ile pencere ve DOM durumunu okuyacaksın.
   - Ekranda gözünle görmediğin hiçbir eylem için "yaptım", "yazı düştü" deme!

4. **EKRAN GÖRÜNTÜSÜ ALMA KURALI:**
   - Asla PowerShell veya Python içinden `pyautogui.screenshot()` çalıştırma (Windows arka plan oturumunda desktop heap hatası verir).
   - Ekran görüntüsü almak için HER ZAMAN doğrudan `alfred screenshot -o /tmp/screen.png` komutunu kullan.

5. **browser_act ≠ Görünen Chrome (22.09.2026 Kanıtlandı — KRİTİK TUZAK):**
   - `alfred browser_act fill/click/press` komutları Playwright'ın **kendi headless context**'ine gider. Kullanıcının ekranında açık Chrome penceresine **ulaşamaz**. `browser_read state` → `about:blank` dönüyorsa bu tuzaktasın.
   - **Çalışan yol:** `alfred browser "URL"` ile Chrome'u öne al → Pablo Win32 Focus Shield pencereyi aktive eder → `ctrl+enter` veya klavye kısayoluyla işlemi tamamla.
   - **Çalışmayan yollar (denendi, hepsi başarısız):** `browser_act fill/click` (headless), `SendKeys` via PowerShell (CREATE_NO_WINDOW), Win32 `mouse_event` (CREATE_NO_WINDOW oturumu), remote debugging + farklı user-data-dir (oturum yok).
   - **Kural:** Görünen Chrome'a eylem gerekiyorsa → `alfred browser "URL"` ile öne al, klavye kısayolu kullan. DOM seçiciye güvenme.

---

## 🛠️ KULLANIM KOMUTLARI VE ARAÇ REHBERİ

### 1. Tarayıcıda URL Açma
```bash
# Tarayıcıda bir site açar ve ekranda ön plana getirir:
alfred browser "https://x.com"
alfred browser "https://youtube.com"
```

### 2. Tarayıcıda DOM Hedefli Eylem Yapma (`browser_act`)
Web sayfalarında tıklama ve metin yazma işlemleri DAİMA bu komutla yapılır:
```bash
# A) Metin alanını temizle ve metin yaz (Fill / Type):
alfred browser_act fill --target "[data-testid='tweetTextarea_0']" --value "CyberGene Otonom Ajan Ekibi canlı test yayını!"
alfred browser_act fill --target "textarea" --value "Mesaj metni"
alfred browser_act fill --target "input[name='search_query']" --value "pablo picasso"

# B) Butona veya öğeye tıkla (Click):
alfred browser_act click --target "[data-testid='tweetButtonInline']"
alfred browser_act click --target "button[type='submit']"

# C) Özel tuşa bas (Press: enter, space, esc):
alfred browser_act press --value "space"
alfred browser_act press --value "enter"

# D) Sayfayı kaydır:
alfred browser_act scroll --value "500"
```

### 3. Tarayıcı Durumunu ve Aktif Sayfayı Okuma (`browser_read`)
```bash
# Aktif sekme başlığını ve URL'sini doğrula:
alfred browser_read state

# Sayfa metnini oku:
alfred browser_read text
```

### 4. Ekran Görüntüsü Alma ve Görsel Doğrulama (`screenshot`)
```bash
# Windows masaüstünün canlı ekran görüntüsünü sunucuya indirir:
alfred screenshot -o /tmp/verified_screen.png

# İndirilen görüntüyü terminalde doğrula veya boyuta bak:
ls -lh /tmp/verified_screen.png
```

### 5. Windows PowerShell / Terminal Komutları (`shell`)
```bash
# PowerShell komutu çalıştırma:
alfred shell "Get-Process | Select-Object -First 5"
alfred shell "Get-Service | Where-Object Status -eq 'Running'"
```

### 6. Windows Dosya İşlemleri (`read` / `write` / `ls`)
```bash
# Dosya oku:
alfred read "C:\Users\lenovo\Desktop\ornek.txt"

# Dosya yaz:
alfred write "C:\Users\lenovo\Desktop\not.txt" "Doğrulanmış içerik"

# Dizin listele:
alfred ls "C:\Users\lenovo\Desktop"
```

### 7. Açık Pencereleri Listeleme ve Win32 Odaklama (`windows` / `focus`)
```bash
# Windows masaüstündeki açık pencereleri (başlık, HWND, boyut) listele:
alfred windows

# Belirtilen pencereyi Win32 Focus Shield ile 0ms gecikmeyle en öne getir ve maksimize et:
alfred focus "Instagram"
alfred focus "Chrome"
alfred focus "Aç"
```

### 8. Yerel Dosya Seçme / Yükleme İletişim Kutusuna Dosya Gönderme (`upload_dialog`)
```bash
# Windows 'Aç' / 'Open' dosya seçme iletişim kutusuna bir veya birden fazla dosya yapıştırıp Enter'a basar:
alfred upload_dialog "C:\Users\lenovo\Desktop\Sosyal Medya\instagram\2026-09-25\1.png" "C:\Users\lenovo\Desktop\Sosyal Medya\instagram\2026-09-25\2.png"
```

### 9. WhatsApp Masaüstü Mesaj Taslağı (`wa`)
```bash
alfred wa 905520947032 "Toplantı hazır."
```

### 10. Sağlık & Canlılık Kontrolü
```bash
alfred ping
alfred health
```

---

## 🛑 DÖNGÜ YASAĞI VE 2-HATA DEVRE KESİCİ (CIRCUIT BREAKER)

1. **AYNI VARYASYONU TEKRARLAMAK YASAKTIR:**
   - Eğer bir komut veya strateji 2 KEZ ÜST ÜSTE BAŞARISIZ OLURSA (örneğin PowerShell ile pencereye odaklanma denemesi veya bulunamayan süreç), 3. bir PowerShell varyasyonu denemek KESİNLİKLE YASAKTIR.
   - Kör döngüye girip deneme-yanılma yapmak Bilal'i yorar ve sistemi kilitler.

2. **DEVRE KESİCİ ADIMLARI (PİVOT):**
   - 2. hatanın hemen ardından:
     * `alfred screenshot -o /tmp/screen.png` ile ekranın gerçek görüntüsünü al.
     * `alfred windows` ile açık pencerelerin gerçek listesini ve başlıklarını al.
   - Durumu teşhis et: Hedef pencere açık mı? Dosya seçme diyaloğu mu açık? Kullanıcı girişi mi gerekiyor?
   - Stratejini kökten değiştir veya eğer kullanıcı müdahalesi gerekiyorsa (login, 2FA vb.) Bilal'e durumu 10 saniye içinde açıkça bildir!

---

## 📱 SOSYAL MEDYA VE WEB İÇERİK YÜKLEME OYNATMA LİSTESİ (PLAYBOOK)

1. **WEB APP KURALI:**
   - Instagram, Twitter/X, LinkedIn vb. Windows Store uygulaması DEĞİLDİR. Asla `Get-AppxPackage` veya `Start-Process 'instagram:'` çalıştırma. Chrome sekmesidir.

2. **ADIM ADIM YÜKLEME AKIŞI:**
   - **Adım 1 (İçerik Kontrolü):** `alfred ls "C:\Users\lenovo\Desktop\Sosyal Medya\..."` ve `alfred read "..."` ile görselleri ve metni doğrula.
   - **Adım 2 (Pencere Kontrolü):** `alfred windows` ile Chrome veya ilgili platform sekmesinin açık olduğunu doğrula.
   - **Adım 3 (Öne Getirme):** `alfred focus "Instagram"` (veya `alfred focus "Chrome"`) ile pencereyi 0ms'de öne al.
   - **Adım 4 (Dosya Seçim Diyaloğu):** Dosya seçici açıldığında DOM etkileşimi donar. Dosyaları aktarmak için DAİMA `alfred upload_dialog "<dosya1>" "<dosya2>"` komutunu kullan.
   - **Adım 5 (Görsel Doğrulama):** `alfred screenshot -o /tmp/upload_check.png` ile dosyaların yüklendiğini teyit et.
   - **Adım 6 (Onay Kapısı):** Metni yapıştır, ekran görüntüsü al ve son "Paylaş" / "Post" butonuna basmadan önce KESİNLİKLE Bilal'den onay (`request_human_approval`) iste!

---

## 🎯 STANDART İCRA PROTOKOLÜ (ADIM ADIM)

1. **Önce Sayfayı Aç veya Öne Getir:** `alfred focus "Chrome"` veya `alfred browser "https://x.com"`
2. **Durumu Kontrol Et:** `alfred windows` ve `alfred browser_read state`
3. **DOM Seçicisiyle Metni Gir:** `alfred browser_act fill --target "[data-testid='tweetTextarea_0']" --value "Metin"`
4. **Görsel Kanıt Al:** `alfred screenshot -o /tmp/tweet_kaniti.png`
5. **Kanıtı Doğrula:** Ekran görüntüsü başarıyla alındıysa ve metin ekrandaysa Bilal'e net ve dürüst sonuç bildir. Asla tahmin yürütme!

