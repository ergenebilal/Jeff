# Cognitive Governance Layer — Harita, Mod Semantiği, Doğrulama

`conversation_loop` → cognitive hook → ADE + Board → enforcement zincirinin
operasyonel haritası. "Bu karar nereden geldi / neden bloklandım / düzeltme canlı mı"
sorularının cevabı burada.

## Dosya haritası

| Bileşen | Canlı yol | Not |
|---|---|---|
| Hook (tek giriş) | `/home/hermes/jeff_cognitive/hook.py` | `cognitive_hook()`, `_evaluate_strategic()`, `log_action_enforcement()` |
| Bridge (adapter) | `/home/hermes/jeff_cognitive/runtime_bridge.py` | ADE/Board/Worker'a sadece çağrı + format dönüşümü |
| ADE | `/opt/hermes/jeff_v2/adversarial_engine.py` | `AdversarialDecisionEngine`; LLM çağrısı başına `timeout=60` |
| Board | `/opt/hermes/jeff_v2/board_deliberation.py` | **Kural-bazlı, LLM'siz** — timeout kavramı yok |
| Enforcement | `/home/hermes/.local/lib/python3.11/site-packages/run_agent.py` | `_cognitive_governance_suppress()`; `_execute_tool_calls` içinde çağrılır |
| Turn entegrasyonu | `.../site-packages/agent/conversation_loop.py` | `_cognitive_turn_note` set/reset |
| Karar kayıtları | `~/.hermes/decisions/dec_*.json` | ADE kaydı + gömülü hooks |
| Tur logu | `~/.hermes/cognitive_hook_decisions.log` | her tur tek JSON satır + `event=action_enforcement` satırları |
| Kalibrasyon/state | `~/.hermes/cognitive.db` | `cognitive_state`, `cognitive_states`, `cognitive_transitions` |

`jeff_cognitive` **iki kopya** olabilir; canlı olanı import resolution + canlı log
format dizesi eşleşmesiyle doğrula (SKILL.md §8).

## Mod semantiği

`COGNITIVE_HOOK_MODE` (env, varsayılan `fast`):
- **`fast` / dry-run** → değerlendirme **gözlemsel**. ADE `dry_run=True` (boş gövde),
  Board yine kural-bazlı oynar. Bu modda sonuç **enforcement tetiklememeli**:
  `verdict=DRY_RUN`, `action=observe`, `blocked=False`. Karar yine kaydedilir
  (denetim izi korunur), sadece infaz edilmez.
- **`full`** → gerçek LLM muhakemesi; `BLOCK` üretilebilir ve enforcement çalışır.

**Tasarım kuralı:** enforcement yetkisi yalnızca **gerçek muhakemeye** aittir.
Placeholder/stub verdict (boş `thesis`/`anti_thesis`, `confidence 0`) veya kanıtsız
girdiyle koşan kural motoru governance BLOCK üretemez. `dry_run` sonucunu sahte
`CLEAR`'a çevirme — CLEAR gerçek bir izin kararıdır; ayrı bir `DRY_RUN` durumu kullan.

## Verdict → aksiyon eşlemeleri

ADE: `SCALE→continue_governed`, `TEST→experiment`, `ITERATE→pivot`, `HOLD→wait`,
`KILL→block`, `RESEARCH→research`, `NORMAL→continue`.
Board: `ACCEPT→continue`, `MODIFY→continue_flagged`, `VALIDATE_FIRST→experiment`,
`DEFER→wait`, `REJECT→block`.

BLOCK koşulu: iki taraftan **herhangi biri** `block` üretirse. Board `REJECT` tek
başına yeter — ADE `HOLD` blok değildir.

## Board neden hep REJECT diyor

Board skorlama: `support_score` vs `oppose_score` (confidence × kanıt ağırlığı)
- `total == 0` → `DEFER` ("yeterli kanıt yok")
- `support > oppose*1.5` → `ACCEPT`
- `oppose > support*1.5` → **`REJECT`**
- yüksek anlaşmazlık → `VALIDATE_FIRST`, aksi → `MODIFY`

`fact_pack` sadece `{"message": ...}` iken kanıt yok → oppose tarafı kazanır →
deterministik REJECT. Bu bir bug değil, kanıtsız girdinin defansif varsayılanı;
çözümü çağrı katmanında (enforcement yetkisi) ya da `fact_pack` zenginleştirmesindedir.

## Karar kaydı şeması (`dec_*.json`)

`decision_id, timestamp, question, trigger, context, thesis, anti_thesis, debate_body,
judge_scores, verdict, confidence, debate_level, num_llm_calls, next_experiment,
real_world_result, raw_outputs`.

**Stub tespiti:** `dry_run` kaydında `thesis {}`, `anti_thesis {}`, `judge_scores` tümü
`null`, `confidence 0` → gerçek muhakeme yok. Bu şekildeki kaydın verdict'i
enforcement için yetkili sayılmamalı.

## Doğrulama komutları

```bash
# Tur başına karar + enforcement olayları
python3 - <<'PY'
import json,collections
rows=[json.loads(l) for l in open('/home/hermes/.hermes/cognitive_hook_decisions.log') if l.strip()]
dec=[r for r in rows if 'action' in r and r.get('event')!='action_enforcement']
enf=[r for r in rows if r.get('event')=='action_enforcement']
print('karar',len(dec),'enforcement',len(enf))
print(collections.Counter(d.get('verdict') for d in dec))
print('BLOCK->enforcement eslesmesi:', [( (d.get('cognitive_result') or {}).get('hooks',{}).get('decision_id'),
      any(e.get('decision_id')==(d.get('cognitive_result') or {}).get('hooks',{}).get('decision_id') for e in enf))
      for d in dec if d.get('action')=='blocked'])
PY

# Canlı hook dosyası + ADIM 12 semantiği yerinde mi
grep -n "DRY_RUN\|dry = _env_mode" /home/hermes/jeff_cognitive/hook.py

# Enforcement katmanı dokunulmamış mı (md5 kaydet)
md5sum /home/hermes/.local/lib/python3.11/site-packages/run_agent.py \
        /home/hermes/.local/lib/python3.11/site-packages/agent/conversation_loop.py
```

## Cerrahi değişiklik protokolü

1. **Yedek:** `cp -p hook.py hook.py.bak-<adim>-$(date +%Y%m%d-%H%M%S)` + tek adım rollback
   komutunu rapora yaz.
2. Değişikliği **tek fonksiyona** sıkıştır; yeni sınıf/state machine/framework ekleme.
3. Enforcement katmanına **dokunma** — geçersiz sinyali **çağrı katmanında** filtrele
   (yukarıda kes), infaz mantığını gevşetme.
4. **İzole test:** `HERMES_HOME=$(mktemp -d)` ile koş; gerçek `~/.hermes/decisions/`
   dizinine yazma. Testten sonra prod dizininin mtime'ı değişmediğini doğrula.
5. **Eski davranışı doğrulayan testler bilerek kırılır** — onları yeni semantiğe taşı,
   silme. Kırılmayı "regresyon" sanma; hangi testin hangi eski kuralı kodladığını söyle.
6. **Fake bridge ile dal testi:** her zaman BLOCK dönen sahte bridge enjekte et →
   dry modda `blocked=False`, `full` modda `blocked=True` beklenir. Böylece gerçek LLM
   çağırmadan her iki dal da kanıtlanır.
7. **Production kanıtı restart ister** (sys.modules cache) — restart ayrı kanaldan;
   test sonucunu production kanıtı sayma, ikisini ayrı satırda raporla.
