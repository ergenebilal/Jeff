# Dogrulama Tarifleri

Bilgisayar sistem/kod iddialarini varsayimsiz dogrularken ise yarayan somut tarifler.

## Davranis Testini Paket Icine Gomme

Paket moduleleri relative import kullandigi icin (`from .state import ...`) dogrulama
betigini **paketin icinden** calistirmak sart:

```python
import subprocess, textwrap

test = textwrap.dedent('''
import tempfile
from pathlib import Path
from jeff_cognitive import CognitiveStore, CognitiveLoop   # bu paket icinden

with tempfile.TemporaryDirectory() as tmp:
    store = CognitiveStore(Path(tmp)/"c.db")
    s = store.create("test", session_id="z")
    loop = CognitiveLoop(store)
    final = loop.run(s.goal_id, max_steps=20)
    print("fazlar:", [t["to_phase"] for t in store.transitions(s.goal_id)][:12])
''')  # relative-import hatalari: ayri betik dosyasi degil, cwd + -c cozer

r = subprocess.run(['python3','-c',test], capture_output=True, text=True,
                   cwd='/home/hermes/<paket>', timeout=40)  # cwd SART
print(r.stdout)
if r.stderr: print("STDERR:", r.stderr[-1500:])
```

- cwd'yi paket dizinine ver; aksi halde `ImportError: attempted relative import with
  no known parent package`.
- `sys.path` ekleyip import etmek yeterli DEGIL — paketi apayri bir modul gibi
  yuklemek icin cwd esas.
- `timeout` ver — sonsuz dongu olasiligina karsi (default 40s).

## Test Kalite Siniflandirma Isaretleri (kodda greple)

Her test dosyasini hangi kategori oldugunu anlamak icin icerik ayrac fine: `mock` /
`monkeypatch` / `MagicMock` / `browser` / `network` / `http` / `sqlite` / `CognitiveStore`.

- Unit: `def test_` puredir, dis kaynak yok (state/calibration/replan routing cost).
- Integration: 2+ modulu temp-SQLite'te birlestirir (loop+store, goals+experiments).
- Behavioral: davranis iddiasi (replan no-sunk-cost, routing governance) — unit
  parametresiz, ama 'karar degisimi' kiyaslar.
- **Mocked:** adinda 'mock' gecen e2e — `test_integration`/`test_end_to_end_mock` =
  temp-db + in-memory, gercek dis dunya yok. MOCK adi kirmizi bayrak.
- **REAL:** gercek LLM/API/network/canli-DB cagrisi — bunu ayrica say; cogu pakette 0.

Kisit o mesaj: "75/75 1.17s" hizlica gecmesi = _pure/dataclass agirlikli_ oldugunu
ele verir (1.17s'lik gercek e2e olamaz). Bu 'davranis kanitlanmadi' demektir, rapora acik yaz.

## Runtime Entegrasyon Kontrol Komutlari

```bash
# canli servislerden paket import ediliyor mu? (0 sonuc = entegre degil)
grep -rl "<paket_adı>\|CognitiveCore" /opt/hermes/jeff_v2/ /home/hermes/hermes_ops/ \
    /home/hermes/.hermes/hermes-agent/run_agent.py 2>/dev/null | grep -v "<paket_adı>"

# dedicated servis var mi
systemctl list-units --type=service | grep -iE "cognit|loop|executive|board"

# canli DB'de paketin tablolari var mi
sqlite3 /home/hermes/.hermes/state.db ".tables" | grep -iE "cognit|decision|lesson"
```

Kod bir yed ek dosyadan caliyorsa (ornek `backups/pre-surgery-checkpoint-.../`)
canli-disk degiskeninin KOKENINI rapora yaz — "calisiyor" ile "yedekten calisiyor"
farklidir.

## Learning→Behavior Kaniti

- 'lesson kaydedildi' = sadece yazim. Okuyan/kullanan VARligini ayri dogrula:
  `grep -i lesson <loop>.py <ade>.py` — her ikisinde de yoksa baglanti yoktur.
- Kanit: ayni karar oncesioncesi/sonrasi AYNI girdiyle calistir, cikti DEGISTI mi?
  Cikti ayniysa 'ogrendigi dersi kullaniyor' iddiasi dugdu.
