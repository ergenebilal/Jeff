---
name: claude-code-entegrasyonu
category: system
description: Use when configuring Claude Code, MCPs, or design skills.
---

# Claude Code CLI ve Otonom Geliştirme Protokolü

Bu skill, yerel makinelerdeki (Windows / Linux) **Claude Code CLI** kurulumunu, MCP sunucu entegrasyonunu, Awwwards tasarım skill'lerini, Claude Code promptlama prensiplerini ve maliyet/token optimizasyon stratejilerini düzenler.

---

## 🚀 1. KURULUM VE VS CODE ENTEGRASYON AKIŞI

1. **İdeal Çalışma Ortamı:**
   - Claude Code yerel makinada (Windows / macOS / Linux) VS Code veya Cursor entegre terminali içinde çalıştırılır.
   - VS Code projenin kök klasöründe açılır, `Ctrl + ~` ile terminal başlatılır ve `claude` yazılır.
   - Bu sayede Claude Code dosyalarda değişiklik yaptığında VS Code editöründe canlı kod akışı izlenebilir.

2. **Varsayılan İzin Modu:**
   - Ekranda `accept edits on` (Shift+Tab ile geçiş yapılabilir) tutulur. Her dosya editinde onay beklemeden otonom kodlama sağlar.

---

## 🛠️ 2. WINDOWS MCP KONFİGÜRASYONU VE KRİTİK TUZAKLAR

### Windows `.claude.json` Konumu:
`C:\Users\<kullanıcı>\.claude.json` (`$env:USERPROFILE\.claude.json`)

### ⚠️ Kritik Windows Pitfall: `npx` ENOENT Bağlantı Hatası & `-y` Bayrak Hatası
1. **`claude mcp add` Komutunda `-y` Bayrağı YASAKTIR:** `claude mcp add` komutuna `npx -y` verilmesi `error: unknown option '-y'` hatası üretir. Doğru kullanım: `claude mcp add <isim> npx <paket-adı>`.
2. **Windows `stdio` ENOENT Bağlantı Hatası:** Windows GUI ve VS Code terminal uygulamalarında `stdio` MCP sunucuları eklenirken doğrudan `"command": "npx"` yazıldığında Windows `npx` yürütülebilir dosyasını bulamayabilir (`ENOENT` / `🔴 Failed` hatası).

**Kesin Çözüm:** `.claude.json` içindeki komutları `cmd.exe /c` sarmalayıcısı ile tanımlayın:

```json
{
  "mcpServers": {
    "notebooklm": {
      "command": "cmd.exe",
      "args": ["/c", "npx", "-y", "notebooklm-mcp"]
    },
    "sequential-thinking": {
      "command": "cmd.exe",
      "args": ["/c", "npx", "-y", "@modelcontextprotocol/server-sequential-thinking"]
    },
    "context7": {
      "command": "cmd.exe",
      "args": ["/c", "npx", "-y", "context7-mcp"]
    },
    "playwright": {
      "command": "cmd.exe",
      "args": ["/c", "npx", "-y", "@modelcontextprotocol/server-playwright"]
    },
    "figma": {
      "command": "cmd.exe",
      "args": ["/c", "npx", "-y", "@figma/mcp-server"]
    }
  }
}
```

### Global MCP Ekleme Komutu:
Tüm projelerde geçerli olması için `-s user` bayrağı kullanılır:
```powershell
claude mcp add -s user context7 npx context7-mcp
claude mcp add -s user playwright npx @modelcontextprotocol/server-playwright
claude mcp add -s user notebooklm npx notebooklm-mcp
claude mcp add -s user sequential-thinking npx @modelcontextprotocol/server-sequential-thinking
claude mcp add -s user figma npx @figma/mcp-server
```

---

## 🎨 3. AWWWARDS TASARIM SKILL PAKETİ VE PROMPTLAMA İLKELERİ

### Yüklü Skill'ler (`%USERPROFILE%\.claude\skills`):
1. **`frontend-design` (Anthropic Resmi):** Jenerik neon AI şablonlarını engeller, profesyonel tipografi, beyaz alan ve editoryal tasarım kuralları getirir.
2. **`taste-skill`:** Projedeki hareket, animasyon ve deneysel tasarım dengesini korur.
3. **`scroll-craft`:** GSAP, Framer Motion ve Lenis tabanlı akıcı kaydırma (scroll) animasyonları üretir.
4. **`design-dna`:** Bir web sitesinin görselinden/videosundan tipografi, renk ve ritim DNA'sını çıkararak yeni tasarıma uygular.

### 🔴 Problem-First & Outcome-Driven Promptlama Protokolü:
Claude Code / Codex'e tasarım veya refaktör direktifi hazırlarken:
- Mikromekanik kod tarifleri veya katı metin kalıpları dikte ETME.
- **Mevcut Kullanıcı Problemlerini** (örn. bilişsel yük, aşırı teknoloji gösterisi, gömülü kalan asıl değer) ve **Beklenen Kabul Kriterlerini (Outcome)** tanımla; tasarımı ve refaktör çözümlere ulaşmayı otonom ajanın aklına bırak.
- **Soyut Şov (Kötü) vs Somut İş Şovu (İyi) Ayrımı:** Soyut uzay noktaları, takımyıldız tuvalleri, radar hatları ve `DÇ-00`, `S-01`, `PATCH-A` gibi soğuk kod etiketleri müşteriyi boğar. Görsel şov, **Lüks Cam Efektli Somut İş Çıktı Kartlarında** (Randevu Defteri, Fatura-Dekont Eşleşmesi, Teklif Özeti) yaşatılmalıdır.

---

## 🧠 4. MODEL DERECELENDİRMESİ VE TOKEN TASARRUF STRATEJİSİ

### Model Görev Bölümü:
- **Claude 3.5 Haiku:** Mekanik işler, MCP araç çağrıları, dosya tamiri, hızlı script koşturma ve rutin kodlama (~100ms yanıt süresi, sıfıra yakın token maliyeti).
- **Claude 3.5 / 3.7 Sonnet & Opus:** Ağır UI/UX tasarım mühendisliği, Awwwards bileşenleri, karmaşık mimari refaktör ve stratejik kararlar.

### NotebookLM MCP İle %95 Girdi Token Tasarrufu:
- Devasa PDF, kütüphane dokümanı veya mimari rehberleri promta yapıştırıp her turda binlerce token yakmak YASAKTIR.
- Dokümanlar Google NotebookLM'e yüklenir; Claude Code `notebooklm` MCP'si ile sadece ihtiyaç duyulan ilgili paragrafı sorgular.
- **Antigravity + NotebookLM Otonom RAG Pipeline:** Arka planda çalışan Antigravity motoru canlı mimari dokümanları, log özetlerini ve güncellemeleri otomatik olarak NotebookLM'e yükler. Claude Code yerel ortamda her işte `notebooklm` MCP'si ile en güncel haritayı sıfır token maliyetiyle sorgular.
- **Google Hesabı Yetkilendirme Kuralı (Kritik Pitfall):** NotebookLM MCP tarayıcı çerezleri veya `notebooklm-mcp-cli auth` ile yetkili hesabı (ör. `ergenebilal@gmail.com`) kullanır. `notebooklm.google.com` üzerindeki not defteri tam olarak yetkilendirilen bu hesaptakiler ile eşleşmelidir; farklı hesapta açılan not defterleri MCP tarafından görünmez (`Notebook Not Found`).
- **VPS SSH Key & Dağıtım Mimarisi:** Claude Code yerel bilgisayarda (`C:\Users\lenovo\cybergene-web`) çalışırken VPS SSH anahtarına ihtiyaç duymaz. Dağıtım `.\deploy.ps1` betiği üzerinden yerel SSH anahtarıyla yürütülür. VPS tarafında ise Hermes (`Hi ergenebilal!`) `git@github.com:ergenebilal/cybergene-web.git` reposuna doğrudan git push yetkisine sahiptir.

### ⚠️ `CLAUDE.md` Bağlam Şişmesi (Context Bloat) Pitfall:
- Devasa sistem brifinglerini veya 6.000+ karakterlik dokümanları bütünüyle `CLAUDE.md` dosyasına yapıştırmak, her mesaj turunda o bağlamın baştan okunmasına ve durmadan token yakılmasına sebep olur.
- **Doğru Yöntem (Mikro-CLAUDE.md):** Tam brifing Google NotebookLM'e yüklenir; `CLAUDE.md` dosyasına ise yalnızca 3 satırlık mikro-yönlendirme yazılır (*"Proje: X. Altyapı ve mimari detayları için `notebooklm` MCP'yi sorgula"*). Böylece system prompt 50 jetonla kalır.
