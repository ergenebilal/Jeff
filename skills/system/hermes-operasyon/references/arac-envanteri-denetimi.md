# Araç / Yetenek Envanteri Denetimi ("elimizde ne var, güncel mi?")

Tetikleyici: kullanıcı "yeteneklerini/MCP'leri/araçlarını analiz et", "daha iyisi var mı",
"güncellenmesi gereken ne var" tipi bir istek yapar. Amaç: kurulu olanı **iddia etmeden** saymak
ve her satır için güncellik hükmünü kanıtla vermek.

## 1. Envanteri say (hepsi tek koşuda alınabilir)

```bash
hermes mcp list                      # MCP sunucuları + enabled durumu
hermes plugins list                  # plugin'ler (enabled/not enabled)
hermes cron list                     # zamanlanmış işler + last run + execution
hermes cron doctor                   # düşen job'lar ve sebepleri
python3 -c "import yaml;d=yaml.safe_load(open('/home/hermes/.hermes/config.yaml'));print(list(d.get('mcp_servers',{})))"
find ~/.hermes/skills -mindepth 2 -name SKILL.md -not -path "*.archive*" | wc -l
find ~/.hermes/hermes-agent/skills -name SKILL.md | wc -l          # builtin
find ~/.hermes/hermes-agent/optional-skills -name SKILL.md | wc -l # kapalı, kurulabilir
```

**Sayı uyuşmazlığı tuzağı:** `find ~/.hermes/skills -name SKILL.md | wc -l` arşivdekileri de sayar
(ör. 183) — "aktif yetenek" sayısı **arşiv hariç** olandır (ör. 22). Rapor ederken hangisini saydığını belirt.

## 2. Kurulu sürümü ölç, sonra upstream ile karşılaştır

| Tür | Kurulu sürüm | Upstream karşılaştırma |
|---|---|---|
| npx ile koşan MCP | `~/.npm/_npx/<hash>/node_modules/<paket>/package.json` → `version` | `npm view <paket> version` |
| Global npm aracı | `which -a <araç>` + `<araç> --version` | `npm view <paket> version` |
| Binary (gh, uv…) | `which -a`, `--version` | `curl -s https://api.github.com/repos/<owner>/<repo>/releases/latest` → `tag_name` |
| Yerel git kurulumu | `git log -1 --oneline`, `git status -sb` (behind sayısı) | `git fetch --tags` + `git log HEAD..origin/main --oneline | wc -l` |
| Çekirdek (hermes) | `hermes --version` ("N commits behind" satırı) | `git tag | sort -V | tail -3` |

`npm view` boş dönerse paket adı yanlış olabilir (ör. docker MCP'si `@supernova123/docker-mcp-server`,
kısaltması değil). Bir MCP'nin gerçek paket adını config'teki `args` alanından oku.

## 3. "Yeni ve daha iyisi var mı" taraması — filtre olmadan liste üretme

Her aday için **üç** şeyi kanıtla, yoksa listeye alma:

1. **Aktiflik:** `curl -sL https://api.github.com/repos/<owner>/<repo>` → `stargazers_count` + `pushed_at`.
   Son commit **6 aydan eski** ise bakımsız/ölü kabul edilir (gözlem: bir RAG MCP'si 415 gündür sessiz).
2. **Yeterli olgunluk:** yıldız sayısı (kaba eşik ≥500) — ama yıldız tek başına gerekçe değildir.
3. **Bu iş akışına somut katkı:** "X'i şu işte şöyle kullanırız" cümlesi yazılamıyorsa aday listeden çıkar.

Ek kurallar:
- **Zaten kapsananı listeleme:** bu stack'te web okuma, tarayıcı otomasyonu, hafıza, docker, takvim/mail
  köprüleri VAR. Aynı işi yapan "yeni" araç ancak ölçülmüş bir eksik varsa gerekçelenir.
- **Repo yeniden adlandırılmış olabilir:** API `Moved Permanently` dönerse `curl -sL` ile takip et;
  yoksa yıldız/tarih alanları boş okunur ve "ölü proje" sanılır.
- Kullanıcının "gereksiz yük kurulmaz" kuralı geçerli: bu denetim **kurulum kararı değildir**, karar için
  kanıt üretir. "Fikir kütüphanesi" ile "şimdi kurulacaklar"ı ayrı yaz; kurulumu onaya sun.

## 4. Rapor şekli

- Önce tek tablo: bileşen · kurulu · güncel · hüküm (🔴 güncelle / 🟡 iyileştir / ✅ dokunma).
- Sonra "ne yapılacak" listesi: her madde **komutuyla** birlikte, en düşük riskli önce.
- Çekirdek (`hermes update`) kalemi ayrı başlık olsun: kirli ağaç + yedek kontrolü olmadan asla
  "şimdi güncelle" diye sunma (bkz. SKILL.md §11).
