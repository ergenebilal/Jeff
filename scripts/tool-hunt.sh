#!/usr/bin/env bash
set -e
cd /home/hermes/tool-hunter

# 1) OpenCode'u tool avına gönder
opencode run --agent operator . "GOREV: GitHub trending'de ve Reddit'te son 3 gundeki populer AI araclari bul.

1. GitHub API: curl -s 'https://api.github.com/search/repositories?q=ai+agent+tool&sort=stars&order=desc&per_page=5'
2. GitHub API: curl -s 'https://api.github.com/search/repositories?q=llm+framework+agent&sort=stars&order=desc&per_page=5'
3. Reddit: curl -s -A 'Mozilla/5.0' 'https://www.reddit.com/r/MachineLearning/hot.json?limit=25'
4. Reddit: curl -s -A 'Mozilla/5.0' 'https://www.reddit.com/r/programming/hot.json?limit=25'

Ciktiyi /home/hermes/tool-hunter/ham-buluntular.md'ye yaz.
SADECE 100+ yildizli veya Reddit'te 30+ upvote almis gercek araclari goster.
Her arac icin: ismi, yildiz sayisi, ne ise yaradigi (1 cumle), link.

DIKKAT: ASAGIDAKILERI KESINLIKLE LISTELEME VE ONERME:
- Headroom (veya headroom iceren herhangi bir repo) — BU SISTEMI BOZUYOR, DAHA ONCE DENENDI" 2>&1

# 2) Python ile filtrele: sadece yeni bulunan araclari raporla
python3 /home/hermes/.hermes/scripts/tool-hunt-filter.py 2>&1

echo "---"
echo "Tool hunt completed at $(date)"
