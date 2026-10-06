"""Bounded handoff changes; ranking, scoring and business workflows stay intact."""
import hashlib
import re


def replace_once(source,old,new):
    if source.count(old)!=1:raise ValueError('Opportunity handoff anchor changed')
    return source.replace(old,new)


def patch_front(source):
    if 'let jeffOpportunityId = null;' in source:return source
    source=replace_once(source,'let askSeq = 0;', 'let jeffOpportunityId = null;\nlet askSeq = 0;')
    source=replace_once(source,'  text = text.trim(); if (!text) return;',
        '  text = text.trim(); if (!text) return;\n  if (opts.opportunityId !== undefined) jeffOpportunityId = opts.opportunityId;')
    source=replace_once(source,"if (!opts.fromVoice) msg('u', esc(text));","if (!opts.fromVoice) msg('u', esc(opts.displayText || text));")
    source=replace_once(source,'body: JSON.stringify({text}), signal: ac.signal',
        'body: JSON.stringify({text, ...(jeffOpportunityId ? {opportunity_id: jeffOpportunityId} : {})}), signal: ac.signal')
    source=replace_once(source,"  abortListening(); stopAudio(); askSeq++; lastReply = '';",
        "  abortListening(); stopAudio(); askSeq++; lastReply = ''; jeffOpportunityId = null;")
    old="  if (b.dataset.oa === 'talk') { go('komuta'); return ask(`\"${o.title}\" fırsatını konuşalım. Önerilen hamle: ${o.move || 'yok'}. Sence nasıl ilerleyelim?`); }"
    new="  if (b.dataset.oa === 'talk') { go('komuta'); return ask('Seçtiğim fırsatı konuşalım. Kartında neden fırsat gördüğünü, beklenen faydayı ve ilk küçük adımı açıkla. Önceki değerlendirmeni değiştirdiysen nedenini de söyle.', {opportunityId: o.id, displayText: `\"${o.title}\" fırsatını konuşalım.`}); }"
    source=replace_once(source,old,new)
    source=replace_once(source,'  voice:()=>voiceName,worklet:', '  opportunity:()=>jeffOpportunityId,\n  voice:()=>voiceName,worklet:')
    return source


def patch_html(source,app_bytes,live_bytes):
    for name,data in [('app.js',app_bytes),('live-call.js',live_bytes)]:
        pattern=r'<script src="'+re.escape(name)+r'(?:\?v=[a-f0-9]+)?"></script>'
        if len(re.findall(pattern,source))!=1:raise ValueError('Panel asset anchor changed')
        source=re.sub(pattern,'<script src="'+name+'?v='+hashlib.sha256(data).hexdigest()[:16]+'"></script>',source)
    return source
