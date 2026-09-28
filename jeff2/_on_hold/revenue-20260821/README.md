# Jeff 5.0 Revenue Engine — Venture Registry

> Master kayıt: `revenue/venture_registry.json`
> Deney şablonu ve karar kriterleri: aşağıda
> Tüzük: skill `jeff-5.0-revenue-engine`

## Venture Kaydı (v1.1 şeması)
`venture_id · name · category · problem · target_market · hypothesis · status · capital_allocated · capital_spent · revenue · profit · roi · customers · conversion_rate · cac · ltv · mrr · experiment_count · last_experiment · next_action · risk_score · opportunity_score · created_at · updated_at`

## Deney Formatı (her deney kaydedilir)
`experiment_id · venture_id · hypothesis · problem · target_customer · solution · acquisition_channel · expected_outcome · max_budget · time_limit · success_criteria · failure_criteria · actual_result · learning · next_action · status(kill/iterate/scale/running)`

## Skorlama Kriterleri (0-100)
Demand · Competition · Pain severity · Willingness to pay · Gross margin · Automation potential · Initial capital · Distribution difficulty · Time to first revenue · Scalability · Recurring revenue · Defensibility · Op complexity · Legal/platform risk

## KILL / ITERATE / SCALE
- **KILL:** talep yok, ödeme yok, CAC sürdürülemez, risk yüksek, daha iyi fırsat var.
- **ITERATE:** sinyal var, model çalışmıyor → teklif/fiyat/hedef/kanal/VP değiştir, yeniden test.
- **SCALE:** gerçek ödeme + pozitif unit economics + tekrarlanabilir → kontrollü büyüt.

## İlk 72 Saat
- Phase 0 (0-24s): sistem audit ✅ (20.08), 20+ fırsat taraması (5 paralel subagent çalışıyor), ilk 5 skorlama (bekleniyor)
- Phase 1 (24-48s): en yüksek 3 fırsat derin araştırma + hipotez/MVP/bütçe
- Phase 2 (48-72s): insan onayı gerektirmeyen deneyleri başlat

## Geçmiş Not
- CRM 50 lead (46 New / 4 Contacted, 9 email), 0 email gönderimi, 0 satış — Bilal kararıyla bekletiliyor (20.08)
- Jeff 4.0 altyapısı yeniden yazılmaz; gelir yönetimine map'lenir
