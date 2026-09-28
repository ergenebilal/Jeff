# Claude Code MCP & Awwwards Skill Entegrasyon Rehberi

## Ne Zaman Kullanılır
- Claude Code ile Awwwards seviyesinde, lüks ve yüksek performanslı web projeleri geliştirirken.
- Yerel makinada (Windows / VS Code terminali) Claude Code MCP sunucularını ve tasarım skill'lerini aktif ederken.
- Token maliyetlerini %99 düşürmek için NotebookLM MCP mimarisini kurarken.

## 🎨 4 Kritik Awwwards Claude Skill'i
1. **`frontend-design`** (`https://github.com/anthropics/skills`): Generic yapay zeka şablon görünümünü engeller; editoryal tipografi, temiz alanlar ve kurumsal tasarım dili getirir.
2. **`taste-skill`** (`https://github.com/Leonxlnx/taste-skill`): Projenin hareket, deneysellik ve kurumsallık dengesini ayarlar; tasarım çizgisini korur.
3. **`scroll-craft`** (`https://github.com/nateherkai/scroll-craft`): Sayfa kaydırıldıkça (scroll) tetiklenen GSAP ve Framer Motion animasyonlarını yönetir.
4. **`design-dna`** (`https://github.com/zanwei/design-dna`): İlham alınan bir sitenin görsel veya videosundan tipografi, boşluk ve tasarım genomunu çıkararak özgün kod üretir.

## 📦 5 Temel MCP Sunucusu
- **`context7`** (`npx -y context7-mcp`): Güncel kütüphane dokümantasyonu (Astro, Tailwind vb.) sunarak eski kod kullanımını engeller.
- **`playwright`** (`npx -y @modelcontextprotocol/server-playwright`): Yerel Chrome ile canlı site taraması ve görsel regression testi yapar.
- **`notebooklm-mcp`** (`npx -y notebooklm-mcp`): Ağır dokümanları Google NotebookLM'e koyup ihtiyaç anında sorgulayarak promtta token yakmayı engeller (%99 tasarruf).
- **`sequential-thinking`** (`npx -y @modelcontextprotocol/server-sequential-thinking`): Adli ve adım adım derin muhakeme yaptırır.
- **`figma`** (`npx -y @figma/mcp-server`): Figma tasarımlarını doğrudan koda çevirir.

## ⚡ 1-Tık Windows PowerShell Otomatik Kurulum Komutu
```powershell
Invoke-WebRequest -Uri "https://cybergene.co/claude_code_pack.zip" -OutFile "$env:TEMP\claude_pack.zip"; Expand-Archive -Path "$env:TEMP\claude_pack.zip" -DestinationPath "$env:TEMP\claude_pack" -Force; Set-Location "$env:TEMP\claude_pack\claude_code_pack"; .\install_claude_pack.ps1
```
